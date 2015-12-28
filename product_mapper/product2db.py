# ex: set ts=4 et:

'''
Scan DynamoDB, process links, product map, output to Postgresql
'''

import sys
sys.path.append('..')

import binascii
import boto3
import botocore
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime
import gc
import multiprocessing
import psycopg2
import psycopg2.extensions
import time
import traceback
from yurl import URL

from product import ProductMapResult, ProductMapResultPage
from spider_backend import s3wrap
from dbconn import get_psql_conn

from barneys import ProductsBarneys
from bathandbodyworks import ProductsBathandBodyWorks
from beautycom import ProductsBeautyCom
from beautybar import ProductsBeautybar
from bergdorfgoodman import ProductsBergdorfGoodman
from bloomingdales import ProductsBloomingdales
from bluefly import ProductsBluefly
from dermstore import ProductsDermstore
from drugstorecom import ProductsDrugstoreCom
from farfetch import ProductsFarfetch
from fwrd import ProductsFwrd
from lordandtaylor import ProductsLordandTaylor
from macys import ProductsMacys
from matchesfashion import ProductsMatchesFashion
from maybelline import ProductsMaybelline
from modaoperandi import ProductsModaoperandi
from mytheresa import ProductsMyTheresa
from neimanmarcus import ProductsNeimanMarcus
from netaporter import ProductsNetaPorter
from nordstrom import ProductsNordstrom
from theoutnet import ProductsTheOutNet
from revolveclothing import ProductsRevolveClothing
from saks import ProductsSaks
from sephora import ProductsSephora
from shopbop import ProductsShopbop
from ssense import ProductsSsense
from stylebop import ProductsStylebop
from tradesy import ProductsTradesy
from ulta import ProductsUlta
from walgreens import ProductsWalgreens
from violetgrey import ProductsVioletgrey
from yoox import ProductsYoox
from zappos import ProductsZappos

'''

pseudocode:

connect to dynamodb for metadata input
connect to s3 for content input
connect to postgresql for product output

while reading metadata
    filter stuff we want
    read content
    send to product mapper
    for each product
        write to postgresql

'''


def each_link(url_host=None, since_ts=0):
    # ref: http://boto3.readthedocs.org/en/latest/reference/customizations/dynamodb.html#ref-dynamodb-conditions

    print 'each_link url_host=%s since_ts=%s' % (
        url_host, datetime.fromtimestamp(since_ts))

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('link')

    kce = Key('host').eq(url_host) & Key('updated').gte(since_ts)
    fe = Attr('body').ne(None)
    #fe = Attr('body').ne(None) # FIXME: temporary for ssense, which was fucking up...
    pe = '#u,updated,host,body' # TODO: updated as well...
    ean = {'#u': 'url',}
    limit = 50

    # TODO: refactor very similiar branches

    if url_host is None:
        # no url_host specified, scan the whole table...
        resp = table.scan(
            FilterExpression=fe,
            ProjectionExpression=pe,
            ExpressionAttributeNames=ean,
            Select='SPECIFIC_ATTRIBUTES'
        )
        for item in resp['Items']:
            yield item
        while 'LastEvaluatedKey' in resp:
            resp = table.scan(
                ExclusiveStartKey=resp['LastEvaluatedKey'],
                ProjectionExpression=pe,
                ExpressionAttributeNames=ean,
                Select='SPECIFIC_ATTRIBUTES'
            )
            for item in resp['Items']:
                yield item
    elif url_host is not None:
        # query for a specific url_host

        resp = None
        # botocore.exceptions.ClientError: An error occurred (ProvisionedThroughputExceededException)
        while resp is None:
            try:
                resp = table.query(
                    IndexName='host-index3',
                    KeyConditionExpression=kce,
                    FilterExpression=fe,
                    ProjectionExpression=pe,
                    ExpressionAttributeNames=ean,
                    Select='SPECIFIC_ATTRIBUTES',
                    Limit=limit
                )
            except botocore.exceptions.ClientError as e:
                print e
                time.sleep(10)
        for item in resp['Items']:
            yield item

        while 'LastEvaluatedKey' in resp:
            retry_sleep = 1
            r = None
            while r is None:
                try:
                    r = table.query(
                        ExclusiveStartKey=resp['LastEvaluatedKey'],
                        IndexName='host-index3',
                        KeyConditionExpression=kce,
                        FilterExpression=fe,
                        ProjectionExpression=pe,
                        ExpressionAttributeNames=ean,
                        Select='SPECIFIC_ATTRIBUTES',
                        Limit=limit
                    )
                    resp = r
                except botocore.exceptions.ClientError as e:
                    print e
                    time.sleep(10)
                except Exception as e:
                    # e.g. OpenSSL.SSL.SysCallError
                    print e
                    time.sleep(retry_sleep)
                    if retry_sleep < 60:
                        retry_sleep *= 2 # exponential backoff
                for item in resp['Items']:
                    yield item

def decompress_body(body):
    import gzip
    import StringIO
    stringio = StringIO.StringIO(body)
    with gzip.GzipFile(fileobj=stringio, mode='rb') as gzip_file:
        f = gzip_file.read()
    stringio.close()
    return f

