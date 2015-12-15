# ex: set ts=4 et:
# -*- coding: utf-8 -*-

import elasticsearch
from elasticsearch.helpers import bulk, streaming_bulk
# ref: https://github.com/elastic/elasticsearch-py/blob/master/example/load.py

from dbconn import get_psql_conn
from psycopg2.extras import RealDictCursor
# "analyzer": "english"

# http://stackoverflow.com/questions/15079064/how-to-setup-a-tokenizer-in-elasticsearch
# https://www.elastic.co/guide/en/elasticsearch/reference/1.4/analysis-ngram-tokenizer.html

schema = \
{
    'settings': {
        'analysis': {
            'filter': {
                'custom_stem': {
                    'type': 'stemmer_override',
                    'rules': [
                        'pumps=>pump',
                        'spiked=>spike',
                        'spikes=>spike',
                        'lacquer=>polish'
                    ]
                }
            },
        'analyzer': {
            'my_english': {
                'tokenizer': 'standard',
                    'filter': [
                        'lowercase',
                        'custom_stem',
                        'porter_stem'
                    ]
                }
            }
        }
    },
    'mappings': {
        'product': {
            'properties': {
                'updated':        { 'type': 'long'   },
                'merchant_sku':   { 'type': 'string' },
                'url_host':       { 'type': 'string' },
                'url':            { 'type': 'string' },
                'brand':          { 'type': 'string' },
                'name':           { 'type': 'string' },
                'descr':          { 'type': 'string', 'index': 'not_analyzed'},
                'in_stock':       { 'type': 'boolean'},
                'stock_level':    { 'type': 'long'   },
                'currency':       { 'type': 'string', 'index': 'not_analyzed'},
                'price_min':      { 'type': 'float'  },
                'price_max':      { 'type': 'float'  },
                'sale_price_min': { 'type': 'float'  },
                'sale_price_max': { 'type': 'float'  },
                #'img_url':        { 'type': 'string', 'index': 'not_analyzed' },
                #'img_urls':       { 'type': 'array', 'index': 'not_analyzed' }, # WTF?
            }
        }
    }
}

def get_rows(conn):
    with conn.cursor('serversidecursor', cursor_factory=RealDictCursor) as cursor:
        cursor.execute('''
select
    extract(epoch from up.updated) as updated,
    merchant_sku,
    url_host,
    url_canonical as url,
    coalesce(bt.brand_to, up.brand) as brand,
    name,
    substr(descr, 0, 4096) as descr,
    in_stock,
    stock_level,
    currency,
    price_min,
    price_max,
    sale_price_min,
    sale_price_max,
    img_urls
from url_product up
left join brand_translate bt
    on bt.brand_from = up.brand
-- limit 1000
''')
        for row in cursor:
            yield dict(row)

'''
curl -XPOST 'localhost:9200/test/type1/1/_update' -d '{
    'doc' : {
        'name' : 'new_name'
    },
    'doc_as_upsert' : true
}'
'''

if __name__ == '__main__':

    import sys

    conn = get_psql_conn()

    es = elasticsearch.Elasticsearch(
        ['search-es0-qjusld7s4jpxxcsy2ktlkfr42m.us-east-1.es.amazonaws.com:80']
    )

    if es.indices.exists('product'):
        print "deleting '%s' index..." % ('product')
        res = es.indices.delete(index='product')
        print " response: '%s'" % (res)

    print es.info()

    es.indices.create(index='product',
                      body=schema)

    cnt = 0
    for ok, result in streaming_bulk(es, get_rows(conn),
                                     doc_type='product', index='product',
                                     chunk_size=1000, max_chunk_bytes=8*1024*1024):
        cnt += 1
        if cnt % 1000 == 0:
            print cnt,
            sys.stdout.flush()
    print cnt

    es.indices.refresh(index='product')

