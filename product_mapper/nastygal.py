# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from nastygal.com to zero or more products
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


MERCHANT_SLUG = 'nastygal'


class ProductNastyGal(object):
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

        if self.descr and not self.features:
            # if there's an list of asterisk'ed features embedded in descr, pull em out
            '''
            descr............. Blaze past 'em. The Strut and Bolt Heels come in gunmetal vegan leather and feature lightning bolt cutouts, stud detailing throughout, front lace-up closure, and red snakeskin-print vegan leather back. *PU *Shoe Height: 9"/23cm *Heel Height: 4.75 *Imported
            '''
            m = re.findall(r'[*](\w[^*]+)', self.descr)
            if m and len(m) >= 3:
                self.features = [normstring(x) for x in m] or None
                self.descr = self.descr[:self.descr.index(m[0])-1].rstrip()

        if self.features:
            if isinstance(self.features, basestring):
                self.features = [self.features]
            self.features = [dehtmlify(f) for f in self.features]

        if self.name:
            if self.name.endswith(" | J.Crew"):
                self.name = self.name[:-len(" | J.Crew")]
            if self.name.endswith("J.Crew"):
                self.name = self.name[:-len("J.Crew")]
            self.name = self.name.strip(" -") or None

        if self.title:
            if self.title.endswith(" | J.Crew"):
                self.title = self.title[:-len(" | J.Crew")]
            if self.title.endswith("J.Crew"):
                self.title = self.title[:-len("J.Crew")]
            self.title = self.title.strip(" -") or None

        if self.price is not None:
            try:
                n = float(self.price)
                if n == 0:
                    self.price = None # some prices are fucked...
            except:
                pass

        if self.color:
            if re.match('^[0-9]+$', self.color):
                # some products have skus for color...
                self.color = None

        if self.upc:
            self.upc = str(self.upc)

    def __repr__(self):
        return ('''ProductNastyGal:
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


class ProductsNastyGal(object):

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

        '''
        <div class='product-detail-container row-fluid' data-style-id='64189' itemscope='itemscope' itemtype='http://schema.org/Product'>
        '''
        dsi = soup.find(attrs={'data-style-id': True})
        if dsi:
            try:
                sku = sku or dsi.get('data-style-id') or None
            except:
                traceback.print_exc()

        if not sku:
            '''
            <input hidden name='ProductId' value='64189'>
            '''
            inp = soup.find('input', name='ProductId', value=True)
            if inp:
                sku = inp.get('value') or None

        if not sku:
            '''
            <input name='productStyleId' type='hidden' value='64189'>
            '''
            inp = soup.find('input', name='ProductStyleId', value=True)
            if inp:
                sku = inp.get('value') or None

        if not sku:
            '''
            <div class='product-style'>Style #:64189
            '''
            ps = soup.find('div', {'class': 'product-style'})
            #print 'ps:', ps
            if ps:
                m = re.search(r'Style #:\s*(\d{3,8})', ps.text)
                if m:
                    sku = m.groups(0)[0]

        fp = soup.find('div', {'class': 'full-price'})
        if fp:
            try:
                price = normstring(fp.get_text()) or None
            except:
                traceback.print_exc()

        pb = soup.select('div#prodDtlBody p')
        if pb:
            try:
                descr = normstring(pb[0].get_text()) or None
            except:
                traceback.print_exc()

        # <div class='product-options'>
        po = soup.find('div', {'class': 'product-options'})
        #print 'po:', po
        if po:
            try:
                sizes = [x for x in
                            [normstring(l.get_text())
                                for l in po.findAll('label', {'class': 'sku-label'})]
                                    if x] or None
            except:
                traceback.print_exc()

        ul = soup.find('ul', {'class': 'breadcrumb'})
        if ul:
            try:
                breadcrumbs = [x for x in
                            [normstring(l.get_text()).strip('/ ')
                                for l in ul.findAll('li', itemtype='http://data-vocabulary.org/Breadcrumb')]
                                    if x] or None
                if breadcrumbs and len(breadcrumbs) >= 3:
                    if breadcrumbs[0] == u'Home' and breadcrumbs[1] == u'Shop All':
                        category = breadcrumbs[2]
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

            brand = (custom.get('brand')
                        or spbrand
                        or og.get('product:brand')
                        or og.get('brand')
                        or None)

            p = ProductNastyGal(
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
                price=(og.get('product:original_price:amount')
                            or og.get('price:amount')
                            or nth(sp.get('price'), 0)
                            or nth(spoffer.get('price'), 0)
                            or custom.get('price')
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
    return ProductsNastyGal.from_html(url, html)


if __name__ == '__main__':

    import sys

    url = 'http://www.nastygal.com/shoes-heels/nasty-gal-strut-and-bolt-cutout-heels'
    filepath = 'test/www.nastygal.com-shoes-heels-nasty-gal-strut-and-bolt-cutout-heels.gz'

    url = 'http://www.nastygal.com/clothes-dresses/lioness-found-love-slit-dress--navy'
    filepath = 'test/www.nastygal.com-clothes-dresses-lioness-found-love-slit-dress--navy.gz'

    # test no-op
    #filepath = 'test/www.mytheresa.com-en-de-leather-wallet-468258.html.gz'

    if len(sys.argv) > 1:
        for filepath in sys.argv[1:]:
            print do_file(url, filepath)
    else:
        print do_file(url, filepath)
