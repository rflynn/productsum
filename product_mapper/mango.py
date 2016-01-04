# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map document archived from shop.mango.com to zero or more products
ref: https://en.wikipedia.org/wiki/Mango_(clothing)

NOTE: some stuff is in espanol
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


MERCHANT_SLUG = 'mango'


class ProductMango(object):
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
            # e.g. "mango man"
            if self.brand.lower().startswith('mango '):
                self.brand = self.brand[:5]
            if self.brand.lower() == 'mango':
                self.brand = 'Mango'

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
            if self.name.endswith(" | MANGO"):
                self.name = self.name[:-len(" | MANGO")]
            if self.name.endswith("MANGO"):
                self.name = self.name[:-len("MANGO")]
            self.name = self.name.strip(" -") or None

        if self.title:
            if self.title.endswith(" | MANGO"):
                self.title = self.title[:-len(" | MANGO")]
            if self.title.endswith("MANGO"):
                self.title = self.title[:-len("MANGO")]
            self.title = self.title.strip(" -") or None

        if self.price is not None:
            try:
                self.price = normstring(self.price)
                # "$129.99$64.99" = $price$sale_price
                m = re.match(r'^(\$[0-9]+(?:\.[0-9]+)?)(\$[0-9]+(?:\.[0-9]+)?)$', self.price)
                if m:
                    #print '$price$saleprice:', m.groups(0)
                    self.price, self.sale_price = m.groups(0)
            except:
                pass

        if self.color:
            self.color = normstring(self.color)

        if self.upc:
            self.upc = str(self.upc)

    def __repr__(self):
        return ('''ProductMango:
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


class ProductsMango(object):

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

        # <input name="id_producto_hidden" id="id_producto_hidden" type="hidden" value="53043578" />
        inp = soup.find('input', type='hidden', id='id_producto_hidden', value=True)
        if inp:
            sku = sku or inp.get('value') or None

        sc = soup.find('script', text=lambda t: t and 'var dataLayerV2Json' in t)
        if sc:
            try:
                m = re.search(r'dataLayerV2Json\s*=\s*({.*})', sc.text)
                if m:
                    objtxt = m.groups(0)[0]
                    print objtxt
                    obj = json.loads(objtxt)
                    pprint(obj)
                    ec = obj.get('ecommerce') or None
                    if ec:
                        dt = ec.get('detail') or None
                        if dt:
                            av = dt.get('availability')
                            if isinstance(av, bool):
                                in_stock = av
                            sku = sku or dt.get('id') or None
                            # XXX: are these even right?
                            #brand = dt.get('brand') or None # XXX: shit
                            #name = dt.get('name') or None
                            #price = dt.get('price') or None
                            #category = dt.get('category') or None
                            #variant = dt.get('variant') or None
                        page = obj.get('page') or None
                        if page:
                            brand = brand or page.get('brand') or None
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
                        or 'J.Crew')

            p = ProductMango(
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
                name=(sp.get('name') # better than custom...
                            or custom.get('name')
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
                colors=(custom.get('colors')
                            or None),
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
    return ProductsMango.from_html(url, html)


if __name__ == '__main__':

    import sys

    url = 'http://shop.mango.com/US/p0/men/clothing/coats/faux-fur-applique-quilted-parka/?id=53099007_56&n=1&s=prendas_he.abrigos_he&ident=0__0_1451795122136&ts=1451795122136&p=1&page=1'
    filepath = 'test/shop.mango.com-US-p0-men-clothing-coats-faux-fur-applique-quilted-parka.gz'

    url = 'http://shop.mango.com/US/p0/women/sale/shoes/buckle-leather-ankle-boots/?id=53043578_99&n=1&s=rebajas_t5_she&ident=0__0_1451792240601&ts=1451792240601&p=2&page=1'
    filepath = 'test/shop.mango.com-US-p0-women-sale-shoes-buckle-leather-ankle-boots.gz'

    # test no-op
    #filepath = 'test/www.mytheresa.com-en-de-leather-wallet-468258.html.gz'

    if len(sys.argv) > 1:
        for filepath in sys.argv[1:]:
            print do_file(url, filepath)
    else:
        print do_file(url, filepath)
