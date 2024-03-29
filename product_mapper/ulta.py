# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from ulta.com to zero or more products
'''

from bs4 import BeautifulSoup
import gzip
import json
from pprint import pprint
import re
import time
import traceback

from htmlmetadata import HTMLMetadata
from og import OG
from product import Product, ProductMapResultPage, ProductMapResult
from schemaorg import SchemaOrg
from tealium import Tealium
from util import nth, normstring, dehtmlify, xboolstr, xstrip


MERCHANT_SLUG = 'ulta'


class ProductUlta(object):
    VERSION = 0
    def __init__(self, id=None, url=None, merchant_name=None, slug=None,
                 merchant_sku=None, upc=None, isbn=None, ean=None,
                 currency=None, sale_price=None, price=None,
                 brand=None, category=None, breadcrumb=None,
                 in_stock=None, stock_level=None,
                 name=None, title=None, descr=None,
                 material=None, features=None,
                 color=None, colors=None,
                 size=None, sizes=None,
                 img_url=None, img_urls=None):

        self.id = id
        self.url = url
        self.merchant_name = merchant_name
        self.slug = slug
        self.merchant_sku = merchant_sku
        self.upc = upc
        self.isbn = isbn
        self.ean = ean
        self.currency = currency
        self.sale_price = sale_price
        self.price = price
        self.brand = brand
        self.category = category
        self.breadcrumb = breadcrumb
        self.in_stock = in_stock
        self.stock_level = stock_level
        self.name = name
        self.title = title
        self.descr = descr
        self.material = material
        self.features = features
        self.color = color
        self.colors = colors
        self.size = size
        self.sizes = sizes
        self.img_url = img_url
        self.img_urls = img_urls

        # fixup
        if self.id is not None:
            self.id = str(self.id) # ensure we're a string, some signals produce numeric
        assert self.id != 'None'
        if self.price:
            self.price = normstring(self.price).replace(' ', '')
        if isinstance(self.brand, list):
            self.brand = u' '.join(self.brand) or None
        self.brand = dehtmlify(normstring(self.brand))
        if isinstance(self.name, list):
            self.name = u' '.join(self.name) or None
        self.name = dehtmlify(normstring(self.name))
        self.title = dehtmlify(normstring(self.title))
        if isinstance(self.descr, list):
            self.descr = u' '.join(self.descr) or None
        self.descr = dehtmlify(normstring(self.descr))
        if self.features:
            self.features = [dehtmlify(f) for f in self.features]

        if self.name:
            if 'Ulta.com - ' in self.name:
                self.name = xstrip(self.name[:self.name.index('Ulta.com - ')]) or None
            if self.name:
                if self.name.lower().startswith('online only'):
                    self.name = self.name[len('online only'):].lstrip() or None

        if self.title:
            if 'Ulta.com - ' in self.title:
                self.title = xstrip(self.title[:self.title.index('Ulta.com - ')]) or None
            if self.title:
                if self.title.lower().startswith('online only'):
                    self.title = self.title[len('online only'):].lstrip() or None

    def __repr__(self):
        return ('''ProductUlta:
    id............... %s
    url.............. %s
    merchant_name.... %s
    merchant_sku..... %s
    slug............. %s
    upc.............. %s
    isbn............. %s
    ean.............. %s
    currency......... %s
    sale_price....... %s
    price............ %s
    brand............ %s
    category......... %s
    breadcrumb....... %s
    in_stock......... %s
    stock_level...... %s
    name............. %s
    title............ %s
    descr............ %s
    material......... %s
    features......... %s
    color............ %s
    colors........... %s
    sizes............ %s
    img_url.......... %s
    img_urls......... %s''' % (
       self.id,
       self.url,
       self.merchant_name,
       self.merchant_sku,
       self.slug,
       self.upc,
       self.isbn,
       self.ean,
       self.currency,
       self.sale_price,
       self.price,
       self.brand,
       self.category,
       self.breadcrumb,
       self.in_stock,
       self.stock_level,
       self.name,
       self.title,
       self.descr,
       self.material,
       self.features,
       self.color,
       self.colors,
       self.sizes,
       self.img_url,
       self.img_urls)).encode('utf8')

    def to_product(self):

        if not self.colors:
            available_colors = None
        elif self.colors == [u'No Color']:
            available_colors = []
        else:
            available_colors = [c for c in self.colors if c]

        if not self.sizes:
            available_sizes = None
        elif self.sizes == [None]:
            available_sizes = []
        else:
            available_sizes = [s for s in self.sizes if s]

        return Product(
            merchant_slug=MERCHANT_SLUG,
            url_canonical=self.url,
            merchant_sku=self.id,
            merchant_product_obj=self,
            price=self.price,
            sale_price=self.sale_price,
            currency=self.currency,
            brand=self.brand,
            category=self.category,
            in_stock=self.in_stock,
            stock_level=None,
            name=self.name,
            title=self.title,
            descr=self.descr,
            features=self.features,
            color=self.color,
            available_colors=available_colors,
            size=None,
            available_sizes=available_sizes,
            img_url=self.img_url,
            img_urls=sorted(self.img_urls) if self.img_urls is not None else None
        )


class ProductsUlta(object):

    VERSION = 0

    @staticmethod
    def get_custom(soup, url):

        brand = None
        category = None
        breadcrumbs = None
        name = None
        descr = None
        sku = None
        productid = None
        slug = None
        colors = None
        sizes = None
        img_url = None

        try:
            canonical_url = soup.find('link', rel='canonical').get('href')
        except:
            canonical_url = url

        form = soup.find('form', id='pdp_addToCart')
        if form:
            hidden = {t['name']: t['value']
                        for t in soup.findAll('input',
                                    {'type':'hidden',
                                     'name':True,
                                     'value':True})}
            sku = hidden.get('pinSkuId')
            brand = hidden.get('pinBrand')
            name = hidden.get('pinDisplay')
            productid = hidden.get('pinProduct')

        js = {}
        blz = soup.find('script', type='text/blzscript', text=lambda t: t and 'var pageData' in t)
        if blz:
            try:
                code = re.search('({.*})', blz.text, re.DOTALL).groups(0)[0]
                #print code
                js = json.loads(code)
                prod = js['product']
                brand = brand or prod.get('brand')
                category = category or prod.get('category')
                descr = descr or prod.get('description')
                productid = productid or prod.get('id')
                img_url = prod.get('imgUrl')
                name = name or prod.get('name')
                sku = sku or prod.get('sku')
                url = prod.get('url', url)
            except:
                pass
        #pprint(js)

        return {
            'sku': sku,
            'slug': slug,
            'brand': brand,
            'category': category,
            'name': name,
            'descr': descr,
            'breadcrumbs': breadcrumbs,
            'colors': colors,
            'sizes': sizes,
        }

    @classmethod
    def from_html(cls, url, html, updated=None):

        starttime = time.time()

        if 'ciSelector=' in url:
            # just a search page, ignore contents
            # e.g. http://www.ulta.com/ulta/a/Makeup-Eyes-Eye-Liner/_/N-1z13uuoZ1z13utqZ1z13utsZ1z13utoZ1z13uulZ26yh?categoryId=cat80042&ciSelector=leaf
            signals = {}
            realproducts = []
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

        soup = BeautifulSoup(html)

        # standard shit
        meta = HTMLMetadata.do_html_metadata(soup)
        sp = SchemaOrg.get_schema_product(html)
        og = OG.get_og(soup)
        metaprod = {tag['property'][8:]: tag['content']
                        for tag in soup.findAll('meta',
                                        {'property': re.compile('^product:'),
                                         'content':True})}
        custom = cls.get_custom(soup, url)
        utag = Tealium.get_utag_data(soup)

        sp = sp[0] if sp else {}

        signals = {
            'meta': meta,
            'sp':   SchemaOrg.to_json(sp),
            'og':   og,
            'metaprod': metaprod,
            'utag': utag,
            'custom': custom,
        }
        #pprint(signals)

        # TODO: tokenize and attempt to parse url itself for hints on brand and product
        # use everything at our disposal

        prodid = (og.get('product:mfr_part_no')
                    or og.get('mfr_part_no')
                    or og.get('product_id')
                    or custom.get('sku') # this one is expected for drugstore.com
                    or nth(sp.get('sku'), 0)
                    or nth(utag.get('product_id'), 0)
                    or nth(utag.get('productID'), 0)
                    or None)

        products = []

        if prodid:

            try:
                spoffer = sp['offers'][0]['properties']
            except:
                spoffer = {}

            try:
                spbrand = sp.get('brand')
                if spbrand:
                    spbrand = spbrand[0]
                    if isinstance(spbrand, basestring):
                        pass
                    elif isinstance(spbrand, dict):
                        spbrand = nth(spbrand['properties']['name'], 0)
                if isinstance(spbrand, list):
                    spbrand = u' '.join(spbrand)
            except:
                spbrand = None

            p = ProductUlta(
                id=prodid,
                url=(og.get('url')
                            or sp.get('url')
                            or url
                            or None),
                slug=custom.get('slug') or None,
                merchant_name=(og.get('product:retailer_title')
                            or og.get('retailer_title')
                            or og.get('site_name')
                            or None),
                ean=(og.get('product:ean')
                            or og.get('ean')
                            or None),
                currency=(og.get('product:price:currency')
                            or og.get('product:sale_price:currency')
                            or og.get('sale_price:currency')
                            or og.get('price:currency')
                            or og.get('currency')
                            or og.get('currency:currency')
                            or metaprod.get('price:currency')
                            or nth(utag.get('order_currency_code'), 0)
                            or nth(spoffer.get('priceCurrency'), 0)
                            or None),
                price=(og.get('product:original_price:amount')
                            or og.get('price:amount')
                            or nth(spoffer.get('price'), 0)
                            or metaprod.get('price:amount')
                            or nth(utag.get('product_price'), 0)
                            or None),
                sale_price=(og.get('product:sale_price:amount')
                            or og.get('sale_price:amount')
                            or og.get('product:price:amount')
                            or og.get('price:amount')
                            or nth(spoffer.get('price'), 0)
                            or None),
                brand=(custom.get('brand')
                            or og.get('product:brand')
                            or og.get('brand')
                            or spbrand
                            or None),
                category=custom.get('category') or None,
                breadcrumb=(custom.get('breadcrumbs')
                            or utag.get('bread_crumb')
                            or None),
                name=(og.get('title')
                            or sp.get('name')
                            or nth(utag.get('product_name'), 0)
                            or None),
                title=(og.get('title')
                            or meta.get('title')
                            or None),
                descr=(custom.get('descr')
                            or og.get('description')
                            or sp.get('description')
                            or meta.get('description')
                            or None),
                in_stock=((spoffer.get('availability') == [u'http://schema.org/InStock'])
                            or (((og.get('product:availability')
                            or og.get('availability')) in ('instock', 'in stock'))
                            or xboolstr(nth(utag.get('product_available'), 0)))
                            or None),
                stock_level=(nth(utag.get('stock_level'), 0)
                            or None),
                material=(og.get('product:material')
                            or og.get('material')
                            or None),
                features=None,
                color=(og.get('product:color')
                            or og.get('color')
                            or metaprod.get('color')
                            or nth(sp.get('color'), 0)
                            or None),
                colors=custom.get('colors'),
                sizes=None,
                img_url=(og.get('image')
                            or nth(sp.get('image'), 0)
                            or None),
                img_urls=sp.get('image'),
            )
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


def do_file(url, filepath):
    print 'filepath:', filepath
    with gzip.open(filepath) as f:
        html = f.read()
    return ProductsUlta.from_html(url, html)


if __name__ == '__main__':

    import sys

    url = 'http://www.ulta.com/ulta/browse/productDetail.jsp?productId=xlsImpprod12911001'
    filepath = 'test/www.ulta.com-ulta-browse-productDetail.jsp-productId-xlsImpprod12911001.gz'

    # test no-op
    #filepath = 'test/www.dermstore.com-product_Lipstick_31136.htm.gz'

    if len(sys.argv) > 1:
        for filepath in sys.argv[1:]:
            print do_file(url, filepath)
    else:
        print do_file(url, filepath)
