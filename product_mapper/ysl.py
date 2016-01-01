# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from ysl.com to zero or more products
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


MERCHANT_SLUG = 'ysl'


class ProductYSL(object):
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

        if self.price:
            if self.price.startswith(u'\xe2\u201a\xac '):
                # replace mangled unicode euro sign U+20AC
                self.price = u'\u20ac ' + self.price[4:]
            self.price = normstring(self.price).replace(' ', '')

        if self.sale_price:
            if self.sale_price.startswith(u'\xe2\u201a\xac '):
                # replace mangled unicode euro sign U+20AC
                self.sale_price = u'\u20ac ' + self.sale_price[4:]
            self.sale_price = normstring(self.sale_price).replace(' ', '')

        if isinstance(self.brand, list):
            self.brand = u' '.join(self.brand) or None
        self.brand = dehtmlify(normstring(self.brand))

        if self.brand:
            if self.brand.startswith('/b/'):
                # e.g. "/b/inglot-cosmetics"
                self.brand = normstring(self.brand[3:].replace('-', ' ')) or None
                if self.brand:
                    self.brand = self.brand.title()

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
            if self.name.endswith(" | YSL.COM"):
                self.name = self.name[:-len(" | YSL.COM")]
            self.name = self.name or None

        if self.title:
            if self.title.endswith(" | YSL.COM"):
                self.title = self.title[:-len(" | YSL.COM")]

        if self.upc:
            self.upc = str(self.upc)

    def __repr__(self):
        return ('''ProductYSL:
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


class ProductsYSL(object):

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
            canonical = soup.find('link', rel='canonical').get('href')
            if canonical:
                url_canonical = urljoin(url, canonical)
        except:
            url_canonical = url

        if not sku:
            # "Cod10":"44670189gt"
            m = re.search(r'"Cod10":"(\w{8,16})"', str(soup))
            print 'm:', m.groups()
            if m:
                sku = m.groups(0)[0]

        # XXX: colors done in javascript
        #sc = soup.find('div', {'class': 'selectColor'})

        #<div id="itemDetails">
        itemd = soup.find('div', id='itemDetails')
        if itemd:
            ed = itemd.find(attrs={'class': 'editorialDescription'})
            if ed:
                try:
                    descr = normstring(ed.get_text())
                except:
                    traceback.print_exc()
            la = itemd.find('div', {'class': 'localizedAttributes'})
            if la:
                try:
                    features = []
                    for d in la.findAll('div'):
                        k = d.find('span', {'class': 'text'}) or \
                             d.find('span', {'class': 'attributesTitle'})
                        v = d.find('span', {'class': 'value'})
                        print 'k:', k
                        print 'v:', v
                        if k and v:
                            k = normstring(k.get_text())
                            v = normstring(v.get_text())
                            features.append(k + ': ' + v)
                    features = features or None
                    if not features:
                        try:
                            features = normstring(la.get_text()) or None
                        except:
                            traceback.print_exc()
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
                    or custom.get('sku')
                    or None)

        products = []

        if prodid:

            try:
                spoffer = sp['offerDetails'][0]['properties'] # XXX: non-standard
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
                        or 'Saint Laurent')

            p = ProductYSL(
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
                            or og.get('product:original_price:amount')
                            or og.get('price:amount')
                            or nth(spoffer.get('price'), 0)
                            or None),
                sale_price=(custom.get('sale_price')
                            or og.get('product:sale_price:amount')
                            or og.get('sale_price:amount')
                            or og.get('product:price:amount')
                            or og.get('price:amount')
                            or custom.get('sale_price')
                            or nth(spoffer.get('price'), 0)
                            or None),
                brand=brand,
                category=custom.get('category') or None,
                breadcrumb=(custom.get('breadcrumbs')
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
    return ProductsYSL.from_html(url, html)


if __name__ == '__main__':

    import sys

    url = 'http://www.ysl.com/us/shop-product/women/handbags-monogram-college-classic-large-monogram-saint-laurent-shopping-bag-in-black-matelasse-leather_cod45267132kh.html#section=women_bags'
    filepath = 'test/www.ysl.com-us-shop-product-women-handbags-monogram-college-classic-large-monogram-saint-laurent-shopping-bag-in-black-matelasse-leather_cod45267132kh.html.gz'

    url = 'http://www.ysl.com/us/shop-product/women/shoes-janis-pumps-classic-janis-105-escarpin-pump-in-black-textured-leather_cod44670189gt.html'
    filepath = 'test/www.ysl.com-us-shop-product-women-shoes-janis-pumps-classic-janis-105-escarpin-pump-in-black-textured-leather_cod44670189gt.html.gz'

    # test no-op
    #filepath = 'test/www.yoox.com-us-44814772VC-item.gz'

    if len(sys.argv) > 1:
        for filepath in sys.argv[1:]:
            print do_file(url, filepath)
    else:
        print do_file(url, filepath)
