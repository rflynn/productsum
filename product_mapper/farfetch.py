# ex: set ts=4 et:

'''
map a document archived from farfetch.com to zero or more products
'''

from bs4 import BeautifulSoup
import json
from pprint import pprint
import re
import time

from htmlmetadata import HTMLMetadata
from og import OG
from product import Product, ProductMapResultPage, ProductMapResult
from schemaorg import SchemaOrg
from tealium import Tealium
from util import nth, xstrip


class ProductFarfetch(object):
    VERSION = 0
    def __init__(self,
                 id=None,
                 canonical_url=None,
                 sku=None,
                 brand=None,
                 instock=None,
                 stocklevel=None,
                 name=None,
                 title=None,
                 descr=None,
                 price=None,
                 sale_price=None,
                 currency=None,
                 img_url=None,
                 img_urls=None,
                 category=None,
                 category_id=None,
                 department=None):
        self.id = id
        self.canonical_url = canonical_url
        self.sku = sku
        self.brand = brand
        self.instock = instock
        self.stocklevel = stocklevel
        self.name = name
        self.title = title
        self.descr = descr
        self.price = price
        self.sale_price = sale_price
        self.currency = currency
        self.img_url = img_url
        self.img_urls = img_urls
        self.category = category
        self.category_id = category_id
        self.department = department

        if not self.img_urls and self.img_url:
            self.img_urls = [self.img_url]

    def __repr__(self):
        return '''ProductFarfetch:
    id...............%s
    url..............%s
    sku..............%s
    brand............%s
    instock..........%s
    stocklevel.......%s
    name.............%s
    title............%s
    descr............%s
    price............%s
    sale_price.......%s
    currency.........%s
    img_url..........%s
    category.........%s
    category_id......%s
    department.......%s
''' % (self.id,
       self.canonical_url,
       self.sku,
       self.brand,
       self.instock,
       self.stocklevel,
       self.name,
       self.title,
       self.descr,
       self.price,
       self.sale_price,
       self.currency,
       self.img_url,
       self.category,
       self.category_id,
       self.department)

    def to_product(self):
        return Product(
            merchant_slug='farfetch',
            url_canonical=self.canonical_url,
            merchant_sku=self.id,
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
            features=None,
            color=None,
            available_colors=None,
            size=None,
            available_sizes=None,
            img_url=self.img_url,
            img_urls=self.img_urls
        )


def get_meta_twitter(soup):

    t = {}

    # twitter card
    # ref: https://dev.twitter.com/cards/types/product
    # <meta property="twitter:card" content="product" />
    card = soup.find('meta', {'property': 'twitter:card'})
    if card:
        t['twitter:card'] = card.get('content')

    tags = soup.findAll(lambda tag: tag.name == 'meta' and tag.get('name') and tag.get('name').startswith('twitter:'))
    tm = {t.get('name'): t.get('content') for t in tags}
    # twitter is weird like this, mapping k:v pairs to 2 separate meta tags, yuck
    for i in xrange(len(tm) + 1):
        k = 'twitter:label%d' % i
        v = 'twitter:data%d' % i
        if k in tm and v in tm:
            t[tm[k]] = tm[v]
    return t


def script_UniversalVariable(soup):
    '''
    search for
    <script>window.universal_variable = { ... }</script>
    '''
    product = {}
    script = soup.find(lambda tag: tag.name == 'script' and 'window.universal_variable' in tag.text)
    if script:
        m = re.search('{.*}', script.text)
        if m:
            objstr = m.group(0)
            obj = json.loads(objstr)
            p = obj.get('product') or {}
            #pprint(p)
            product = {
                'brand': p.get(u'designerName'),
                'currency': p.get(u'currency'),
                'category': p.get(u'category'),
                'category_id': p.get(u'categoryId'),
                'department': p.get(u'department'),
                'name': p.get(u'name'),
                'id': p.get(u'id'),
                'img_url': p.get(u'image_url'),
                'in_stock': p.get(u'hasStock'),
                'sku': p.get(u'sku_code'),
                'stock_level': p.get(u'totalStock'),
                'price': p.get(u'unit_price'),
                'sale_price': p.get(u'unit_sale_price'),
                'url': p.get(u'url'),
            }
    return product

