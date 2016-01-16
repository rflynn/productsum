# ex: set ts=4 et:
# -*- encoding: utf-8 -*-

import boto3
import botocore
from boto3.dynamodb.conditions import Key, Attr
import time


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
                IndexName='host-index3',
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
                    IndexName='host-index3',
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
            while True:
                try:
                    print table.delete_item(Key={'url': url})
                    break
                except botocore.exceptions.ClientError as e:
                    print e
                    time.sleep(10)


    #deleteall('www.yoox.com', '/TellAFriend')

    #deleteall('www.dillards.com', '/webapp/wcs/stores/servlet/ReviewForm')
    #deleteall('www.dillards.com', 'void(0)')

    #deleteall('www.ulta.com', '/_/N-')
    #deleteall('www.jcpenney.com', '/_/N-')
    #deleteall('www.saksfifthavenue.com', '/_/N-')
    #deleteall('www.target.com', '/_/N-')
    #deleteall('www.cvs.com', '/_/N-')
    #deleteall('www.cvs.com', '/N-')

    #deleteall('www.jcpenney.com', '/jsp/')

    #deleteall('www.tradesy.com', '/tel:')

    #deleteall('www.ln-cc.com', '/send-to-friend')

    #deleteall('www.skinstore.com', '/ContentPages/BazaarVoiceLogin.aspx')

    #deleteall('www.narscosmetics.com', '/Wishlist-Add')
    #deleteall('www.narscosmetics.com', '/SendToFriend-')
    #deleteall('www.narscosmetics.com', '/null')

    #deleteall('www.cvs.com', '/stores/cvs-pharmacy-locations/')
    #deleteall('www.cvs.com', '/store-locator/')

    #deleteall('www.bluemercury.com', '/quick-view.aspx')

    #deleteall('www.beautylish.com', '/review/')

    #deleteall('www.michaelkors.com', '/')

    #deleteall('www.cvs.com', ';jsessionid=')
    #deleteall('www.cvs.com', '/minuteclinic/')

    #deleteall('www.walmart.com', '/')

    #deleteall('www.mytheresa.com', '/de-de/')
    #deleteall('www.ssense.com', '/fr-fr/')

    # nuke all javascript-requiring sites before we had selenim set up
    #deleteall('www.stuartweitzman.com', '/')
    #deleteall('www.thecorner.com', '/')
    #deleteall('www.luisaviaroma.com', '/')
    #deleteall('www.sephora.com', '/')

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
