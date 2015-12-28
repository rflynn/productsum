# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from modaoperandi.com to zero or more products
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


MERCHANT_SLUG = 'modaoperandi'


class ProductModaoperandi(object):
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
        if self.title:
            if self.title.endswith(' | Moda Operandi'):
                self.title = self.title[:-len(' | Moda Operandi')]
        if isinstance(self.descr, list):
            self.descr = u' '.join(self.descr) or None
        self.descr = dehtmlify(normstring(self.descr))
        if self.features:
            self.features = [dehtmlify(f) for f in self.features]
        if self.color:
            self.color = self.color.title()

    def __repr__(self):
        return ('''ProductModaoperandi:
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
            available_colors=self.colors,
            size=self.size,
            available_sizes=self.sizes,
            img_url=self.img_url,
            img_urls=sorted(self.img_urls) if self.img_urls is not None else None
        )


class ProductsModaoperandi(object):

    VERSION = 0

    @staticmethod
    def get_custom(soup, url, og):

        sku = None
        slug = None
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
        currency = None
        price = None
        sale_price = None
        color = None
        colors = None
        size = None
        sizes = None
        img_url = None
        img_urls = None
        # moda-specific
        producttype = None
        is_preorder = None
        endsontxt = None

        try:
            canonical_url = soup.find('link', rel='canonical').get('href')
        except:
            canonical_url = url

        '''
<div class="container col-43-gutter ga-eec-product" data-brand="Oscar de la Renta" data-category="SHOES" data-id="516337" data-name="Lola Pump in Seafoam Patent Leather" data-price="770.0" data-producttype="boutique">
        '''
        tag = soup.find('div', {'data-brand': True})
        if tag:
            brand = brand or tag.get('data-brand')
            category = category or tag.get('data-category')
            sku = sku or tag.get('data-id')
            name = name or tag.get('data-name')
            price = price or tag.get('data-price')
            producttype = producttype or tag.get('data-producttype')

        tag = soup.find('span', {'class': 'product-name'})
        if tag:
            name = normstring(tag.get_text())

        js = {}
        pd = soup.find('script', text=lambda t: t and 'var pageData' in t)
        if pd:
            try:
                code = re.search('({[^;]*})', pd.text, re.DOTALL).groups(0)[0]
                #print code
                js = json.loads(code)
                obj = js['data']
                #pprint(obj)

                url = obj.get('url', url)
                sku = sku or obj.get('id')
                if sku:
                    sku = str(sku)
                productid = productid or obj.get('id')
                brand = brand or obj.get('designer_name')
                subcategory = obj.get('subcategory')
                if category and subcategory:
                    breadcrumbs = [category, subcategory]
                slug = slug or obj.get('slug')
                price = obj.get('retail_price_usd') or None
                if price:
                    currency = 'USD'
                name = name or obj.get('name')
                descr = descr or obj.get('description')
                if descr:
                    if '**' in descr:
                        descr = descr.replace('**', '') # weird highlighting of brand name...
                img_url = obj.get('imgUrl')
                imgs = obj.get('images')
                if imgs:
                    img_urls = [imgs[i]['medium'] for i in imgs['order']]
                # if the image order thing worked, use the first image
                img_url = img_urls[0]

            except:
                pass
        #pprint(js)

        di = soup.find('div', {'class': 'detail-info'})
        if di:
            features = [f for f in [normstring(li.get_text() if hasattr(li, 'get_text') else li)
                            for li in di.findAll('li')] if f]

            if features:
                c = [f for f in features if f and f.lower().startswith('color:')]
                if c:
                    # if this worked, use it, it's more accurate than the tag data
                    color = dehtmlify(normstring(c[0][6:]))

        # <select class="custom-selector cart_variant_id" data-selector=".cart_variant_id" id="sizes" name="sizes"><option data-sku="TAT-PC-OIL" price="48" selected="selected" stock="1" value="2244">5.1 oz</option></select>
        tag = soup.find('select', {'name': 'sizes'})
        if tag:
            tag = tag.find('option', selected=True)
            if tag:
                size = tag.text

        tag = soup.find('div', {'class': 'ends-on'})
        if tag:
            txt = normstring(tag.get_text())
            if txt:
                endsontxt = txt.lower()
                if 'available for preorder' in endsontxt:
                    is_preorder = True
                elif endsontxt == u'':
                    is_preorder = False

        '''
        <p class="prod-state pdp__product-info--additional-info" id="availabilityTextOriginal">
            Sold Out
        </p>
        '''
        tag = soup.find('p', id='availabilityTextOriginal')
        if tag:
            txt = normstring(tag.get_text())
            if txt:
                txt = txt.lower()
                if txt == 'sold out':
                    in_stock = False

        if in_stock is not False:
            if not is_preorder:
                in_stock = True

        return {
            'sku': sku,
            'slug': slug,
            'brand': brand,
            'category': category,
            'breadcrumbs': breadcrumbs,
            'name': name,
            'in_stock': in_stock,
            'descr': descr,
            'features': features,
            'currency': currency,
            'price': price,
            'sale_price': sale_price,
            'color': color,
            'colors': colors,
            'size': size,
            'sizes': sizes,
            'img_url': img_url,
            'img_urls': img_urls,
            'producttype': producttype,
            'is_preorder': is_preorder,
            'endsontxt': endsontxt,
        }

    @classmethod
    def from_html(cls, url, html, updated=None):

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
                    or custom.get('sku')
                    or nth(utag.get('product_id'), 0)
                    or nth(sp.get('sku'), 0)
                    or nth(utag.get('product_id'), 0)
                    or nth(utag.get('productID'), 0)
                    or None)

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
                    or utag.get('designer_name')
                    or og.get('product:brand')
                    or og.get('brand')
                    or spbrand
                    or None)

        price = (og.get('product:original_price:amount')
                    or (nth(utag.get('product_original_price'), 0) or None)
                    or og.get('price:amount')
                    or nth(spoffer.get('price'), 0)
                    or custom.get('price') # expected
                    or nth(utag.get('product_price'), 0)
                    or None)

        products = []

        # moda plays it loose with product ids; so we need to be really
        # sure we have a "real" product...

        if prodid and brand and price:

            p = ProductModaoperandi(
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
                            or nth(utag.get('order_currency_code'), 0)
                            or nth(spoffer.get('priceCurrency'), 0)
                            or custom.get('currency')
                            or None),
                price=price,
                sale_price=(og.get('product:sale_price:amount')
                            or og.get('sale_price:amount')
                            or og.get('product:price:amount')
                            or og.get('price:amount')
                            or custom.get('sale_price') # expected
                            or nth(spoffer.get('price'), 0)
                            or nth(utag.get('product_unit_price'), 0)
                            or None),
                brand=brand,
                category=custom.get('category') or None,
                breadcrumb=(custom.get('breadcrumbs')
                            or utag.get('bread_crumb')
                            or None),
                name=(custom.get('name')
                            or (nth(utag.get('product_name'), 0) or None)
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
                            or (nth(utag.get('product_color'), 0) or None)
                            or og.get('product:color')
                            or og.get('color')
                            or nth(sp.get('color'), 0)
                            or None),
                colors=custom.get('colors'),
                size=custom.get('size') or None,
                sizes=custom.get('sizes'),
                img_url=(custom.get('img_url')
                            or og.get('image')
                            or nth(sp.get('image'), 0)
                            or nth(utag.get('product_image_url'), 0)
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
    return ProductsModaoperandi.from_html(url, html)


if __name__ == '__main__':

    import sys

    # test no-op
    #tfilepath = 'test/www.yoox.com-us-44814772VC-item.gz'

    # test that a brand page is not detected as a product
    url = 'https://www.modaoperandi.com/penguin-randomhouse'
    filepath = 'test/www.modaoperandi.com-penguin-randomhouse-ensure-brand-not-seen-as-product.gz'

    # test a product
    url = 'https://www.modaoperandi.com/oscar-de-la-renta-ss16/lola-pump-in-seafoam-patent-leather'
    filepath = 'test/www.modaoperandi.com-oscar-de-la-renta-ss16-lola-pump-in-seafoam-patent-leather.gz'

    if len(sys.argv) > 1:
        for filepath in sys.argv[1:]:
            print do_file(url, filepath)
    else:
        print do_file(url, filepath)
