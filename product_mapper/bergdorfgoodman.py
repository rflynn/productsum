# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from bergdorfgoodman.com to zero or more products
'''

from bs4 import BeautifulSoup, NavigableString
import base64
import gzip
import json
from pprint import pprint
import re
import requests
import time

from htmlmetadata import HTMLMetadata
from og import OG
from product import Product, ProductMapResultPage, ProductMapResult
from schemaorg import SchemaOrg
from tealium import Tealium
from util import nth, normstring, dehtmlify, maybe_join, xboolstr, xint

MERCHANT_SLUG = 'bergdorfgoodman'


class ProductBergdorfGoodman(object):
    VERSION = 0
    def __init__(self, prodid=None, canonical_url=None,
                 stocklevel=None, in_stock=None,
                 bread_crumb=None, brand=None,
                 price=None, currency=None,
                 name=None, title=None, descr=None,
                 features=None, color=None, size=None,
                 img_url=None,
                 cmos_catalog_id=None,
                 cmos_item=None,
                 cmos_sku=None):

        assert isinstance(prodid,          basestring)
        assert isinstance(canonical_url,   basestring)
        assert isinstance(stocklevel,      (type(None), int))
        assert isinstance(in_stock,        (type(None), bool))
        assert isinstance(bread_crumb,     (type(None), list))
        assert isinstance(brand,           (type(None), basestring))
        assert isinstance(price,           (type(None), basestring))
        assert isinstance(currency,        (type(None), basestring))
        assert isinstance(name,            (type(None), basestring))
        assert isinstance(title,           (type(None), basestring))
        assert isinstance(descr,           (type(None), basestring))
        assert isinstance(features,        (type(None), list))
        assert isinstance(color,           (type(None), basestring))
        assert isinstance(size,            (type(None), basestring))
        assert isinstance(img_url,         (type(None), basestring))
        assert isinstance(cmos_catalog_id, (type(None), basestring))
        assert isinstance(cmos_item,       (type(None), basestring))
        assert isinstance(cmos_sku,        (type(None), basestring))

        self.prodid = prodid
        self.canonical_url = canonical_url
        self.stocklevel = stocklevel
        self.in_stock = in_stock
        self.bread_crumb = bread_crumb
        self.brand = brand
        self.price = price
        self.currency = currency
        self.name = normstring(name)
        self.title = title
        self.descr = descr
        self.features = features
        self.color = color
        self.size = size
        self.img_url = img_url
        self.cmos_catalog_id = cmos_catalog_id
        self.cmos_item = cmos_item
        self.cmos_sku = cmos_sku

        # fixups
        # weird case; the descriptions are shitty; at least we clean up the text slightly... :-/
        if self.descr and self.features:
            if self.descr == u''.join(self.features):
                self.descr = u' '.join(self.features)

    def __repr__(self):
        return '''ProductBerfordGoodman:
    prodid...........%s
    url..............%s
    in_stock.........%s
    stocklevel.......%s
    bread_crumb......%s
    brand............%s
    price............%s
    currency.........%s
    name.............%s
    title............%s
    descr............%s
    feautures........%s
    color............%s
    size.............%s
    img_url..........%s
    cmos_catalog_id..%s
    cmos_item........%s
    cmos_sku.........%s
