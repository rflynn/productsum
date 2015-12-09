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
import gc
import multiprocessing
import psycopg2
import psycopg2.extensions
import sys
import time
import traceback
from yurl import URL

from product import ProductMapResult
from spider_backend import s3wrap

from barneys import ProductsBarneys
from bergdorfgoodman import ProductsBergdorfGoodman
from bluefly import ProductsBluefly
from dermstore import ProductsDermstore
from farfetch import ProductsFarfetch
from fwrd import ProductsFwrd
from lordandtaylor import ProductsLordandTaylor
from macys import ProductsMacys
from neimanmarcus import ProductsNeimanMarcus
from netaporter import ProductsNetaPorter
from nordstrom import ProductsNordstrom
from revolveclothing import ProductsRevolveClothing
from saks import ProductsSaks
from shopbop import ProductsShopbop
from yoox import ProductsYoox

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


def each_link(url_host=None):
    # ref: http://boto3.readthedocs.org/en/latest/reference/customizations/dynamodb.html#ref-dynamodb-conditions

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('link')

    fe = Attr('body').ne(None) # TODO: does this work?
    pe = '#u,host,body' # TODO: updated as well...
    ean = {'#u': 'url',}

    # TODO: refactor very similiar branches

    if url_host is None:
        # no url_host specified, scan the whole table...
        resp = table.scan(
            FilterExpression=fe,
            ProjectionExpression=pe,
            ExpressionAttributeNames=ean
        )
        for item in resp['Items']:
            yield item
        while 'LastEvaluatedKey' in resp:
            resp = table.scan(
                ExclusiveStartKey=resp['LastEvaluatedKey'],
                ProjectionExpression=pe,
                ExpressionAttributeNames=ean
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
                    IndexName='host-index',
                    KeyConditionExpression=Key('host').eq(url_host),
                    FilterExpression=fe,
                    ProjectionExpression=pe,
                    ExpressionAttributeNames=ean
                )
            except botocore.exceptions.ClientError as e:
                print e
                time.sleep(10)
        for item in resp['Items']:
            yield item

        while 'LastEvaluatedKey' in resp:
            r = None
            while r is None:
                try:
                    r = table.query(
                        ExclusiveStartKey=resp['LastEvaluatedKey'],
                        IndexName='host-index',
                        KeyConditionExpression=Key('host').eq(url_host),
                        FilterExpression=fe,
                        ProjectionExpression=pe,
                        ExpressionAttributeNames=ean
                    )
                    resp = r
                except botocore.exceptions.ClientError as e:
                    print e
                    time.sleep(10)
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
    'www.bergdorfgoodman.com': ProductsBergdorfGoodman,
    'www.bluefly.com':      ProductsBluefly,
    'www.dermstore.com':    ProductsDermstore,
    'www.farfetch.com':     ProductsFarfetch,
    'www.fwrd.com':         ProductsFwrd,
    'www.lordandtaylor.com': ProductsLordandTaylor,
    'www1.macys.com':       ProductsMacys,
    'www.neimanmarcus.com': ProductsNeimanMarcus,
    'www.net-a-porter.com': ProductsNetaPorter,
    'www.revolveclothing.com': ProductsRevolveClothing,
    'www.saksfifthavenue.com': ProductsSaks,
    'www.shopbop.com':      ProductsShopbop,
    'www.yoox.com':         ProductsYoox,
}

'''
given a url and associated data...
read the HTML body from S3
read zero or more products from the HTML using a host-specific mapper
return the results
'''
def handle_url(url, host, sha256):
    try:
        body = s3wrap.get_body_by_hash('productsum-spider',
                                       binascii.hexlify(sha256))
        if body:
            return Host2Map[host].from_html(url, decompress_body(body.read()))
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


starttime = time.time()

def show_progress(sent, recv):
    now = time.time()
    elapsed = now - starttime
    recvrate = recv / max(1.0, elapsed)
    print 'progress: %.1f sec, %d sent, %d recv (%.1f/sec)' % (
        elapsed, sent, recv, recvrate)


url_host = None

if len(sys.argv) > 1:
    url_host = sys.argv[1]
    print 'url_host:', url_host
    if url_host not in Host2Map:
        print 'url host not in ', sorted(Host2Map.keys())
        sys.exit(1)

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

'''
scan all links in dynamodb
if a link has a body, and we have a ProductMapper for that host
    enqueue it for the worker processes
    also, process their output
'''
try:
    for link in each_link(url_host=url_host):
        sha256 = link['body']
        host = link['host']
        if sha256 and host in Host2Map:
            sha256 = bytearray(sha256.value) # extract raw binary
            url = link['url']
            sent += 1
            print sent, url.encode('utf8')
            if sent < skip:
                recv += 1 # fake it
            else:
                q1.put((url, host, sha256))
                if q1.qsize() >= POOLSIZE * 2:
                    # input queue full enough, process output.
                    # throttles input rate
                    recv += handle_responses(q2, min_handle=1)
            if sent % 1000 == 0:
                show_progress(sent, recv)
    handle_responses(q2, sent - recv)
except KeyboardInterrupt:
    try:
        pool.terminate()
    except:
        pass

show_progress(sent, recv)

print 'done'

