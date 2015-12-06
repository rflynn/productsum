# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from neimanmarcus.com to zero or more products
'''

from BeautifulSoup import BeautifulSoup
import base64
import gzip
import json
from pprint import pprint
import re
import requests
import time

from htmlmetadata import HTMLMetadata
from og import OG
from schemaorg import SchemaOrg
from tealium import Tealium


class ProductBergdorfGoodman(object):
    def __init__(self, prodid=None, canonical_url=None,
                 stocklevel=None, instock=None,
                 name=None, descr=None,
                 price=None, currency=None,
                 img_url=None,
                 bread_crumb=[],
                 cmos_catalog_id=None,
                 cmos_item=None,
                 cmos_sku=None):

        assert prodid is None or isinstance(prodid, basestring)
        assert canonical_url is None or isinstance(canonical_url, basestring)
        assert stocklevel is None or isinstance(stocklevel, basestring)
        assert instock is None or isinstance(instock, basestring)
        assert name is None or isinstance(name, basestring)
        assert descr is None or isinstance(descr, basestring)
        assert price is None or isinstance(price, basestring)
        assert currency is None or isinstance(currency, basestring)
        assert img_url is None or isinstance(img_url, basestring)
        assert isinstance(bread_crumb, list)
        assert cmos_catalog_id is None or isinstance(cmos_catalog_id, basestring)
        assert cmos_item is None or isinstance(cmos_item, basestring)
        assert cmos_sku is None or isinstance(cmos_sku, basestring)

        self.prodid = prodid
        self.canonical_url = canonical_url
        self.stocklevel = stocklevel
        self.instock = instock
        self.name = re.sub('\s+', ' ', name.strip()) if name else None
        self.descr = descr
        self.price = price
        self.currency = currency
        self.img_url = img_url
        self.bread_crumb = bread_crumb
        self.cmos_catalog_id = cmos_catalog_id
        self.cmos_item = cmos_item
        self.cmos_sku = cmos_sku

    def __repr__(self):
        return '''ProductBerfordGoodman:
    prodid...........%s
    url..............%s
    instock..........%s
    stocklevel.......%s
    name.............%s
    descr............%s
    price............%s
    currency.........%s
    img_url..........%s
    bread_crumb......%s
    cmos_catalog_id..%s
    cmos_item........%s
    cmos_sku.........%s
''' % (self.prodid,
       self.canonical_url,
       self.instock,
       self.stocklevel,
       self.name,
       self.descr,
       self.price,
       self.currency,
       self.img_url,
       self.bread_crumb,
       self.cmos_catalog_id,
       self.cmos_item,
       self.cmos_sku)


class ProductsBergdorfGoodman(object):

    @staticmethod
    def from_html(url, html):

        products = []

        sp = SchemaOrg.get_schema_product(html)
        og = OG.get_og(html)
        soup = BeautifulSoup(html)
        meta = HTMLMetadata.do_html_metadata(soup)
        utag = Tealium.get_utag_data(soup)

        pprint(utag)

        # is there one or more product on the page?
        if (sp
            or utag.get(u'page_type') == u'Product Detail'
            or og.get('type') == u'product'):
            # ok, there's 1+ product. extract them...
            assert len(sp) < 2
            if sp:
                sp = sp[0]

            name = None
            if utag.get(u'product_name'):
                name = utag[u'product_name'][0]
            else:
                name = (og.get('title') or
                        meta.get('title') or None)

            p = ProductBergdorfGoodman(
                prodid=utag.get('product_id')[0] or None,
                canonical_url=url,
                stocklevel=utag.get('stock_level')[0] or None,
                instock=utag.get('product_available')[0] or None,
                name=name,
                descr=' '.join(sp.get('description') or []) or None,
                price=utag.get('product_price')[0] or None,
                currency=utag.get('order_currency_code'),
                img_url=None,
                bread_crumb=utag.get('bread_crumb') or [],
                cmos_catalog_id=(utag['product_cmos_catalog_id'][0]
                                    if 'product_cmos_catalog_id' in utag else None),
                cmos_item=utag['product_cmos_item'][0] if 'product_cmos_item' in utag else None,
                cmos_sku=utag['product_cmos_sku'][0] if 'product_cmos_sku' in utag else None,
            )
            products.append(p)

        return products


if __name__ == '__main__':

    filepath = 'www.bergdorfgoodman.com-Christian-Louboutin-So-Kate-Patent-Red-Sole-Pump-Nude-Pumps-prod109600142_cat379623__-p.prod.gz'

    products = []

    with gzip.open(filepath) as f:
        html = f.read()
        products = ProductsBergdorfGoodman.from_html('http://bergdorfgoodman.example/', html)

    print products


'''
'''
