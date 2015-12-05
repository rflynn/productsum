# ex: set ts=4 et:

import boto3


if __name__ == '__main__':

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('link')

    print 'item_count:', table.item_count
    print 'table_size_bytes:', table.table_size_bytes

'''
>>> dynamodb = boto3.resource('dynamodb')
>>> table = dynamodb.Table('link')
>>> print(table.creation_date_time)
2015-11-29 00:56:24.850000-05:00
>>> dir(table)
['__class__', '__delattr__', '__dict__', '__doc__', '__eq__', '__format__', '__getattribute__', '__hash__', '__init__', '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_injector', '_name', u'attribute_definitions', 'batch_writer', u'creation_date_time', u'delete', u'delete_item', u'get_item', u'global_secondary_indexes', u'item_count', u'key_schema', u'latest_stream_arn', u'latest_stream_label', 'load', u'local_secondary_indexes', 'meta', u'name', u'provisioned_throughput', u'put_item', u'query', 'reload', u'scan', u'stream_specification', u'table_arn', u'table_name', u'table_size_bytes', u'table_status', u'update', u'update_item']
>>> print(table.item_count)
71285
>>> print(table.table_size_bytes)
426782383
'''

'''
>>> client.get_item(TableName='link', Key={'url':{'S':'http://www.saksfifthavenue.com/'}})
{u'Item': {u'lastok': {u'N': u'1448853157'}, u'body': {u'NULL': True}, u'updated': {u'N': u'1448853157'}, u'code': {u'N': u'200'}, u'links': {u'NULL': True}, u'created': {u'N': u'1448853157'}, u'url': {u'S': u'http://www.saksfifthavenue.com/'}, u'host': {u'S': u'www.saksfifthavenue.com'}, u'clen': {u'NULL': True}, u'olen': {u'N': u'339294'}, u'mime': {u'S': u'text/html'}, u'url_canon': {u'S': u'http://www.saksfifthavenue.com/Entry.jsp'}}, 'ResponseMetadata': {'HTTPStatusCode': 200, 'RequestId': 'MV4H9KLK4JDNTABJ0P42H5LIL3VV4KQNSO5AEMVJF66Q9ASUAAJG'}}
>>> client.delete_item(TableName='link', Key={'url':{'S':'http://www.saksfifthavenue.com/'}})
{'ResponseMetadata': {'HTTPStatusCode': 200, 'RequestId': '45QUQPK3HORA38EMSLI0QV0UURVV4KQNSO5AEMVJF66Q9ASUAAJG'}}
'''