'''
{u'CurrencyCode': u'USD',
 u'category': u'Pumps',
 u'categoryId': 136307,
 u'currency': u'USD',
 u'department': u'Luxe',
 u'designerName': u'Jimmy Choo',
 u'hasStock': True,
 u'id': u'11249317',
 u'image_url': u'http://cdn-images.farfetch.com/11/24/93/17/11249317_6011630_120.jpg',
 u'name': u"'Lucy' pumps",
 u'prices': [{u'EUR': [{u'1': 543.16}, {u'2': 543.16}]},
             {u'USD': [{u'1': 574.02}, {u'2': 574.02}]},
             {u'GBP': [{u'1': 381.12}, {u'2': 381.12}]},
             {u'BRL': [{u'1': 2217.56}, {u'2': 2217.56}]},
             {u'CAD': [{u'1': 766.43}, {u'2': 766.43}]},
             {u'AUD': [{u'1': 793.13}, {u'2': 793.13}]},
             {u'JPY': [{u'1': 70688}, {u'2': 70688}]},
             {u'RUB': [{u'1': 38105.43}, {u'2': 38105.43}]},
             {u'KRW': [{u'1': 665341}, {u'2': 665341}]},
             {u'CHF': [{u'1': 590.75}, {u'2': 590.75}]},
             {u'SGD': [{u'1': 810.04}, {u'2': 810.04}]},
             {u'MXN': [{u'1': 9514.46}, {u'2': 9514.46}]}],
 u'sku_code': u'11249317',
 u'storeId': 9306,
 u'totalStock': 8,
 u'unit_price': 574.02,
 u'unit_price_aud': 793.13,
 u'unit_price_eur': 543.16,
 u'unit_price_gbp': 381.12,
 u'unit_price_jpy': 70688.3,
 u'unit_price_usd': 574.02,
 u'unit_sale_price': 574.02,
 u'unit_sale_price_aud': 793.13,
 u'unit_sale_price_eur': 543.16,
 u'unit_sale_price_gbp': 381.12,
 u'unit_sale_price_usd': 574.02,
 u'url': u'http://www.farfetch.com/shopping/women/jimmy-choo-lucy-pumps-item-11249317.aspx?storeid=9306'}
'''

class ProductsFarfetch(object):

    @staticmethod
    def from_html(url, html):

        starttime = time.time()

        products = []

        soup = BeautifulSoup(html)
        sp = SchemaOrg.get_schema_product(html)
        og = OG.get_og(soup)
        meta = HTMLMetadata.do_html_metadata(soup)
        #utag = Tealium.get_utag_data(soup)
        twit = get_meta_twitter(soup)
        uv = script_UniversalVariable(soup)

        sp = sp[0] if sp else {}

        signals = {
            'sp':  SchemaOrg.to_json(sp),
            'og':  og,
            'meta':meta,
            'tw':  twit,
            'uv':  uv,
        }

        prodid = uv.get('id') or None

        # is there one or more product on the page?
        if prodid:

            p = ProductFarfetch(
                id=prodid,
                canonical_url=url,
                sku=nth(sp.get(u'sku'), 0) or uv.get('sku') or None,
                brand=uv.get('brand') or None,
                instock=(uv.get('in_stock')
                            or og.get('availability') == u'instock'
                            or twit.get(u'Availability') == u'In Stock'),
                stocklevel=uv.get('stock_level'),
                name=xstrip(nth(sp.get(u'name'), 0)
                        or uv.get('name')
                        or og.get('title')
                        or meta.get('title') or None),
                title=(og.get('title')
                        or meta.get('title')
                        or None),
                descr=xstrip(nth(sp.get(u'description'), 0)
                        or og.get('description')
                        or meta.get('description') or None),
                sale_price=uv.get('sale_price') or None,
                price=(uv.get('price')
                       or og.get('price:amount')
                       or twit.get(u'Price') or None),
                currency=uv.get('currency') or og.get('price:currency') or None,
                img_url=uv.get('img_url') or og.get('image') or None,
                category=uv.get('category') or None,
                category_id=uv.get('category_id') or None,
                department=uv.get('department') or None
            )
            products.append(p)

        realproducts = [p.to_product() for p in products]

        page = ProductMapResultPage(
                    merchant_slug='farfetch',
                    url=url,
                    size=len(html),
                    proctime = time.time() - starttime,
                    signals=signals)

        return ProductMapResult(page=page,
                                products=realproducts)


if __name__ == '__main__':

    import gzip

    url = 'http://farfetch.example/'
    filepath = 'test/www.farfetch.com-shopping-women-jimmy-choo--lucy-pumps-item-11249317.aspx.gz'

    with gzip.open(filepath) as f:
        html = f.read()

    products = ProductsFarfetch.from_html(url, html)
    print products
