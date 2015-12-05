# ex: set ts=4 et:

import boto3


bucket = 'productsum-spider'
#s3 = boto3.client('s3')
#l = s3.list_objects(Bucket=bucket)
#b = s3.Bucket(bucket)

client = boto3.client('s3')
paginator = client.get_paginator('list_objects')
for result in paginator.paginate(Bucket=bucket, Delimiter='/'):
    for prefix in result.get('CommonPrefixes'):
        print(prefix.get('Prefix'))


'''
'''
