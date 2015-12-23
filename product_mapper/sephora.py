# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from sephora.com to zero or more products
'''

from bs4 import BeautifulSoup
import execjs
import gzip
import json
from pprint import pprint
import re
import time
import traceback
from urlparse import urljoin

from htmlmetadata import HTMLMetadata
from og import OG
from product import Product, ProductMapResultPage, ProductMapResult
from schemaorg import SchemaOrg
from tealium import Tealium
from util import nth, normstring, dehtmlify, xboolstr, u


MERCHANT_SLUG = 'sephora'


class ProductSephora(object):
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
            if self.name.endswith(" | Bloomingdale's"):
                self.name = self.name[:-len(" | Bloomingdale's")]

        if self.title:
            if self.title.endswith(" | Bloomingdale's"):
                self.title = self.title[:-len(" | Bloomingdale's")]

        if self.upc:
            self.upc = str(self.upc)

    def __repr__(self):
        return ('''ProductSephora:
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
    size............. %s
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
       self.size,
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
        elif self.sizes == ['NO SIZE']:
            available_sizes = []
        else:
            available_sizes = [s for s in self.sizes if s]

        return Product(
            merchant_slug=MERCHANT_SLUG,
            url_canonical=self.url,
            upc=self.upc,
            merchant_sku=self.id,
            merchant_product_obj=self,
            price=self.price,
            sale_price=self.sale_price,
            currency=self.currency,
            brand=self.brand,
            category=self.category,
            bread_crumb=self.breadcrumb,
            in_stock=self.in_stock,
            stock_level=None,
            name=self.name,
            title=self.title,
            descr=self.descr,
            features=self.features,
            color=self.color,
            available_colors=available_colors,
            size=self.size,
            available_sizes=available_sizes,
            img_url=self.img_url,
            img_urls=sorted(self.img_urls) if self.img_urls is not None else None
        )


