# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from bathandbodyworks.com to zero or more products
'''

from bs4 import BeautifulSoup
import execjs
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
from util import nth, normstring, dehtmlify, xboolstr


MERCHANT_SLUG = 'bathandbodyworks'


class ProductBathandBodyWorks(object):
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

    def __repr__(self):
        return ('''ProductBathandBodyWorks:
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


class ProductsBathandBodyWorks(object):

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

        try:
            canonical_url = soup.find('link', rel='canonical').get('href')
        except:
            canonical_url = url

        breadcrumbs = [normstring(b.get_text())
                        for b in soup.select('div#breadcrumbs li.breadcrumb')] or None

        if og.get('type') == 'product':
            # this appears on some non-product pages, so ignore those...
            tag = soup.find('input', {'name': 'prod_id',
                                      'type': 'hidden',
                                      'value': True})
            if tag and tag.get('value'):
                sku = tag['value']

        tag = soup.find('span', {'class': 'availability-status'})
        if tag:
            txt = normstring(tag.get_text())
            if txt:
                in_stock = (txt.lower() == 'in stock')

        pd = soup.find('div', id='product-detail')
        if pd:
            try:
                brand = normstring(pd.find('div', {'class': 'brand'}).get_text())
                color = normstring(pd.find('div', {'class': 'brand-color'}).get_text())
                category = normstring(pd.find('div', {'class': 'fn'}).get_text())
            except:
                pass

        tag = soup.find('title')
        if tag:
            try:
                # e.g. Vanilla Bean Noel Body Lotion   - Signature Collection - Bath & Body Works
                pieces = tag.text.split(' - ')
                if len(pieces) == 3:
                    pieces = [normstring(p) for p in pieces]
                    name_, brand_, bb = pieces
                    if bb == u'Bath & Body Works':
                        name = name_
                        brand = brand_
            except:
                pass

        try:
            descr = soup.find('div', id='product-overview').get_text()
        except:
            pass

        try:
            features = [normstring(li.text)
                            for li in soup.select('div#product-description li')] or None
        except:
            pass

        tag = soup.find('script',
                            text=lambda t: t and bool(re.search(r'\bess\.productJSON\s*=',
                                                        t, re.DOTALL)))
        if tag:
            m = re.search(r'ess\.productJSON\s*=\s*({[^;]+})', tag.text, re.DOTALL)
            if m:
                try:
                    objtxt = m.groups(0)[0]
                    obj = execjs.eval(objtxt)
                    #pprint(obj)
                    sku = obj.get('productId') or None
                    price = obj.get('basePrice') or None
                    title = obj.get('title') or None
                    sale_price = obj.get('price') or None
                    img_url = obj.get('mainImageURL') or None
                    names = [o.get('color')
                               for s, o in obj.get('skus', {}).iteritems()
                                    if o.get('color')]
                    colors = sorted(o.get('color')
                                        for s, o in obj.get('skus', {}).iteritems()
                                            if o.get('color'))
                    sizes = sorted(o.get('size')
                                        for s, o in obj.get('skus', {}).iteritems()
                                            if o.get('size'))
                    if sizes and len(sizes) == 1:
                        size = sizes[0]
                except:
                    traceback.print_exc()

        if (not color) and colors and len(colors) == 1:
            color = colors[0]

        if (not category) and breadcrumbs:
            category = breadcrumbs[-1]

        return {
            'sku': sku,
            'slug': slug,
            'brand': brand,
            'category': category,
            'name': name,
            'in_stock': in_stock,
            'descr': descr,
            'features': features,
            'price': price,
            'breadcrumbs': breadcrumbs,
            'color': color,
            'colors': colors,
            'size': size,
            'sizes': sizes,
        }

    @classmethod
    def from_html(cls, url, html, updated=None):

        starttime = time.time()

        soup = BeautifulSoup(html)

        # standard shit
        meta = HTMLMetadata.do_html_metadata(soup)
        sp = SchemaOrg.get_schema_product(html)
        og = OG.get_og(soup)
        metaprod = {tag['property'][8:]: tag['content']
                        for tag in soup.findAll('meta',
                                        {'property': re.compile('^product:'),
                                         'content':True})}
        custom = cls.get_custom(soup, url, og)

        sp = sp[0] if sp else {}

        signals = {
            'meta': meta,
            'sp':   SchemaOrg.to_json(sp),
            'og':   og,
            'metaprod': metaprod,
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

            p = ProductBathandBodyWorks(
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
                            or nth(spoffer.get('priceCurrency'), 0)
                            or None),
                price=(og.get('product:original_price:amount')
                            or og.get('price:amount')
                            or nth(spoffer.get('price'), 0)
                            or custom.get('price') # expected
                            or None),
                sale_price=(og.get('product:sale_price:amount')
                            or og.get('sale_price:amount')
                            or og.get('product:price:amount')
                            or og.get('price:amount')
                            or custom.get('sale_price') # expected
                            or nth(spoffer.get('price'), 0)
                            or None),
                brand=(custom.get('brand')
                            or og.get('product:brand')
                            or og.get('brand')
                            or spbrand
                            or None),
                category=custom.get('category') or None,
                breadcrumb=(custom.get('breadcrumbs')
                            or None),
                name=(custom.get('name')
                            or og.get('title')
                            or sp.get('name')
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
                            or custom.get('in_stock')
                            or None)),
                stock_level=(custom.get('stock_level')
                            or None),
                material=(og.get('product:material')
                            or og.get('material')
                            or None),
                features=custom.get('features') or None,
                color=(custom.get('color')
                            or og.get('product:color')
                            or og.get('color')
                            or metaprod.get('color')
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
                    signals=signals,
                    updated=updated)

        return ProductMapResult(page=page,
                                products=realproducts)


def do_file(url, filepath):
    print 'filepath:', filepath
    with gzip.open(filepath) as f:
        html = f.read()
    return ProductsBathandBodyWorks.from_html(url, html)


if __name__ == '__main__':

    import sys

    url = 'http://www.bathandbodyworks.com/product/index.jsp?productId=67258816'
    filepath = 'test/www.bathandbodyworks.com-product-index.jsp-productId-67258816.gz'

    # test no-op
    #filepath = 'test/www.yoox.com-us-44814772VC-item.gz'
    #filepath = 'www.bathandbodyworks.com-category-index.jsp-categoryId-36355536.gz'

    if len(sys.argv) > 1:
        for filepath in sys.argv[1:]:
            print do_file(url, filepath)
    else:
        print do_file(url, filepath)
