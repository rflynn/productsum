# ex: set ts=4 et:
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
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
from util import nth, xstrip, dehtmlify


class ProductNordstrom(object):
    def __init__(self, id=None, url=None, slug=None, style_number=None,
                 currency=None, current_price=None, original_price=None,
                 brand=None, brandpage=None,
                 in_stock=None,
                 name=None, title=None, descr=None,
                 features=None, color=None, colors=None, sizes=None,
                 img_urls=None):

        self.id = id
        self.url = url
        self.slug = slug
        self.style_number = style_number
        self.currency = currency
        self.current_price = current_price
        self.original_price = original_price
        self.brand = brand
        self.brandpage = brandpage
        self.in_stock = in_stock
        self.name = name
        self.title = title
        self.descr = descr
        self.features = features
        self.color = color
        self.colors = colors
        self.sizes = sizes
        self.img_urls = img_urls

        # fixup
        if self.id is not None:
            self.id = str(self.id) # ensure we're a string, some signals produce numeric
        assert self.id != 'None'
        self.brand = dehtmlify(self.brand)
        self.name = dehtmlify(self.name)
        self.title = dehtmlify(self.title)
        if self.features:
            self.features = [dehtmlify(f) for f in self.features]

    def __repr__(self):
        return ('''ProductNordstrom:
    id...............%s
    url..............%s
    slug.............%s
    style_number.....%s
    currency.........%s
    current_price....%s
    original_price...%s
    brand............%s
    brandpage........%s
    in_stock.........%s
    name.............%s
    title............%s
    descr............%s
    features.........%s
    color............%s
    colors...........%s
    sizes............%s
    img_urls.........%s''' % (
       self.id,
       self.url,
       self.slug,
       self.style_number,
       self.currency,
       self.current_price,
       self.original_price,
       self.brand,
       self.brandpage,
       self.in_stock,
       self.name,
       self.title,
       self.descr,
       self.features,
       self.color,
       self.colors,
       self.sizes,
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
        elif self.sizes == [None]:
            available_sizes = []
        else:
            available_sizes = [s for s in self.sizes if s]

        return Product(
            merchant_slug='nordstrom',
            url_canonical=self.url,
            merchant_sku=self.id,
            merchant_product_obj=self,
            price=self.original_price,
            sale_price=self.current_price,
            currency=self.currency,
            brand=self.brand,
            in_stock=self.in_stock,
            stock_level=None,
            name=self.name,
            title=self.title,
            descr=self.descr,
            features=self.features,
            color=self.color,
            available_colors=available_colors,
            size=None,
            available_sizes=available_sizes,
            img_url=list(self.img_urls)[0] if self.img_urls else None,
            img_urls=sorted(self.img_urls) if self.img_urls is not None else None
        )


class ProductsNordstrom(object):

    @staticmethod
    def script_digitalData(soup):
        '''
        a simpler js obj is initialized at window.digitalData
        '''
        products = []
        try:
            script = soup.find(lambda tag: tag.name == 'script' and 'window.digitalData' in tag.text)
            if script:
                m = re.search('{.*}', script.text, re.DOTALL)
                if m:
                    objstr = m.group(0)
                    obj = json.loads(objstr)
                    # aha! if there is more than one product, then obj[product] is an array!
                    pi = obj.get(u'product')
                    if pi:
                        if isinstance(pi, dict):
                            prodlist = [pi]
                        elif isinstance(pi, list):
                            prodlist = pi
                        for px in prodlist:
                            p = px[u'productInfo']
                            #pprint(p)
                            data = {
                                'id': p[u'productID'],
                                'name': p[u'productName'],
                                'current_price': p[u'salePrice'] or p[u'basePrice'] or None,
                                'original_price': p[u'basePrice'],
                                'brand': p[u'brandName'],
                                'style_number': p[u'styleNumber'],
                                'color': p[u'color'],
                            }
                            products.append(data)
        except:
            traceback.print_exc()
        return products

    @staticmethod
    def script_ProductPageDesktop(soup):
        '''
        search for
        <script>React.render(React.createElement(ProductPageDesktop, {"initialData" ... }), document.getElementById( 'main' ));</script>
        a large, complex js object is passed to ReactJS
        '''
        data = {}
        script = soup.find(lambda tag: tag.name == 'script' and 'ProductPageDesktop' in tag.text)
        if script:
            # FIXME: too fragile; instead, parse matching { ... } after "StyleModel"...
            m = re.search('{.*}', script.text)
            #print 'script.text:', script.text.encode('utf8')
            if m:
                objstr = m.group(0)
                # XXX: son of a bitch. BeautifulSoup doesn't know
                # how to parse javascript, and when it finds js
                # with HTML-ish stuff inside it tries to parse it
                # and ends up corrupting it
                # the js contains the valid string:
                # "...<a href=\"http://...\">blah</a>"
                # with proper escapes, but BeautifulSoup corrupts it...
                objstr2 = objstr.replace('href=""', 'href=\\"\\"')
                #print 'objstr2:', objstr2.encode('utf8')
                try:
                    obj = json.loads(objstr2)
                    #pprint(obj)
                    #pprint(obj[u'initialData'][u'Model'])
                    #pprint(obj)
                    sm = obj[u'initialData'][u'Model'][u'StyleModel']
                    #pprint(sm)
                    data = {
                        'id': sm[u'Id'],
                        'name': sm[u'Name'],
                        'title': sm[u'Title'],
                        'slug': sm[u'PathAlias'],
                        'descr': sm[u'Description'],
                        'currency': sm[u'ChoiceGroups'][0][u'Price'][u'CurrencyCode'] if sm[u'ChoiceGroups'] else None,
                        'current_price': sm[u'ChoiceGroups'][0][u'Price'][u'CurrentPrice'] if sm[u'ChoiceGroups'] else None,
                        'original_price': sm[u'ChoiceGroups'][0][u'Price'][u'OriginalPrice'] if sm[u'ChoiceGroups'] else None,
                        'brand': sm[u'Brand'][u'Name'],
                        'brandpage': sm[u'Brand'][u'BrandUrl'],
                        'in_stock': sm[u'IsAvailable'],
                        # TODO: pre-order
                        'style_number': sm[u'Number'],
                        'features': sm[u'Features'],
                        'colors': list(set(x[u'Color'] for x in sm[u'Skus'])),
                        'sizes': list(set(x[u'Size'] for x in sm[u'Skus'])),
                        'img_urls': list(set(x[u'ImageMediaUri'][u'Large']
                                        for x in sm[u'StyleMedia']
                                            if x[u'ImageMediaUri'][u'Large'])),
                    }
                except:
                    traceback.print_exc()
                    
        return data

    @staticmethod
    def from_html(url, html):

        starttime = time.time()

        soup = BeautifulSoup(html)

        # standard shit
        sp = SchemaOrg.get_schema_product(html)
        og = OG.get_og(soup)
        meta = HTMLMetadata.do_html_metadata(soup)
        utag = Tealium.get_utag_data(soup)

        # custom
        ddx = ProductsNordstrom.script_digitalData(soup)
        ppd = ProductsNordstrom.script_ProductPageDesktop(soup)

        signals = {
            'sp':   SchemaOrg.to_json(sp),
            'og':   og,
            'meta': meta,
            'ddx':  ddx,
            'ppd':  ppd,
        }

        #pprint(signals)

        dd = ddx[0] if ddx else {}

        # NOTE: on the test product at least og[type] is 'website', oh well...

        products = []

        prodid = ppd.get('id') or dd.get('id') or None

        if prodid:
            p = ProductNordstrom(
                id=prodid,
                url=url or og.get('url') or None,
                slug=ppd.get('slug') or None,
                style_number=ppd.get('style_number') or dd.get('style_number') or None,
                currency=None,
                current_price=ppd.get('current_price') or dd.get('current_price') or None,
                original_price=ppd.get('original_price') or None,
                brand=ppd.get('brand') or dd.get('brand') or None,
                brandpage=ppd.get('brandpage'),
                name=dd.get('name') or ppd.get('name') or None,
                title=dd.get('name') or ppd.get('title') or meta.get('title') or None,
                descr=dehtmlify(ppd.get('descr')) or meta.get('description') or None,
                in_stock=ppd.get('in_stock'),
                features=ppd.get('features') or None,
                color=dd.get('color') or None,
                colors=ppd.get('colors') or None,
                sizes=ppd.get('sizes') or None,
                img_urls=ppd.get('img_urls') or None
            )
            products.append(p)

        realproducts = [p.to_product() for p in products]

        page = ProductMapResultPage(
                    merchant_slug='nordstrom',
                    url=url,
                    size=len(html),
                    proctime = time.time() - starttime,
                    signals=signals)

        return ProductMapResult(page=page,
                                products=realproducts)


if __name__ == '__main__':

    # test a shoe
    url = 'http://shop.nordstrom.com/s/jimmy-choo-abel-pointy-toe-pump-women/3426524'
    filepath = 'test/shop.nordstrom.com-s-jimmy-choo-abel-pointy-toe-pump-women-3426524.html.gz'

    # test 2 products on page
    url = 'http://shop.nordstrom.com/o/tracy-porter-for-poetic-wanderlust-sisley-quilt-sham/4127306?origin=category'
    filepath = 'test/shop.nordstrom.com-o-tracy-porter-for-poetic-wanderlust-sisley-quilt-sham-4127306-multiple-products.gz'

    url = 'http://shop.nordstrom.com/s/ecco-sierra-ii-sneaker-men/3957994?origin=category'
    filepath = 'test/shop.nordstrom.com-s-ecco-sierra-ii-sneaker-men-3957994-dd-empty.gz'

    # not available
    url = 'http://shop.nordstrom.com/s/giorgio-armani-formal-loafer-men/4082797'
    filepath = 'test/shop.nordstrom.com-s-giorgio-armani-formal-loafer-men-4082797-not-available.gz'

    # TODO: price failed
    url = 'http://shop.nordstrom.com/s/armani-collezioni-herringbone-silk-tie/4174895?origin=category'
    filepath = 'test/shop.nordstrom.com-s-armani-collezioni-herringbone-silk-tie-4174895-price.gz'

    # TODO: dd js parse error
    url = 'http://shop.nordstrom.com/s/ugg-australia-amie-classic-slim-water-resistant-short-boot-women/4106431?origin=category'
    filepath = 'test/shop.nordstrom.com-s-ugg-australia-amie-classic-slim-water-resistant-short-boot-women-4106431-dd-parse-error.gz'

    with gzip.open(filepath) as f:
        html = f.read()

    result = ProductsNordstrom.from_html(url, html)
    print result
