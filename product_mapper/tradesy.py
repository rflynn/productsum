# ex: set ts=4 et:
# -*- coding: utf-8 *-*

'''
map a document archived from tradesy.com to zero or more products
'''

from bs4 import BeautifulSoup
import execjs
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
from util import nth, normstring, xboolstr, u


class ProductTradesy(object):
    def __init__(self,
                 prodid=None,
                 canonical_url=None,
                 brand=None,
                 instock=None,
                 stocklevel=None,
                 price=None,
                 sale_price=None,
                 currency=None,
                 name=None,
                 title=None,
                 descr=None,
                 features=None,
                 color=None,
                 colors=None,
                 size=None,
                 sizes=None,
                 img_url=None,
                 img_urls=None,
                 category=None,
                 category_id=None,
                 department=None):

        assert isinstance(prodid, basestring)

        self.prodid = prodid
        self.canonical_url = canonical_url
        self.brand = brand
        self.instock = instock
        self.stocklevel = stocklevel
        self.price = price
        self.sale_price = sale_price
        self.currency = currency
        self.name = normstring(name)
        self.title = normstring(title)
        self.descr = normstring(descr)
        self.features = features
        self.color = color
        self.colors = colors
        self.size = size
        self.sizes = sizes
        self.img_url = img_url
        self.img_urls = img_urls
        self.category = category
        self.category_id = category_id
        self.department = department

        if self.title and self.title.endswith(' | SHOPBOP'):
            self.title = self.title[:-11]

    def __repr__(self):
        return '''ProductTradesy:
    prodid...........%s
    url..............%s
    brand............%s
    instock..........%s
    stocklevel.......%s
    price............%s
    sale_price.......%s
    currency.........%s
    name.............%s
    title............%s
    descr............%s
    features.........%s
    color............%s
    colors...........%s
    size.............%s
    sizes............%s
    img_url..........%s
    img_urls.........%s
    category.........%s
    category_id......%s
    department.......%s
''' % (self.prodid,
       self.canonical_url,
       self.brand,
       self.instock,
       self.stocklevel,
       self.price,
       self.sale_price,
       self.currency,
       self.name,
       self.title,
       self.descr,
       self.features,
       self.color,
       self.colors,
       self.size,
       self.sizes,
       self.img_url,
       self.img_urls,
       self.category,
       self.category_id,
       self.department)

    def to_product(self):
        return Product(
            merchant_slug='tradesy',
            url_canonical=self.canonical_url,
            merchant_sku=self.prodid,
            merchant_product_obj=self,
            price=self.price,
            sale_price=self.sale_price,
            currency=self.currency,
            category=self.category,
            brand=self.brand,
            in_stock=self.instock,
            stock_level=self.stocklevel,
            name=self.name,
            title=self.title,
            descr=self.descr,
            features=self.features,
            color=self.color,
            available_colors=self.colors,
            size=self.size,
            available_sizes=self.sizes,
            img_url=self.img_url,
            img_urls=self.img_urls
        )


def get_custom(soup):

    product = {}

    prodid = None
    brand = None
    name = None
    in_stock = None
    price = None
    currency = None
    size = None
    sizes = None
    color = None
    colors = None
    img_url = None
    img_urls = None

    '''
    <div class="content clearfix" itemscope itemtype="http://schema.org/Product">

    <meta itemprop="name" content="Patent Leather Pigalle Pointed-toe Pink Pumps"/>
    <meta itemprop="sku" content="5407615"/>
    <meta itemprop="brand" content="Christian Louboutin"/>
    <meta itemprop="color" content="Pink"/>

    <div itemprop="offers" itemscope itemtype="http://schema.org/Offer" style="visibility: hidden">
        <meta itemprop="price" content="698"/>
        <meta itemprop="priceCurrency" content="USD"/>
        <meta itemprop="itemCondition" content="Gently used"/>
        <meta itemprop="availability" content="http://schema.org/InStock"/>
    </div>
    '''

    product = {
        #'prodid': prodid,
        #'brand': brand,
        #'name': name,
        #'in_stock': in_stock,
        #'price': price,
        #'currency': currency,
        #'size': size,
        #'sizes': sizes,
        #'color': color,
        #'colors': colors,
        #'img_url': img_url,
        #'img_urls': img_urls,
    }
    #pprint(product)
    return product


class ProductsTradesy(object):

    @staticmethod
    def from_html(url, html):

        starttime = time.time()

        products = []

        soup = BeautifulSoup(html)
        meta = HTMLMetadata.do_html_metadata(soup)
        sp = SchemaOrg.get_schema_product(html)
        og = OG.get_og(soup)
        custom = get_custom(soup)

        sp = sp[0] if sp else {}

        signals = {
            'meta':meta,
            'sp':  SchemaOrg.to_json(sp),
            'og':  og,
            'custom': custom,
        }
        #pprint(signals)

        prodid = custom.get('prodid') or nth(sp.get('sku'), 0) or None

        # is there one or more product on the page?
        if prodid:
            p = ProductTradesy(
                prodid=prodid,
                canonical_url=url,
                brand=u(nth(sp.get('brand'), 0) or custom.get('brand')) or None,
                instock=(custom.get('in_stock')
                            or og.get('availability') == u'instock' or None),
                stocklevel=custom.get('stock_level'),
                name=u(nth(sp.get(u'name'), 0)
                        or custom.get('name')
                        or og.get('title')
                        or meta.get('title') or None),
                title=u(og.get('title')
                        or meta.get('title')
                        or None),
                descr=u(nth(sp.get(u'description'), 0)
                        or og.get('description')
                        or meta.get('description') or None),
                sale_price=custom.get('sale_price') or None,
                price=u(custom.get('price')
                       or og.get('price:amount') or None),
                currency=custom.get('currency') or og.get('price:currency') or None,
                size=custom.get('size') or None,
                sizes=custom.get('sizes') or None,
                color=u(nth(sp.get('color'), 0) or custom.get('color')) or None,
                colors=custom.get('colors') or None,
                img_url=u(custom.get('img_url')
                            or og.get('image')
                            or nth(sp.get('image'), 0) or None),
                img_urls=custom.get('img_urls') or None,
            )
            products.append(p)

        realproducts = [p.to_product() for p in products]

        page = ProductMapResultPage(
                    merchant_slug='tradesy',
                    url=url,
                    size=len(html),
                    proctime = time.time() - starttime,
                    signals=signals)

        return ProductMapResult(page=page,
                                products=realproducts)


if __name__ == '__main__':

    import gzip

    url = 'https://www.tradesy.com/shoes/christian-louboutin-neon-patent-pink-pumps-5407615/'
    filepath = 'test/www.tradesy.com-shoes-christian-louboutin-neon-patent-pink-pumps-5407615.gz'

    # test no-op
    #filepath = 'test/www.dermstore.com-product_Lipstick_31136.htm.gz'

    with gzip.open(filepath) as f:
        html = unicode(f.read(), 'utf8')

    products = ProductsTradesy.from_html(url, html)
    print products
