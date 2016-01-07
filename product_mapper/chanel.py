# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from chanel.com to zero or more products
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


MERCHANT_SLUG = 'chanel'


class ProductChanel(object):
    VERSION = 0
    def __init__(self, id=None, url=None, merchant_name=None, slug=None,
                 merchant_sku=None, upc=None, mpn=None, isbn=None, ean=None,
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
        self.mpn = mpn
        self.isbn = isbn
        self.ean = ean
        self.currency = currency
        self.sale_price = normstring(sale_price)
        self.price = normstring(price)
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

        # clean up "$brand $upper_name"
        if self.name:
            if self.brand:
                if self.name.upper().startswith(self.brand.upper()):
                    self.name = self.name[len(self.brand):].lstrip()
            if self.name.upper() == self.name:
                self.name = self.name.title()

        self.title = dehtmlify(normstring(self.title))
        if isinstance(self.descr, list):
            self.descr = u' '.join(self.descr) or None
        if self.title:
            if self.title.startswith('CHANEL - '):
                self.title = self.title[len('CHANEL - '):]
            if self.name:
                if self.title == self.name.upper():
                    self.title = self.name

        self.descr = dehtmlify(normstring(self.descr))

        if self.features:
            self.features = [dehtmlify(f) for f in self.features]

        if self.upc:
            self.upc = str(self.upc)

        if self.mpn:
            self.mpn = str(self.mpn)

    def __repr__(self):
        return ('''ProductChanel:
    id............... %s
    url.............. %s
    merchant_name.... %s
    merchant_sku..... %s
    slug............. %s
    upc.............. %s
    mpn.............. %s
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
       self.mpn,
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
            mpn=self.mpn,
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


class ProductsChanel(object):

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
            url_canonical = urljoin(url, soup.find('link', rel='canonical').get('href'))
        except:
            url_canonical = url

        try:
            breadcrumbs = [x for x in
                            [normstring(a.get_text()) for a in
                                soup.select('div[itemscope] span.breadcrumb a[href]')]
                                    if x] or None
        except:
            traceback.print_exc()

        if not sku:
            u = URL(url)
            if u.path:
                # http://www.ln-cc.com/en/women/jackets-2/pre-ss16%3A-lanvin-single-breasted-coat/lan0223002col.html
                m = re.search('/sku/([0-9]{4,12})$', u.path)
                if m:
                    sku = m.groups(0)[0]

        '''
<form class="stylized_form product_form">
        <input type="hidden" name="productId" value="122567" />
        <input type="hidden" name="skuId" value="122570" />
        <input type="hidden" name="skuPIMId" value="189830" />
        <input type="hidden" name="productPIMId" value="P189810" />
        <input type="hidden" name="price" value="36.00" />
        <input type="hidden" name="family" value="ILLUSION D'OMBRE" />
        <input type="hidden" name="name"  value="LONG WEAR LUMINOUS EYESHADOW"/>
        <input type="hidden" name="skuName" value="122 OCEAN LIGHT" />
        <input type="hidden" name="unitLabel" value="Shade" />
        <input type="hidden" name="item_trigger" value="http://www.chanel.com/en_US/fragrance-beauty/cms2export/Site1Files/P189810/S189830_XLARGE.jpg" />
        <input type="hidden" name="skuUrl" value="http://www.chanel.com/en_US/fragrance-beauty/Makeup-Eyeshadow-ILLUSION-D%27OMBRE-122567/sku/122570" />
        '''
        try:
            inp = {i['name']: i['value']
                        for i in soup.select('form.stylized_form input[type="hidden"]')}
            #pprint(inp)
            # TODO: there are a bunch of sku/product ids in here, figure them out...
            sku = inp.get('productId') or None
            price = price or inp.get('price') or None
            name = name or inp.get('name') or None
            if name:
                if name == name.upper():
                    name = name.title()
            family = inp.get('family') or None
        except:
            traceback.print_exc()

        '''
        '''
        try:
            dj = [x for x in
                    [json.loads(o.get('data-json') or None)
                        for o in soup.select('select[id^="Skus"] option[data-json]')]
                            if x] or None
            attrs = [x for x in
                        [d.get('seoText') or d.get('skuTitle') or None
                            for d in dj]
                                if x] or None
            #pprint(dj)
            if dj and attrs:
                unit = dj[0].get('unitOfMeasurementLabel')
                if unit == 'Size':
                    sizes = attrs
                elif unit == 'Shade':
                    colors = attrs
        except:
            traceback.print_exc()
        

        # <meta name="WT.sku_sz" content="3.4 fl. oz." />
        try:
            sz = soup.find('meta', {'name': 'WT.sku_sz', 'content': True})
            if sz:
                size = sz.get('content') or None
        except:
            traceback.print_exc()

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
            'img_urls': img_urls,
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
                    or nth(sp.get('sku'), 0)
                    or nth(sp.get('productID'), 0) # should exist in chanel
                    or custom.get('sku') # should exist in chanel
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
                        or og.get('product:brand')
                        or og.get('brand')
                        or spbrand
                        or 'Chanel')

            p = ProductChanel(
                id=prodid,
                url=(custom.get('url_canonical')
                            or og.get('url')
                            or sp.get('url')
                            or url
                            or None),
                upc=custom.get('upc') or None,
                mpn=nth(sp.get('mpn'), 0) or None,
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
                brand=brand,
                category=custom.get('category') or None,
                breadcrumb=(custom.get('breadcrumbs')
                            or utag.get('bread_crumb')
                            or None),
                name=(sp.get('name')
                            or custom.get('name')
                            or og.get('title')
                            or nth(utag.get('product_name'), 0)
                            or None),
                title=(custom.get('title')
                            or og.get('title')
                            or meta.get('title')
                            or None),
                descr=(custom.get('descr')
                            or sp.get('description') # much better than og
                            or og.get('description')
                            or meta.get('description')
                            or None),
                in_stock=((spoffer.get('availability') == [u'http://schema.org/InStock'])
                            or (((og.get('product:availability')
                            or og.get('availability')) in ('instock', 'in stock'))
                            or xboolstr(nth(utag.get('product_available'), 0)))
                            or custom.get('in_stock')
                            or None),
                stock_level=(nth(utag.get('stock_level'), 0)
                            or custom.get('stock_level')
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
    return ProductsChanel.from_html(url, html)


if __name__ == '__main__':

    import sys

    url = 'http://www.chanel.com/en_US/fragrance-beauty/Fragrance-CHANCE-EAU-VIVE-CHANCE-EAU-VIVE-139602'
    filepath = 'test/www.chanel.com-en_US-fragrance-beauty-Fragrance-CHANCE-EAU-VIVE-CHANCE-EAU-VIVE-139602-sku-139604.gz'

    url = 'http://www.chanel.com/en_US/fragrance-beauty/Fragrance-Coco-Noir-COCO-NOIR-138411'
    filepath = 'test/www.chanel.com-en_US-fragrance-beauty-Fragrance-Coco-Noir-COCO-NOIR-138411-sku-138412.gz'

    url = 'http://www.chanel.com/en_US/fragrance-beauty/Makeup-Eyeshadow-ILLUSION-D%27OMBRE-122567/sku/140226'
    filepath = 'test/www.chanel.com-en_US-fragrance-beauty-Makeup-Eyeshadow-ILLUSION-D%27OMBRE-122567-sku-140226.gz'

    # test no-op
    #url = 'http://www.shiseido.com/perfect-rouge/9990000000039,en_US,pd.html'
    #filepath = 'test/www.shiseido.com-perfect-rouge-9990000000039,en_US,pd.html.gz'

    if len(sys.argv) > 1:
        for filepath in sys.argv[1:]:
            print do_file(url, filepath)
    else:
        print do_file(url, filepath)