Host2Map = {
    'shop.nordstrom.com':   ProductsNordstrom,
    'www.barneys.com':      ProductsBarneys,
    'www.beauty.com':       ProductsBeautyCom,
    'www.beautybar.com':       ProductsBeautybar,
    'www.bathandbodyworks.com': ProductsBathandBodyWorks,
    'www.bergdorfgoodman.com': ProductsBergdorfGoodman,
    'www1.bloomingdales.com':ProductsBloomingdales,
    'www.bluefly.com':      ProductsBluefly,
    'www.dermstore.com':    ProductsDermstore,
    'www.drugstore.com':    ProductsDrugstoreCom,
    'www.farfetch.com':     ProductsFarfetch,
    'www.fwrd.com':         ProductsFwrd,
    'www.lordandtaylor.com': ProductsLordandTaylor,
    'www1.macys.com':       ProductsMacys,
    'www.matchesfashion.com': ProductsMatchesFashion,
    'www.maybelline.com':   ProductsMaybelline,
    'www.modaoperandi.com': ProductsModaoperandi,
    'www.mytheresa.com':    ProductsMyTheresa,
    'www.neimanmarcus.com': ProductsNeimanMarcus,
    'www.net-a-porter.com': ProductsNetaPorter,
    'www.revolveclothing.com': ProductsRevolveClothing,
    'www.saksfifthavenue.com': ProductsSaks,
    'www.sephora.com':      ProductsSephora,
    'www.shopbop.com':      ProductsShopbop,
    'www.ssense.com':       ProductsSsense,
    'www.stylebop.com':     ProductsStylebop,
    'www.theoutnet.com':    ProductsTheOutNet,
    'www.tradesy.com':      ProductsTradesy,
    'www.ulta.com':         ProductsUlta,
    'www.violetgrey.com':   ProductsVioletgrey,
    'www.walgreens.com':    ProductsWalgreens,
    'www.yoox.com':         ProductsYoox,
    'www.zappos.com':       ProductsZappos,
}

'''
given a url and associated data...
read the HTML body from S3
read zero or more products from the HTML using a host-specific mapper
return the results
'''
def handle_url(url, host, sha256, updated):
    try:
        body = s3wrap.get_body_by_hash('productsum-spider',
                                       binascii.hexlify(sha256))
        if body:
            return Host2Map[host].from_html(url,
                                            unicode(decompress_body(body.read()), 'utf8'),
                                            updated=updated)
    except:
        traceback.print_exc()
        raise

'''
per-CPU(ish) worker that
    reads input
    does expensive-ish work
    writes output to second queue
NOTE: doesn't peg a CPU due to S3 i/o
'''
def worker(q1, q2):
    while True:
        params = q1.get(True)
        q2.put(handle_url(*params))
        #gc.collect()

'''
read completed work from the queue
and serialize it to postgres
'''
def handle_responses(q2, min_handle=0):

    def _get_nowait(q):
        try:
            return q.get_nowait()
        except: # argh Queue is stupid with its Empty exception...
            return None

    starttime = time.time()
    recv = 0
    #print 'min_handle:', min_handle
    try:
        results = _get_nowait(q2)
        while results is not None or (recv < min_handle):
            if results is not None:
                recv += 1
                try:
                    assert isinstance(results, ProductMapResult)
                    results.save()
                except:
                    traceback.print_exc()
            elif results is None:
                if recv == 0 and time.time() - starttime > 30:
                    # try to avoid hanging forever, which seems to happen...
                    break
                if recv < min_handle:
                    time.sleep(0.1) # avoid too-hot a loop
            results = _get_nowait(q2)
    except KeyboardInterrupt:
        pass
    except:
        traceback.print_exc()
    return recv


def map_products(url_host):

    starttime = time.time()

    def show_progress(sent, recv):
        now = time.time()
        elapsed = now - starttime
        recvrate = recv / max(1.0, elapsed)
        print 'progress: %.1f sec, %d sent, %d recv (%.1f/sec)' % (
            elapsed, sent, recv, recvrate)

    man = multiprocessing.Manager()
    q1 = man.Queue()
    q2 = man.Queue()

    # our worker processes don't peg the CPU due to i/o
    # so if we directly map 1:1 w/ CPU we waste a lot of resources
    POOLSIZE = multiprocessing.cpu_count() * 2
    pool = multiprocessing.Pool(POOLSIZE, worker, (q1, q2,))

    sent = 0
    recv = 0
    skip = 0

    # parsing the HTML is dreadfully slow old sport
    # so we had to pool our CPUs don't you know

    # calculate the earliest timestamp we should accept
    since_ts = 0
    conn = get_psql_conn()
    if url_host:
        since_ts = ProductMapResultPage.first_any_updated(conn, url_host) or 0

    '''
    scan all links in dynamodb
    if a link has a body, and we have a ProductMapper for that host
        enqueue it for the worker processes
        also, process their output
    '''
    try:
        for link in each_link(url_host=url_host, since_ts=since_ts):
            sha256 = link['body']
            host = link['host']
            url = link['url']
            updated = link['updated']
            last_updated = ProductMapResultPage.last_updated(conn, host, url) or 0
            if sha256 and host in Host2Map and updated > last_updated:
                # has data, we have a mapper for the host, and updated since last seen...
                sha256 = bytearray(sha256.value) # extract raw binary
                sent += 1
                print sent, url.encode('utf8')
                if sent < skip:
                    recv += 1 # fake it
                else:
                    q1.put((url, host, sha256, updated))
                    if q1.qsize() >= POOLSIZE * 2:
                        # input queue full enough, process output.
                        # throttles input rate
                        recv += handle_responses(q2, min_handle=1)
                if sent % 1000 == 0:
                    show_progress(sent, recv)
        print 'finishing up final %s...' % (sent - recv)
        handle_responses(q2, 0)
    except KeyboardInterrupt:
        try:
            pool.terminate()
        except:
            pass

    show_progress(sent, recv)

if __name__ == '__main__':

    url_hosts = sys.argv[1:]
    if url_hosts:
        while url_hosts:
            url_host = url_hosts.pop(0)
            print 'url_host:', url_host
            if url_host not in Host2Map:
                print 'url host not in ', sorted(Host2Map.keys())
                sys.exit(1)
            map_products(url_host)
    else:
        map_products(None) # all

    print 'done'
