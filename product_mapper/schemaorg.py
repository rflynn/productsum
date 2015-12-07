# ex: set ts=4 et:

from collections import defaultdict
import microdata
from pprint import pprint


'''
a surprising number of merchants use schema.org metadata
ref: http://schema.org/
ref: https://en.wikipedia.org/wiki/Resource_Description_Framework
'''
class SchemaOrg(object):

    @staticmethod
    def get_schema_items(html):
        items = microdata.get_items(html)
        return [i.json_dict() for i in items]

    @staticmethod
    def get_schema_product(html):
        items = microdata.get_items(html) or []
        p1 = microdata.URI(u'http://schema.org/Product')
        p2 = microdata.URI(u'http://schema.org/IndividualProduct')
        products = [i for i in items
                        if p1 in (i.itemtype or []) or p2 in (i.itemtype or [])]
        '''
        for p in products:
            print p.itemtype
            print p.json_dict()
        print products
        '''

        prods = [dict(p.json_dict()['properties'])
                    for p in products]
        #pprint(prods)
        return prods

    @staticmethod
    def to_json(sp):
        # strip the defaultdicts out
        if isinstance(sp, list):
            return [SchemaOrg.to_json(x) for x in sp]
        elif isinstance(sp, (dict, defaultdict)):
            return {k: SchemaOrg.to_json(v) for k, v in sp.iteritems()}
        else:
            return sp

