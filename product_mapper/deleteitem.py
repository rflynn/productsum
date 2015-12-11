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
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('link')

    seq = fetchall(table, url_host='www.net-a-porter.com', url_contains='?image_view=')
    for item in seq:
        url = item['url']
        print url
        print table.delete_item(Key={'url': url})
        #Key={'url':{'S': url}},

