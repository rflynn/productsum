# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from narscosmetics.com to zero or more products
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


MERCHANT_SLUG = 'narscosmetics'


class ProductNarsCosmetics(object):
    VERSION = 0
    def __init__(self, id=None, url=None, merchant_name=None, slug=None,
                 merchant_sku=None, upc=None, isbn=None, ean=None, asin=None,
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
        self.asin = asin
        self.currency = normstring(currency) or None
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
        self.color = normstring(color) or None
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
            if self.name.endswith(" | NARS Cosmetics"):
                self.name = self.name[:-len(" | NARS Cosmetics")]

        if self.title:
            if self.title.endswith(" | NARS Cosmetics"):
                self.title = self.title[:-len(" | NARS Cosmetics")]

        if self.upc:
            self.upc = str(self.upc)


    def __repr__(self):
        return ('''ProductNarsCosmetics:
    id............... %s
    url.............. %s
    merchant_name.... %s
    merchant_sku..... %s
    slug............. %s
    upc.............. %s
    isbn............. %s
    ean.............. %s
    asin............. %s
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
       self.asin,
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
            asin=self.asin,
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


class ProductsNarsCosmetics(object):

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
        asin = None
        upcs = None

        try:
            url_canonical = urljoin(url, soup.find('link', rel='canonical').get('href'))
        except:
            url_canonical = url

        # <ul itemprop="breadcrumb">
        br = soup.find('ul', itemprop='breadcrumb')
        if br:
            try:
                breadcrumbs = [x for x in
                                [normstring(l.get_text())
                                    for l in br.findAll('li')]
                                        if x] or None
            except:
                traceback.print_exc()

        pc = soup.find('div', id='product-content')
        if pc:
            try:
                p = pc.find('span', {'class': 'price-sales'})
                if p:
                    price = normstring(p.get_text())
            except:
                traceback.print_exc()

        '''
<select class="Color jsform-custom" id="product-color-select">

<option class="emptyswatch" value="7845092216"
data-href="http://www.narscosmetics.com/on/demandware.store/Sites-US-Site/default/Product-Variation?pid=999NACSLP0001&amp;dwvar_999NACSLP0001_color=7845092216"
data-color="713B34">
Bansar
</option>
        '''
        try:
            colors = [x for x in
                        [normstring(o.get_text())
                            for o in soup.select('select.Color option[data-color]')]
                                if x] or None
        except:
            traceback.print_exc()

        try:
            t1 = soup.find('div', id='tab1')
            print 't1:', t1
            if t1:
                p = t1.find('p')
                if p:
                    descr = normstring(p.get_text())
                u = t1.find('ul')
                if u:
                    features = [x for x in
                                    [normstring(li.get_text())
                                        for li in u.findAll('li')]
                                            if x] or None
        except:
            traceback.print_exc()

        if not sku:
            u = URL(url)
            if u.path:
                m = re.search('/([0-9]{8,14})\.html$', url_canonical)
                if m:
                    sku = m.groups(0)[0]
                    upc = sku # ref: http://www.upcindex.com/607845036371

        try:
            img_urls = [x for x in
                            [urljoin(url_canonical, img.get('src'))
                                for img in soup.select('div.product-primary-image img[src]')]
                                    if x] or None
            if img_urls:
                img_url = img_urls[0]
        except:
            traceback.print_exc()

        try:
            breadcrumbs = [x for x in
                            [normstring(li.get_text())
                                for li in soup.select('ol.breadcrumb li')]
                                    if x] or None
            if breadcrumbs:
                if breadcrumbs[0] == u'Home':
                    category = breadcrumbs[1]
        except:
            traceback.print_exc()

        return {
            'url_canonical': url_canonical,
            'brand': brand,
            'sku': sku,
            'upc': upc,
            'asin': asin,
            'slug': slug,
            'category': category,
            'name': name,
            'in_stock': in_stock,
            'stock_level': stock_level,
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
            'img_url': img_url,
            'img_urls': img_urls,
            'upcs': upcs,
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
                    or nth(sp.get('productId'), 0)
                    or nth(sp.get('productID'), 0) # this one is expected for narscosmetics.com
                    or custom.get('sku')
                    or None)

        products = []

        if prodid:

            brand = (nth(sp.get('brand'), 0)
                        or u'NARS')

            try:
                spoffer = sp['offers'][0]['properties']
            except:
                spoffer = {}

            descr = (custom.get('descr')
                        or nth(sp.get('description'), 0)
                        or og.get('description')
                        or meta.get('description')
                        or None)
            descr = dehtmlify(normstring(descr))

            p = ProductNarsCosmetics(
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
                asin=custom.get('asin') or None,
                brand=brand,
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
                category=custom.get('category') or None,
                breadcrumb=(custom.get('breadcrumbs')
                            or None),
                name=(custom.get('name')
                            or nth(sp.get('name'), 0)
                            or og.get('title')
                            or None),
                title=(custom.get('title')
                            or og.get('title')
                            or meta.get('title')
                            or None),
                descr=descr,
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
                img_urls=(sp.get('image')
                            or custom.get('img_urls')
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
    return ProductsNarsCosmetics.from_html(url, html)


if __name__ == '__main__':

    import sys

    url = 'http://www.narscosmetics.com/USA/palais-royal-satin-lip-pencil/0607845092100.html'
    filepath = 'test/www.narscosmetics.com-USA-palais-royal-satin-lip-pencil-0607845092100.html.gz'

    url = 'http://www.narscosmetics.com/USA/schiap-nail-polish/0607845036371.html'
    filepath = 'test/www.narscosmetics.com-USA-schiap-nail-polish-0607845036371.html.gz'

    # test no-op
    #filepath = 'test/www.yoox.com-us-44814772VC-item.gz'

    if len(sys.argv) > 1:
        for filepath in sys.argv[1:]:
            print do_file(url, filepath)
    else:
        print do_file(url, filepath)
