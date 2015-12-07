# ex: set ts=4 et:

'''
Scan DynamoDB, process links, product map, output to Postgresql
'''

import sys
sys.path.append('..')

import binascii
import boto3
from boto3.dynamodb.conditions import Key, Attr
import gc
import multiprocessing
import psycopg2
import psycopg2.extensions
import time
import traceback
from yurl import URL

from product import ProductMapResult
from spider_backend import s3wrap

from bergdorfgoodman import ProductsBergdorfGoodman
from bluefly import ProductsBluefly
from dermstore import ProductsDermstore
from farfetch import ProductsFarfetch
from lordandtaylor import ProductsLordandTaylor
from macys import ProductsMacys
from neimanmarcus import ProductsNeimanMarcus
from netaporter import ProductsNetaPorter
from nordstrom import ProductsNordstrom
from saks import ProductsSaks
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


def each_link():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('link')
    # ref: http://boto3.readthedocs.org/en/latest/reference/customizations/dynamodb.html#ref-dynamodb-conditions
    #fe = Key('year').between(1950, 1959);
    fe = Attr('body').ne(None) # TODO: does this work?
    pe = '#u,host,body' # TODO: updated as well...
    ean = {'#u': 'url',}
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
    'www.bergdorfgoodman.com': ProductsBergdorfGoodman,
    'www.bluefly.com':      ProductsBluefly,
    'www.dermstore.com':    ProductsDermstore,
    'www.farfetch.com':     ProductsFarfetch,
    'www.lordandtaylor.com': ProductsLordandTaylor,
    'www1.macys.com':       ProductsMacys,
    'www.neimanmarcus.com': ProductsNeimanMarcus,
    'www.net-a-porter.com': ProductsNetaPorter,
    'www.saksfifthavenue.com': ProductsSaks,
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

    recv = 0
    #print 'min_handle:', min_handle
    try:
        results = _get_nowait(q2)
        while results is not None or (recv < min_handle):
            if results is not None:
                recv += 1
                assert isinstance(results, ProductMapResult)
                results.save()
            if results is None and recv < min_handle:
                time.sleep(0.1) # avoid too-hot a loop
            results = _get_nowait(q2)
    except KeyboardInterrupt:
        pass
    return recv

man = multiprocessing.Manager()
q1 = man.Queue()
q2 = man.Queue()

# our worker processes don't peg the CPU due to i/o
# so if we directly map 1:1 w/ CPU we waste a lot of resources
POOLSIZE = multiprocessing.cpu_count() * 2
pool = multiprocessing.Pool(POOLSIZE, worker, (q1, q2,))

sent = 0
recv = 0

# parsing the HTML is dreadfully slow old sport
# so we had to pool our CPUs don't you know

'''
scan all links in dynamodb
if a link has a body, and we have a ProductMapper for that host
    enqueue it for the worker processes
    also, process their output
'''
try:
    for link in each_link():
        sha256 = link['body']
        host = link['host']
        if sha256 and host in Host2Map:
            sha256 = bytearray(sha256.value) # extract raw binary
            url = link['url']
            sent += 1
            print sent, url
            q1.put((url, host, sha256))
            if sent - recv >= POOLSIZE * 2:
                # input queue full enough, process output.
                # throttles input rate
                recv += handle_responses(q2, min_handle=1)
    handle_responses(q2, sent - recv)
except KeyboardInterrupt:
    try:
        pool.terminate()
    except:
        pass

print 'done'

