# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from jimmychoo.com to zero or more products
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
from yurl import URL

from htmlmetadata import HTMLMetadata
from og import OG
from product import Product, ProductMapResultPage, ProductMapResult
from schemaorg import SchemaOrg
from tealium import Tealium
from util import nth, normstring, dehtmlify, xboolstr, u


MERCHANT_SLUG = 'jimmychoo'


class ProductJimmyChoo(object):
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
        self.price = u(price)
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

        if self.id:
            if self.id.lower().startswith('sku: #'):
                self.id = self.id[6:]

        if isinstance(self.brand, list):
            self.brand = u' '.join(self.brand) or None
        self.brand = dehtmlify(normstring(self.brand))

        if self.brand:
            # e.g. "/hush-puppies"
            if self.brand.startswith('/'):
                self.brand = self.brand[1:].replace('-', ' ').title()

        if isinstance(self.name, list):
            self.name = u' '.join(self.name) or None
        self.name = dehtmlify(normstring(self.name)) or None
        self.title = dehtmlify(normstring(self.title))
        if isinstance(self.descr, list):
            self.descr = u' '.join(self.descr) or None
        self.descr = dehtmlify(normstring(self.descr))
        if self.features:
            if isinstance(self.features, basestring):
                self.features = [self.features]
            self.features = [dehtmlify(f) for f in self.features]

        if self.name:
            if self.name.endswith(" | JIMMY CHOO"):
                self.name = self.name[:-len(" | JIMMY CHOO")]
            self.name = self.name or None

        if self.title:
            if self.title.endswith(" | JIMMY CHOO"):
                self.title = self.title[:-len(" | JIMMY CHOO")]

        if self.upc:
            self.upc = str(self.upc)

    def __repr__(self):
        return ('''ProductJimmyChoo:
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
            stock_level=self.stock_level,
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


class ProductsJimmyChoo(object):

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
        stock_level = None
        slug = None
        currency = None
        price = None
        sale_price = None
        color = None
        colors = None
        size = None
        sizes = None
        img_url = None
        img_urls = None
        upc = None
        upcs = None

        try:
            canonical = soup.find('link', rel='canonical').get('href')
            if canonical:
                url_canonical = urljoin(url, canonical)
        except:
            url_canonical = url

        obj = {}

        # window.universal_variable.product
        s = soup.find('script', text=lambda t: t and 'window.universal_variable.product' in t)
        #print 's:', s
        if s:
            try:
                m = re.search(r'window\.universal_variable\.product\s*=\s*({.*})', s.text)
                #print 'm:', m
                if m:
                    objtxt = m.groups(0)[0]
                    #print objtxt
                    obj = json.loads(objtxt)
                    #pprint(obj)
            except:
                traceback.print_exc()

        # universal_variable.listing.items.push(
        s = soup.find('script', text=lambda t: t and 'universal_variable.listing.items.push(' in t)
        #print 's:', s
        if s:
            try:
                m = re.search(r'universal_variable.listing.items.push\(({.*})', s.text)
                #print 'm:', m
                if m:
                    objtxt = m.groups(0)[0]
                    #print objtxt
                    obj = json.loads(objtxt)
                    #pprint(obj)
            except:
                traceback.print_exc()

        if obj:
            #pprint(obj)
            try:
                sku = obj.get('id') or None
                name = obj.get('name') or None
                descr = obj.get('description') or None
                price = obj.get('unit_price') or None
                if price:
                    price = str(price)
                sale_price = obj.get('unit_sale_price') or None
                if sale_price:
                    sale_price = str(sale_price)
                currency = obj.get('currency') or None
                brand = obj.get('manufacturer') or None
                img_url = obj.get('image_url') or None
                if obj.get('category_hierarchy'):
                    breadcrumbs = [normstring(x) for x in
                                    obj['category_hierarchy'].split('>')] or None
                if breadcrumbs:
                    category = breadcrumbs[-1]
                else:
                    category = obj.get('subcategory') or obj.get('category') or None
                attr = obj.get('attributes')
                if attr and isinstance(attr, dict):
                    if attr.get('availability'):
                        in_stock = attr['availability'].upper() == 'IN_STOCK'
                    va = attr.get('variations_availability')
                    if va and isinstance(va, dict):
                        stock_level = (va.get('variants_instock')
                                        or va.get('variants_available')
                                        or va.get('variantsavailable') or None)
                        if not isinstance(stock_level, (type(None), int)):
                            stock_level = None
                        ava = va.get('arr_variants_available') or []
                        avu = va.get('arr_variants_unavailable') or []
                        if isinstance(ava, list) and isinstance(avu, list):
                            colors = []
                            sizes = []
                            for x in ava + avu:
                                m = re.search('^(.*)/([^/]+)$', x)
                                if m:
                                    colors.append(m.groups(0)[0])
                                    sizes.append(m.groups(0)[1])
                            colors = sorted(set(colors)) or None
                            sizes = sorted(set(sizes)) or None
            except:
                traceback.print_exc()

        return {
            'url_canonical': url_canonical,
            'brand': brand,
            'sku': sku,
            'upc': upc,
            'upcs': upcs,
            'slug': slug,
            'category': category,
            'name': name,
            'descr': descr,
            'in_stock': in_stock,
            'stock_level': stock_level,
            'features': features,
            'currency': currency,
            'price': price,
            'sale_price': sale_price,
            'breadcrumbs': breadcrumbs,
            'color': color,
            'colors': colors,
            'size': size,
            'sizes': sizes,
            'img_url': img_url,
            'img_urls': img_urls,
        }

    @classmethod
    def from_html(cls, url, html, updated=None):

        starttime = time.time()

        if False:
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

        soup = BeautifulSoup(html)

        # standard shit
        meta = HTMLMetadata.do_html_metadata(soup)
        sp = SchemaOrg.get_schema_product(html)
        og = OG.get_og(soup)
        custom = cls.get_custom(soup, url, og)

        sp = sp[0] if sp else {}

        signals = {
            'meta': meta,
            'sp':   SchemaOrg.to_json(sp),
            'og':   og,
            'custom': custom,
        }
        #pprint(signals)

        prodid = (og.get('product:mfr_part_no')
                    or og.get('mfr_part_no')
                    or og.get('product_id')
                    or nth(sp.get('sku'), 0)
                    or nth(sp.get('productId'), 0)
                    or nth(sp.get('productID'), 0)
                    or custom.get('sku')
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

            brand = (custom.get('brand')
                        or spbrand
                        or og.get('product:brand')
                        or og.get('brand')
                        or None)

            breadcrumbs = None
            try:
                breadcrumbs = sp['breadcrumb'][0]['properties']['title']
                if not isinstance(breadcrumbs, list):
                    breadcrumbs = None
            except:
                breadcrumbs = None

            p = ProductJimmyChoo(
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
                            or nth(spoffer.get('priceCurrency'), 0)
                            or custom.get('currency')
                            or None),
                price=(custom.get('price')
                            or nth(sp.get('price'), 0)
                            or nth(spoffer.get('price'), 0)
                            or og.get('product:original_price:amount')
                            or og.get('price:amount')
                            or None),
                sale_price=(custom.get('sale_price')
                            or nth(spoffer.get('price'), 0)
                            or og.get('product:sale_price:amount')
                            or og.get('sale_price:amount')
                            or og.get('product:price:amount')
                            or og.get('price:amount')
                            or None),
                brand=brand,
                category=custom.get('category') or None,
                breadcrumb=(breadcrumbs
                            or custom.get('breadcrumbs')
                            or None),
                name=(custom.get('name')
                            or sp.get('name')
                            or og.get('title')
                            or meta.get('title')
                            or None),
                title=(custom.get('title')
                            or og.get('title')
                            or meta.get('title')
                            or None),
                descr=(custom.get('descr')
                            or nth(sp.get('description'), 0)
                            or nth(spoffer.get('description'), 0)
                            or og.get('description')
                            or meta.get('description')
                            or None),
                in_stock=((spoffer.get('availability') == [u'http://schema.org/InStock'])
                            or (((og.get('product:availability')
                            or og.get('availability')) in ('instock', 'in stock')))
                            or custom.get('in_stock')
                            or None),
                stock_level=(custom.get('stock_level')
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
                            or custom.get('img_url')
                            or None),
                img_urls=(custom.get('img_urls')
                            or sp.get('image')
                            or None),
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
    return ProductsJimmyChoo.from_html(url, html)


if __name__ == '__main__':

    import sys

    url = 'http://us.jimmychoo.com/en/women/shoes/pumps/lorelai-100/anthracite-fine-glitter-fabric-pumps-with-pecan-leather-flower-mix-embellishment--LORELAI100FGW0C0957.html?cgid=women-shoes-pumps#start=1'
    filepath = 'test/us.jimmychoo.com-en-women-shoes-pumps-lorelai-100-anthracite-fine-glitter-fabric-pumps-with-pecan-leather-flower-mix-embellishment--LORELAI100FGW0C0957.html.gz'

    url = 'http://us.jimmychoo.com/en/men/bags-and-accessories/sunglasses/'
    filepath = 'test/us.jimmychoo.com-en-men-bags-and-accessories-sunglasses.gz'

    url = 'http://us.jimmychoo.com/en/women/bags/shoulder-bags/lockett-petite/black-and-chrome-spazzolato-leather-shoulder-bag-LOCKETTPETITESBK012573.html?cgid=women-handbags-shoulder#start=1'
    filepath = 'test/us.jimmychoo.com-en-women-bags-shoulder-bags-lockett-petite-black-and-chrome-spazzolato-leather-shoulder-bag-LOCKETTPETITESBK012573.html.gz'

    # test no-op
    #filepath = 'test/www.mytheresa.com-en-de-leather-wallet-468258.html.gz'

    if len(sys.argv) > 1:
        for filepath in sys.argv[1:]:
            print do_file(url, filepath)
    else:
        print do_file(url, filepath)
