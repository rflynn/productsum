# ex: set ts=4 et:

import microdata
from pprint import pprint


'''
some merchants use http://www.data-vocabulary.org/Product/
a less popular variant of schema.org
ref: http://www.data-vocabulary.org/Product/
ref: http://schema.org/
ref: https://en.wikipedia.org/wiki/Resource_Description_Framework
'''
class DataVocabulary(object):

    @staticmethod
    def get_schema_product(html):
        items = microdata.get_items(html)
        print items
        product_uri = microdata.URI('http://data-vocabulary.org/Product')
        products = [i for i in items
                        if product_uri in i.itemtype]
        print products

        prods = [dict(product.json_dict()['properties'])
                    for product in products]
        pprint(prods)
        return prods


