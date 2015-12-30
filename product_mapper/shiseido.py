# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from shiseido.com to zero or more products
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


MERCHANT_SLUG = 'shiseido'


class ProductShiseido(object):
    VERSION = 0
    def __init__(self, id=None, url=None, merchant_name=None, slug=None,
                 merchant_sku=None, upc=None, ean=None,
                 isbn=None, isbn13=None, isbn10=None,
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
        self.isbn13 = isbn13
        self.isbn10 = isbn10
        self.ean = ean
        self.currency = currency
        self.sale_price = normstring(sale_price)
        self.price = normstring(price)
        self.brand = normstring(brand)
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
            if self.name.endswith(" - Shiseido.com"):
                self.name = self.name[:-len(" - Shiseido.com")]

        if self.title:
            if self.title.endswith(" - Shiseido.com"):
                self.title = self.title[:-len(" - Shiseido.com")]

        if self.upc:
            self.upc = str(self.upc)

        if self.descr:
            if (not self.isbn) and 'ISBN' in self.descr:
                # e.g. Hardcover, Simon & Schuster, 2015, ISBN13 9781501115943, ISBN10 1501115944'
                if not self.isbn13:
                    m = re.search('ISBN13 ([0-9]{13})', self.descr)
                    if m:
                        isbn13 = m.groups(0)[0]
                        self.isbn = isbn13
                        self.isbn13 = isbn13
                if not self.isbn10:
                    m = re.search('ISBN10 ([0-9]{10})', self.descr)
                    if m:
                        isbn10 = m.groups(0)[0]
                        if not self.isbn:
                            self.isbn = isbn10
                        self.isbn10 = isbn10

    def __repr__(self):
        return ('''ProductShiseido:
    id............... %s
    url.............. %s
    merchant_name.... %s
    merchant_sku..... %s
    slug............. %s
    upc.............. %s
    isbn............. %s
    isbn13........... %s
    isbn10........... %s
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
       self.isbn13,
       self.isbn10,
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
            isbn=self.isbn,
            isbn13=self.isbn13,
            isbn10=self.isbn10,
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


class ProductsShiseido(object):

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
        upc = None
        upcs = None

        try:
            url_canonical = soup.find('link', rel='canonical').get('href')
        except:
            url_canonical = url

        '''
        <script type="text/javascript">
            ...
            window.universal_variable.product = {
        '''
        tag = soup.find('script', text=lambda t: t and 'window.universal_variable.product = {' in t)
        if tag:
            try:
                m = re.search('window.universal_variable.product = ({.*});', tag.text)
                if m:
                    objtxt = m.groups(0)[0].strip()
                    #print objtxt
                    obj = json.loads(objtxt)
                    #obj = execjs.eval(objtxt)
                    #pprint(obj)
                    sku = obj.get('sku_code') or None
                    name = obj.get('name') or None
                    url_canonical = url_canonical or obj.get('url') or url
                    currency = obj.get('currency') or None
                    price = obj.get('unit_price') or None
                    if price:
                        price = str(price)
                    sale_price = obj.get('unit_sale_price') or None
                    if sale_price:
                        sale_price = str(sale_price)
                    stock_level = obj.get('stock') # sweet!
                    if not isinstance(stock_level, (int, long)):
                        stock_level = None
                    if stock_level is not None:
                        in_stock = stock_level > 0
                    category = obj.get('category') or None
                    if category and category == 'Shiseido':
                        brand = 'Shiseido'
            except:
                traceback.print_exc()

        # descr and features
        tag = soup.find('div', {'class': 'longDescr'})
        if tag:
            try:
                # contains descr and maybe list of features
                flist = tag.find('ul')
                if flist:
                    flist.extract()
                    features = [x for x in
                                    [normstring(li.get_text())
                                        for li in flist.findAll('li')]
                                            if x] or None
                descr = normstring(tag.get_text())
            except:
                traceback.print_exc()

        # breadcrumbs
        tag = soup.find('div', id='breadcrumb')
        if tag:
            try:
                breadcrumbs = [x for x in
                                    [normstring(a.text)
                                        for a in tag.findAll('a')]
                                            if x] or None
                if breadcrumbs:
                    category = breadcrumbs[1]
            except Exception as e:
                print e

        # div class="sizeVariations
        tag = soup.find('div', {'class': 'sizeVariations'})
        if tag:
            # <div class="variationSize">50ml/1.9oz</div>
            vs = tag.find('div', {'class': 'variationSize'})
            if vs:
                try:
                    size = normstring(vs.get_text())
                except Exception as e:
                    print e
            else:
                svsize = tag.findAll('div', {'class': 'svSize'})
                if svsize and len(svsize) == 2:
                    vs = svsize[1]
                    try:
                        size = normstring(vs.get_text()) or None
                        if size:
                            # ensure it's vaguely possible a size
                            if len(size) < 3 or len(size) > 30:
                                size = None
                    except Exception as e:
                        print e

        # colors
        # select class="colorVariationSelect
        tag = soup.find('select', {'class': 'colorVariationSelect'})
        if tag:
            try:
                colors = [x for x in
                            [normstring(a.text)
                                for a in tag.findAll('option')]
                                    if x] or None
            except:
                pass


        return {
            'url_canonical': url_canonical,
            'brand': brand,
            'sku': sku,
            'upc': upc,
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
        }

    @classmethod
    def from_html(cls, url, html, updated=None):

        starttime = time.time()

        if False:
            # nuthin'
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
                    or nth(sp.get('sku'), 0) # should exist in shiseido
                    or custom.get('sku') # should exist in shiseido
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

            p = ProductShiseido(
                id=prodid,
                url=(custom.get('url_canonical')
                            or og.get('url')
                            or sp.get('url')
                            or url
                            or None),
                upc=(custom.get('upc')
                            or og.get('upc')
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
                            or sp.get('name')
                            or og.get('title')
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
                            or custom.get('in_stock')),
                stock_level=(nth(utag.get('stock_level'), 0)
                            or custom.get('stock_level')),
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
    return ProductsShiseido.from_html(url, html)


if __name__ == '__main__':

    import sys

    url = 'http://www.shiseido.com/urban-environment-uv-protection-cream-spf-40/0730852105140,en_US,pd.html'
    filepath = 'test/www.shiseido.com-urban-environment-uv-protection-cream-spf-40-0730852105140,en_US,pd.html.gz'

    url = 'http://www.shiseido.com/perfect-rouge/9990000000039,en_US,pd.html'
    filepath = 'test/www.shiseido.com-perfect-rouge-9990000000039,en_US,pd.html.gz'

    # test no-op
    #filepath = 'test/www.yoox.com-us-44814772VC-item.gz'

    if len(sys.argv) > 1:
        for filepath in sys.argv[1:]:
            print do_file(url, filepath)
    else:
        print do_file(url, filepath)
