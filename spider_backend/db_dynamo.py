
import boto3
import botocore
import cPickle
from datetime import datetime
import hashlib
import json
from pprint import pprint
import random
from time import sleep
from yurl import URL
import zlib


dynamodb = boto3.resource('dynamodb')
client = boto3.client('dynamodb')

def utcnow():
    return long(datetime.utcnow().strftime('%s'))

# gotta support brand pages e.g. http://www.gilt.com/brands
MAXLINKS = 10000

def link_update_results(url, httpcode, olen, clen,
                        sha256, canonical_url, mimetype, links):
    now = str(utcnow())
    if links:
        # in practice the most i've seen legitimately on e.g. a list of all brands/designers
        if len(links) > MAXLINKS:
            print 'trimming links from len %s to %s items...' % (len(links), MAXLINKS)
            links = links[:MAXLINKS]
    if links:
        print 'links is ~%s bytes stringified...' % len(json.dumps(links))
        print 'links is ~%s bytes compressed...' % len(zlib.compress(json.dumps(links)))
    else:
        print 'links is empty...'
    item = {
        'url': {'S': url},
        'created': {'N': now},
        'updated': {'N': now},
        'lastok': {'N': now} if httpcode == 200 else {'NULL': True},
        'host': {'S': URL(url).host},
        'url_canon': {'S':canonical_url},
        'code': {'N':str(httpcode)},
        'olen': {'N':str(olen)} if olen is not None else {'NULL':True},
        'clen': {'N':str(clen)} if clen is not None else {'NULL':True},
        'mime': {'S':mimetype} if mimetype else {'NULL':True},
        'body': {'B':sha256} if sha256 else {'NULL':True},
        'links': {'B':zlib.compress(json.dumps(list(links)))} if links else {'NULL':True}
    }
    #pprint(item)
    ok = False
    while not ok:
        try:
            client.put_item(TableName='link', Item=item)
            ok = True
        except Exception as e:
            print e
            sleep(5)

def get_url_updated(url):
    while True:
        try:
            resp = client.get_item(
                    TableName='link',
                    Key={'url':{'S': url}},
                    ProjectionExpression='updated'
            )
        except Exception as e:
            print e
            sleep(5)
    updated = None
    item = resp.get(u'Item')
    if item:
        updated = int(item['updated']['N'])
    return updated


def _get_url_uncached(url):
    resp = None
    # retry on ProvisionedThroughputExceededException
    while not resp:
        try:
            resp = client.get_item(TableName='link', Key={'url':{'S': url}})
        except Exception as e:
            print e
            sleep(3 + (random.random() * 7))
    item = resp.get(u'Item')
    if item:
        item['url'] = item['url']['S']
        item['created'] = int(item['created']['N'])
        item['updated'] = int(item['updated']['N'])
        item['lastok'] = int(item['lastok']['N']) if 'N' in item['lastok'] else None
        item['host'] = item['host']['S']
        item['url_canon'] = item['url_canon']['S']
        item['code'] = int(item['code']['N'])
        item['olen'] = int(item['olen']['N']) if 'N' in item['olen'] else None
        item['clen'] = int(item['clen']['N']) if 'N' in item['clen'] else None
        item['mime'] = item['mime']['S'] if 'S' in item['mime'] else None
        item['body'] = item['body']['B'] if 'B' in item['body'] else None
        item['links'] = json.loads(zlib.decompress(item['links']['B'])) if 'B' in item['links'] else []
    return item

class CachedURL(object):
    def __init__(self, item):
        self.freshness = utcnow()
        self.set_item(item)
        self.hitcnt = 0
    def hit(self):
        self.hitcnt += 1
    def set_item(self, item):
        self.item = zlib.compress(cPickle.dumps(item))
    def get_item(self):
        return cPickle.loads(zlib.decompress(self.item))
    def is_stale(self, now=None):
        now = now or utcnow()
        return now - self.freshness > 60 * 20 # 20 minutes
    @staticmethod
    def expire_stale_items(urlcache):
        # without this, unaccessed items sit in memory, wasting space
        expired = []
        now = utcnow()
        for k, v in urlcache.iteritems():
            if v.is_stale(now):
                expired.append(k)
        for k in expired:
            del urlcache[k]

_URLCache = {}

def get_url(url):
    global _URLCache
    cu = _URLCache.get(url)
    item = None
    if cu:
        if cu.is_stale():
            print 'cache hit, stale...'
            del _URLCache[url]
            # FIXME: since we don't do multi-threads, we're mixing
            # logic about the whole cache into access for a single entry
            # oh well...
            CachedURL.expire_stale_items(_URLCache)
        else:
            print 'cache hit (%d items)...' % (len(_URLCache),)
            item = cu.get_item()
    else: # not cu
        print 'cache miss...'
        item = _get_url_uncached(url)
        _URLCache[url] = CachedURL(item)
    return item

def invalidate_cache(url):
    global _URLCache
    del _URLCache[url]

def init():
    pass

def shutdown():
    pass


if __name__ == '__main__':

    url = 'http://test.example/'
    link_update_results(
        url, 200,
        100, 50, hashlib.sha256().digest(),
        'http://test.com/',
        'text/html',
        {
            url,
            url + '2/',
            url + '3/',
        })
    pprint(get_url(url))
    pprint(get_url(url+'?nope'))

