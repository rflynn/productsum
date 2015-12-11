# ex: set ts=4 et:
# -*- encoding: utf-8 -*-

import boto3
from boto3.dynamodb.conditions import Key, Attr


def fetchall(table, url_host=None, url_contains=None):

    assert url_host
    assert url_contains

    fe = Attr('url').contains(url_contains)
    pe = '#u'
    ean = {'#u': 'url',}

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
        retry_sleep = 1
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
            except Exception as e:
                # e.g. OpenSSL.SSL.SysCallError
                print e
                time.sleep(retry_sleep)
                if retry_sleep < 60:
                    retry_sleep *= 2 # exponential backoff
            for item in resp['Items']:
                yield item

if __name__ == '__main__':

    def deleteall(url_host, url_contains):
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('link')
        seq = fetchall(table, url_host=url_host, url_contains=url_contains)
        for item in seq:
            url = item['url']
            print url
            print table.delete_item(Key={'url': url})

    #deleteall('www.fwrd.com', '/fw/Login.jsp')
    #deleteall('www.zappos.com', '/favorites.do')
    #deleteall('www.barneys.com', '/on/')

    #deleteall('www.net-a-porter.com', '?image_view=')
    #deleteall('www.mytheresa.com', '%7C')
    #deleteall('www.dermstore.com', '/list_')
    #deleteall('www.saksfifthavenue.com', '/stores/stores.jsp?')
    #deleteall('www.bluefly.com', 'jsessionid=')
    #deleteall('www.shopbop.com', '/actions/')
    #deleteall('www.yoox.com', '/kg/')
    #deleteall('www.yoox.com', '/ma/')
    #deleteall('www.yoox.com', '/mk/')
    #deleteall('www.yoox.com', '/tw/')
    #deleteall('www.yoox.com', '/am/')