''' % (self.prodid,
       self.canonical_url,
       self.in_stock,
       self.stocklevel,
       self.bread_crumb,
       self.brand,
       self.price,
       self.currency,
       self.name,
       self.title,
       self.descr,
       self.features,
       self.color,
       self.size,
       self.img_url,
       self.cmos_catalog_id,
       self.cmos_item,
       self.cmos_sku)

    def to_product(self):
        return Product(
            merchant_slug=MERCHANT_SLUG,
            url_canonical=self.canonical_url,
            merchant_sku=self.prodid,
            merchant_product_obj=self,
            price=self.price,
            sale_price=None,
            currency=self.currency,
            brand=self.brand,
            in_stock=self.in_stock,
            stock_level=None,
            name=self.name,
            title=self.title,
            descr=self.descr,
            features=self.features,
            color=self.color,
            available_colors=None,
            size=self.size,
            available_sizes=None,
            img_url=self.img_url,
            img_urls=[self.img_url] if self.img_url else None
        )


class ProductsBergdorfGoodman(object):

    VERSION = 0

    @staticmethod
    def get_custom(soup, html, url):
        data = {}
        brand = None
        name = None
        descr = None
        features = None
        url_canonical = None
        # brand
        tag = soup.find('a', itemprop='brand')
        if tag:
            brand = normstring(tag.text)

        # <span id="lbl_DesignerSingleItem" class="product-designer">Tata Harper</span>
        tag = soup.find('span', {'id': 'lbl_DesignerSingleItem',
                                 'class': 'product-designer'}, text=True)
        if tag and hasattr(tag, 'text') and tag.text:
            brand = brand or normstring(tag.text)

        # <input class="cmDesignerName" type="hidden" disabled="disabled" value="Tata Harper" />
        tag = soup.find('input', {'class': 'cmDesignerName'}, value=True)
        if tag and tag.get('value'):
            brand = brand or normstring(tag.get('value'))

        tag = soup.find('h1', itemprop='name')
        if tag:
            try:
                tag = tag.contents[0]
                if isinstance(tag, NavigableString):
                    # ensure this is a bare piece of text within the name tag; we don't want the whole name, just the brand prefix
                    brand = brand or normstring(tag)
            except Exception as e:
                print e
        # name
        '''
        <span class="product-displayname">Apostrophy Pointed Red-Sole Pump, Black</span>
        '''
        tag = soup.find('span', {'class': 'product-displayname'})
        if tag:
            name = normstring(tag.text)
        # features
        tag = soup.find('div', itemprop='description')
        if tag:
            features = [normstring(f.text) for f in tag.findAll('li') or []] or None
        # url_canonical
        tag = soup.find('meta', itemprop='url')
        if tag:
            url_canonical = tag.get('content')

        #itemprops = soup.findAll(itemprop=True)
        
        data = {
            'url_canonical': url_canonical,
            'brand': brand,
            'name': name,
            'descr': descr,
            #'itemprops': itemprops,
            'features': features,
        }
        return data

    @classmethod
    def from_html(cls, url, html, updated=None):

        starttime = time.time()

        if '/search.jsp?' in url:
            # search results are not products
            page = ProductMapResultPage(
                    version=cls.VERSION,
                    merchant_slug=MERCHANT_SLUG,
                    url=url,
                    size=len(html),
                    proctime = time.time() - starttime,
                    signals={},
                    updated=updated)
            return ProductMapResult(page=page,
                                    products=[])

        products = []

        soup = BeautifulSoup(html)
        sp1 = SchemaOrg.get_schema_product(html)
        og = OG.get_og(soup)
        meta = HTMLMetadata.do_html_metadata(soup)
        utag = Tealium.get_utag_data(soup)
        custom = cls.get_custom(soup, html, url)

        # we get multiple... merge em!
        sp = {}
        for s in sp1:
            for k, v in s.iteritems():
                sp[k] = v

        signals = {
            'sp':   SchemaOrg.to_json(sp),
            'og':   og,
            'meta': meta,
            'utag': utag,
            'custom': custom,
        }
        #pprint(signals)

        prodid = nth(utag.get('product_id'), 0) or None
        canonical_url=(custom.get('url_canonical')
                        or nth(sp.get('url'), 0)
                        or custom.get('url')
                        or url) # og[url] is fucked...

        # is there one or more product on the page?
        if prodid and canonical_url:

            p = ProductBergdorfGoodman(
                prodid=prodid,
                canonical_url=canonical_url,
                stocklevel=xint(nth(utag.get('stock_level'), 0)) or None,
                in_stock=xboolstr(nth(utag.get('product_available'), 0) or None),
                brand=( # sp lists a url path as the brand, not the brand name. ugh...
                        custom.get('brand') or None),
                price=nth(utag.get('product_price'), 0) or None,
                currency=utag.get('order_currency_code') or None,
                name=(custom.get('name')
                        or nth(utag.get(u'product_name'), 0)
                        or og.get('title')
                        or meta.get('title') or None),
                title=(custom.get('title')
                        or og.get('title')
                        or meta.get('title') or None),
                descr=maybe_join(' ', sp.get('description')) or None,
                features=custom.get('features'),
                img_url=og.get('image') or None,
                bread_crumb=utag.get('bread_crumb') or None,
                cmos_catalog_id=nth(utag.get('product_cmos_catalog_id'), 0) or None,
                cmos_item=nth(utag.get('product_cmos_item'), 0) or None,
                cmos_sku=nth(utag.get('product_cmos_sku'), 0) or None)

            products.append(p)

        realproducts = [p.to_product() for p in products]

        page = ProductMapResultPage(
                    version=cls.VERSION,
                    merchant_slug=MERCHANT_SLUG,
                    url=url,
                    size=len(html),
                    proctime = time.time() - starttime,
                    signals=signals,
                    updated=updated)

        return ProductMapResult(page=page,
                                products=realproducts)


if __name__ == '__main__':

    url = 'http://www.bergdorfgoodman.com/Christian-Louboutin-Apostrophy-Pointed-Red-Sole-Pump-Black-Pumps/prod113370002_cat379623__/p.prod'

    # test no-op
    #filepath = 'test/www.dermstore.com-product_Lipstick_31136.htm.gz'

    # test 1 product
    filepath = 'test/www.bergdorfgoodman.com-Christian-Louboutin-So-Kate-Patent-Red-Sole-Pump-Nude-Pumps-prod109600142_cat379623__-p.prod.gz'

    #filepath = 'www.bergdorfgoodman.com-Tata-Harper-Boosted-Contouring-Eye-Mask-1-0-oz-prod111290137-p.prod.gz'

    # skip by url
    #url = 'http://www.bergdorfgoodman.com/search.jsp?N=4294967088&from=saledi&rd=1&Ntt=Elie+Tahari'

    with gzip.open(filepath) as f:
        html = f.read()

    products = ProductsBergdorfGoodman.from_html(url, html)
    print products

