# ex: set ts=4 et:

'''
map a document archived from barneys.com to zero or more products
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
from util import nth, normstring, xboolstr


class ProductBarneys(object):

    VERSION = 0

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
        return '''ProductBarneys:
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
            merchant_slug='barneys',
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
    sizes = None
    color = None
    img_url = None
    img_urls = None

    '''
    <meta property="product:brand" content="Sergio Rossi" />
    <meta property="product:retailer_part_no" content="504296100" />
    <meta property="product:price:amount" content="995.00" />
    <meta property="product:price:currency" content="USD" />
    <meta property="product:availability" content="instock" />
    <meta property="product:color" content="null" />
    '''
    mp = {t['property'][8:]: t['content'] for t in
            soup.findAll('meta', content=True,
                            property=re.compile('^product:'))}
    #pprint(mp)
    prodid = mp.get('retailer_part_no') or None
    brand = mp.get('brand') or None
    price = mp.get('price:amount')
    currency = mp.get('price:currency')
    if 'availability' in mp:
        in_stock = mp['availability'].lower() in ('instock', 'in stock')
    if 'color' in mp:
        if mp['color'] and mp['color'].lower() != 'null':
            color = mp['color']

    product = {
        'prodid': prodid,
        'brand': brand,
        'name': name,
        'in_stock': in_stock,
        'price': price,
        'currency': currency,
        'sizes': sizes,
        'color': color,
        'img_url': img_url,
        'img_urls': img_urls,
    }
    #pprint(product)
    return product


class ProductsBarneys(object):

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

        prodid = custom.get('prodid') or None

        # is there one or more product on the page?
        if prodid:

            p = ProductBarneys(
                prodid=prodid,
                canonical_url=url,
                brand=custom.get('brand') or None,
                instock=(custom.get('in_stock')
                            or og.get('availability') == u'instock'),
                stocklevel=custom.get('stock_level'),
                name=(nth(sp.get(u'name'), 0)
                        or custom.get('name')
                        or og.get('title')
                        or meta.get('title') or None),
                title=(og.get('title')
                        or meta.get('title')
                        or None),
                descr=(nth(sp.get(u'description'), 0)
                        or og.get('description')
                        or meta.get('description') or None),
                sale_price=custom.get('sale_price') or None,
                price=(custom.get('price')
                       or og.get('price:amount') or None),
                currency=custom.get('currency') or og.get('price:currency') or None,
                size=custom.get('size') or None,
                sizes=custom.get('sizes') or None,
                color=custom.get('color') or None,
                colors=custom.get('colors') or None,
                img_url=custom.get('img_url') or og.get('image') or None,
                img_urls=custom.get('img_urls') or None,
                category=custom.get('category') or None,
                category_id=custom.get('category_id') or None,
                department=custom.get('department') or None
            )
            products.append(p)

        realproducts = [p.to_product() for p in products]

        page = ProductMapResultPage(
                    merchant_slug='barneys',
                    url=url,
                    size=len(html),
                    proctime = time.time() - starttime,
                    signals=signals)

        return ProductMapResult(page=page,
                                products=realproducts)


if __name__ == '__main__':

    import gzip

    url = 'https://www.shopbop.com/tresor-pump-sergio-rossi/vp/v=1/1576638246.htm'
    filepath = 'test/www.barneys.com_adidas-stan-smith-pony-hair-sneakers-504163267.html.gz'

    url = 'http://www.barneys.com/sergio-rossi-puzzle-back-zip-sandals-504296100.html'
    filepath = 'test/www.barneys.com-sergio-rossi-puzzle-back-zip-sandals-504296100.html.gz'

    with gzip.open(filepath) as f:
        html = f.read()

    products = ProductsBarneys.from_html(url, html)
    print products