class ProductsSephora(object):

    VERSION = 0

    @staticmethod
    def get_custom(soup, url, og):

        sku = None
        productid = None
        brand = None
        category = None
        breadcrumbs = None
        name = None
        title = None
        descr = None
        features = None
        in_stock = None
        slug = None
        price = None
        sale_price = None
        color = None
        colors = None
        size = None
        sizes = None
        img_url = None
        upc = None
        upcs = None

        try:
            url_canonical = soup.find('link', rel='canonical').get('href')
        except:
            url_canonical = url

        #<body id="product" ng-app="PDP" seph-currency="$"
        tag = soup.find('body', {'seph-currency': True})
        if tag:
            if tag.get('seph-currency') == '$':
                currency = 'USD'
            else:
                print 'unknown currency %s' % (tag.get('seph-currency'),)

        # jackpot
        tag = soup.find('script', {'data-entity': 'Sephora.Sku'})
        if tag and hasattr(tag, 'text'):
            try:
                objtxt = tag.text
                #print objtxt
                #obj = execjs.eval(objtxt)
                obj = json.loads(objtxt)
                pprint(obj)
            except:
                traceback.print_exc()
                obj = {}
            sku = obj.get('sku_number') or None
            productid = obj.get('primary_product_id') or None
            price = obj.get('list_price') or None
            if price:
                price = str(price)
            sale_price = obj.get('sale_price') or None
            if sale_price:
                sale_price = str(sale_price)
            size = normstring(obj.get('sku_size')) or None
            hero = obj.get('hero_images') or None
            if hero:
                paths = hero.split(' ')
                # calculate abs path
                img_url = urljoin(url_canonical or url, paths[-1])

            p = obj.get('primary_product')
            if isinstance(p, dict):
                brand = p.get('brand_name') or None
                name = p.get('display_name') or None

        # var wa_v2
        tag = soup.find('script', text=lambda t: t and 'var wa_v2' in t)
        if tag:
            m = re.search('({.*})', tag.text)
            if m:
                try:
                    objtxt = m.groups(0)[0]
                    print objtxt
                    obj = json.loads(objtxt)
                    pprint(obj)
                except:
                    traceback.print_exc()
                    obj = {}
                breadcrumbs = obj.get('categoryPath') or None
                if breadcrumbs:
                    if isinstance(breadcrumbs, list):
                        category = breadcrumbs[-1]
                    else:
                        breadcrumbs = None
                p = obj.get('prodViewEvent')
                if p and isinstance(p, dict):
                    sku = sku or p.get('skuId') or None
                    price = price or p.get('price') or None
                    name = name or p.get('productName') or None
                    oos = p.get('notInStock')
                    if isinstance(oos, bool):
                        in_stock = not oos

        tag = soup.find('div', {'class': 'SwatchGroup'})
        if tag:
            if 'SwatchGroup--text' in tag['class']:
                # sizes
                sizes = [dehtmlify(normstring(t.get_text()))
                            for t in tag.findAll('div', {'class': 'Swatch-txt'})]
            elif 'SwatchGroup--fragrance' not in tag['class']:
                # colors...
                def da2color(da):
                    try:
                        return dehtmlify(normstring(da.split(':')[1]))
                    except:
                        pass
                colors = [c for c in
                            [da2color(t['data-analytics'])
                                for t in tag.findAll('div', {'data-analytics': True})]
                                    if c] or None

        return {
            'url_canonical': url_canonical,
            'brand': brand,
            'sku': sku,
            'upc': upc,
            'slug': slug,
            'category': category,
            'name': name,
            'in_stock': in_stock,
            'descr': descr,
            'features': features,
            'currency': currency,
            'price': price,
            'sale_price': sale_price,
            'breadcrumbs': breadcrumbs,
            'color': color,
            'colors': colors,
            'size': size,
            'sizes': sizes,
            'upcs': upcs,
        }

    @classmethod
    def from_html(cls, url, html):

        starttime = time.time()

        soup = BeautifulSoup(html)

        # standard shit
        meta = HTMLMetadata.do_html_metadata(soup)
        sp = SchemaOrg.get_schema_product(html)
        og = OG.get_og(soup)
        custom = cls.get_custom(soup, url, og)
        utag = Tealium.get_utag_data(soup)

        sp = sp[0] if sp else {}

        signals = {
            'meta': meta,
            'sp':   SchemaOrg.to_json(sp),
            'og':   og,
            'utag': utag,
            'custom': custom,
        }
        #pprint(signals)

        # TODO: tokenize and attempt to parse url itself for hints on brand and product
        # use everything at our disposal

        prodid = (og.get('product:mfr_part_no')
                    or og.get('mfr_part_no')
                    or og.get('product_id')
                    or custom.get('sku') # this one is expected for bloomingdales.com
                    or nth(sp.get('sku'), 0)
                    or nth(utag.get('product_id'), 0)
                    or nth(utag.get('productID'), 0)
                    or None)

        products = []

        if prodid and og.get('type') == 'product':

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

            p = ProductSephora(
                id=prodid,
                url=(custom.get('url_canonical')
                            or og.get('url')
                            or sp.get('url')
                            or url
                            or None),
                upc=custom.get('upc') or None,
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
                            or nth(utag.get('order_currency_code'), 0)
                            or nth(spoffer.get('priceCurrency'), 0)
                            or custom.get('currency')
                            or None),
                price=(custom.get('price')
                            or og.get('product:original_price:amount')
                            or og.get('price:amount')
                            or nth(spoffer.get('price'), 0)
                            or nth(utag.get('product_price'), 0)
                            or None),
                sale_price=(custom.get('sale_price')
                            or og.get('product:sale_price:amount')
                            or og.get('sale_price:amount')
                            or og.get('product:price:amount')
                            or og.get('price:amount')
                            or custom.get('sale_price')
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
                name=(custom.get('name')
                            or og.get('title')
                            or sp.get('name')
                            or nth(utag.get('product_name'), 0)
                            or None),
                title=(custom.get('title')
                            or og.get('title')
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
                            or custom.get('in_stock')
                            or None),
                stock_level=(nth(utag.get('stock_level'), 0)
                            or None),
                material=(og.get('product:material')
                            or og.get('material')
                            or None),
                features=custom.get('features') or None,
                color=(custom.get('color')
                            or og.get('product:color')
                            or og.get('color')
                            or nth(sp.get('color'), 0)
                            or None),
                colors=custom.get('colors'),
                size=custom.get('size') or None,
                sizes=custom.get('sizes'),
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
                    signals=signals)

        return ProductMapResult(page=page,
                                products=realproducts)


def do_file(url, filepath):
    print 'filepath:', filepath
    with gzip.open(filepath) as f:
        html = f.read()
    return ProductsSephora.from_html(url, html)


if __name__ == '__main__':

    import sys

    url = 'http://www.sephora.com/studded-kiss-lipstick-P387435?skuId=1621762'
    filepath = 'test/www.sephora.com-studded-kiss-lipstick-P387435-skuId-1621762.html.gz'

    url = 'http://www.sephora.com/triple-action-cleansing-water-P297132?skuId=1344852'
    filepath = 'test/www.sephora.com-triple-action-cleansing-water-P297132-skuId-1344852.html.gz'

    url = 'http://www.sephora.com/flowerbomb-P255506?skuId=1233139'
    filepath = 'test/www.sephora.com-flowerbomb-P255506-skuId-1233139.html.gz'

    url = 'http://www.sephora.com/fatgirlslim-tm-arm-candy-P385526?skuId=1604370'
    filepath = 'test/www.sephora.com-fatgirlslim-tm-arm-candy-P385526-skuId-1604370.html.gz'

    # test no-op
    #filepath = 'test/www.yoox.com-us-44814772VC-item.gz'

    if len(sys.argv) > 1:
        for filepath in sys.argv[1:]:
            print do_file(url, filepath)
    else:
        print do_file(url, filepath)
