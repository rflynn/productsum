# ex: set ts=4 et:

import boto3 as boto

# ref: http://boto3.readthedocs.org/en/latest/guide/dynamodb.html
# ref: http://boto3.readthedocs.org/en/latest/reference/customizations/dynamodb.html

# Get the service resource.
dynamodb = boto.resource('dynamodb')

# Create the DynamoDB table.
table = dynamodb.create_table(
    TableName='link',
    KeySchema=[
        {
            'AttributeName': 'url',
            'KeyType': 'HASH'
        },
    ],
    AttributeDefinitions=[
        {
            'AttributeName': 'url',
            'AttributeType': 'S'
        },
    ],
    # don't know enough about these...
    #LocalSecondaryIndexes=[],
    #GlobalSecondaryIndexes=[],
    #StreamSpecification={},
    ProvisionedThroughput={
        'ReadCapacityUnits': 25,
        'WriteCapacityUnits': 25,
    }
)

'''
        {
            'AttributeName': 'datetime_created',
            'AttributeType': 'N'
        },
        {
            'AttributeName': 'datetime_updated',
            'AttributeType': 'N'
        },
        {
            'AttributeName': 'datetime_last_ok',
            'AttributeType': 'N'
        },

        {
            'AttributeName': 'url',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'host',
            'AttributeType': 'S'
        },

        # fetch
        {
            'AttributeName': 'fetch_url_canonical',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'fetch_code',
            'AttributeType': 'N'
        },
        {
            'AttributeName': 'fetch_origbytes',
            'AttributeType': 'N'
        },
        {
            'AttributeName': 'fetch_savebytes',
            'AttributeType': 'N'
        },
        {
            'AttributeName': 'fetch_mimetype',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'fetch_sha256',
            'AttributeType': 'B'
        },

        # save a set of outgoing links
        {
            'AttributeName': 'fetch_links',
            'AttributeType': 'S' # WTF: want an 'SS' here...
        },
'''

# Wait until the table exists.
table.meta.client.get_waiter('table_exists').wait(TableName='link')

# Print out some data about the table.
print(table.item_count)

