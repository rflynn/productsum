# ex: set ts=4 et:

'''
report how many urls we've spidered from each host (fqdn)
dynamodb equivalent of 'select host, count(*) from link group by host;
'''

import boto3
import json
import decimal
from boto3.dynamodb.conditions import Key, Attr
import sys
from collections import Counter

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('link')

#fe = Key('year').between(1950, 1959);
#pe = "#yr, title, info.rating"
pe = 'host'
# Expression Attribute Names for Projection Expression only.
#ean = { "#yr": "year", }
esk = None

resp = table.scan(
    #FilterExpression=fe,
    ProjectionExpression=pe
    #ExpressionAttributeNames=ean
)

def sortprint(c):
    for k, v in sorted(c.items(), key=lambda x:x[1], reverse=True):
        print '%7d %s' % (v, k)

c = Counter()

for i in resp['Items']:
    c[i.get('host')] += 1

loopcnt = 1
while 'LastEvaluatedKey' in resp:
    loopcnt += 1
    print resp.get('LastEvaluatedKey')
    resp = table.scan(
        ProjectionExpression=pe,
        #FilterExpression=fe,
        #ExpressionAttributeNames=ean,
        ExclusiveStartKey=resp['LastEvaluatedKey']
    )
    for i in resp['Items']:
        c[i.get('host')] += 1

sortprint(c)

print 'loopcnt:', loopcnt

'''
Mon Nov 30 20:48:21 EST 2015

  19357 shop.nordstrom.com
  19175 www.neimanmarcus.com
  17728 www.luisaviaroma.com
  15355 www.farfetch.com
  15289 www.bergdorfgoodman.com
  13438 www.violetgrey.com
  10888 www1.macys.com
   8888 www.bluefly.com
   8641 www.mytheresa.com
   7407 www.saksfifthavenue.com
   7391 www.barneys.com
   7287 www.fwrd.com
   4823 www.ssense.com
   4100 www.yoox.com
   4091 www.shopbop.com
   3957 www.net-a-porter.com
   2276 www.sephora.com
   1587 www.dermstore.com
   1525 www.revolveclothing.com
    364 www.stuartweitzman.com
done

real    7m22.220s
user    0m13.315s
sys     0m0.656s
'''
