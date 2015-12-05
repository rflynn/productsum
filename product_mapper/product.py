# ex: set ts=4 et:


'''
one product to rule them all
every FoobarMerchantProduct maps to this thing
'''

import json
import psycopg2
import re
from yurl import URL

from util import dehtmlify, normstring


dbhost = 'productmap.ccon1imhl6ui.us-east-1.rds.amazonaws.com'
dbname = 'productmap'
dbuser = 'root'
dbpass = 'SyPi6q1gp961'

# PGPASSWORD=SyPi6q1gp961 psql -h productmap.ccon1imhl6ui.us-east-1.rds.amazonaws.com -U root productmap

# ref: http://initd.org/psycopg/docs/usage.html#unicode-handling
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
#psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)


_Conn = None
def get_psql_conn():
    global _Conn
    if not _Conn:
        _Conn = psycopg2.connect("host='%s' user='%s' password='%s' dbname='%s'" % (
            (dbhost, dbuser, dbpass, dbname)))
        _Conn.set_client_encoding('utf8')
        print _Conn
    return _Conn


class Product(object):

    def __init__(self,
                 merchant_slug=None, url_canonical=None, merchant_sku=None,
                 merchant_product_obj=None,
                 upc=None, gtin8=None, gtin12=None, gtin13=None, gtin14=None, mpn=None,
                 price=None, sale_price=None, currency=None,
                 brand=None, category=None, bread_crumb=None,
                 in_stock=None, stock_level=None,
                 name=None, title=None, descr=None,
                 features=None,
                 color=None, available_colors=None,
                 size=None, available_sizes=None,
                 img_url=None, img_urls=None):

        # typechecking
        assert isinstance(merchant_slug,    basestring)
        assert isinstance(url_canonical,    basestring)
        assert isinstance(merchant_sku,     basestring)
        assert merchant_product_obj is not None
        assert isinstance(upc,              (type(None), basestring))
        assert isinstance(gtin8,            (type(None), basestring))
        assert isinstance(gtin12,           (type(None), basestring))
        assert isinstance(gtin13,           (type(None), basestring))
        assert isinstance(gtin14,           (type(None), basestring))
        assert isinstance(mpn,              (type(None), basestring))
        assert isinstance(price,            (type(None), int, float, basestring))
        assert isinstance(sale_price,       (type(None), int, float, basestring))
        assert isinstance(currency,         (type(None), basestring))
        assert isinstance(brand,            (type(None), basestring))
        assert isinstance(category,         (type(None), basestring))
        assert isinstance(bread_crumb,      (type(None), list))
        assert isinstance(in_stock,         (type(None), bool))
        assert isinstance(stock_level,      (type(None), int, long))
        assert isinstance(name,             (type(None), basestring))
        assert isinstance(title,            (type(None), basestring))
        assert isinstance(descr,            (type(None), basestring))
        assert isinstance(features,         (type(None), list))
        assert isinstance(color,            (type(None), basestring))
        assert isinstance(available_colors, (type(None), list))
        assert isinstance(size,             (type(None), basestring))
        assert isinstance(available_sizes,  (type(None), list))
        assert isinstance(img_url,          (type(None), basestring))
        assert isinstance(img_urls,         (type(None), list))

        # logical checking
        # no false-y entries e.g. [''] or [None]
        assert not available_colors or all(available_colors)
        assert not available_sizes or all(available_sizes)
        assert not img_urls or all(img_urls)

        self.merchant_slug = merchant_slug
        self.url_canonical = url_canonical
        self.url_host = URL(url_canonical).host
        self.merchant_sku = merchant_sku
        self.upc = upc
        self.gtin8 = gtin8
        self.gtin12 = gtin12
        self.gtin13 = gtin13
        self.gtin14 = gtin14
        self.mpn = mpn
        self.price_str = str(price)
        self.price_min = None
        self.price_max = None
        self.sale_price_str = str(sale_price)
        self.sale_price_min = None
        self.sale_price_max = None
        self.currency = currency
        self.brand = brand
        self.category = category
        self.bread_crumb = bread_crumb
        self.in_stock = in_stock
        self.stock_level = stock_level
        self.name = name
        self.title = title
        self.descr = descr
        self.features = features
        self.color = color
        self.available_colors = available_colors
        self.size = size
        self.available_sizes = available_sizes
        self.img_url = img_url if img_url else img_urls[0] if img_urls else None
        self.img_urls = img_urls

        self.fixup_prices_and_currency()

        # verify errors fixed up
        if self.name is not None:
            self.name = normstring(dehtmlify(self.name))
            assert '<sup>' not in self.name
            assert '</sup>' not in self.name
            assert '<br>' not in self.name
            assert '<strong>' not in self.name
            assert '&amp;' not in self.name


    def fixup_prices_and_currency(self):
        cur, pmin, pmax = Product.parse_price(self.price_str)
        if not self.currency and cur:
            if cur == '$':
                self.currency = 'USD'
        if pmin:
            self.price_min = pmin
        if pmax:
            self.price_max = pmax
        
        cur, pmin, pmax = Product.parse_price(self.sale_price_str)
        if not self.currency and cur:
            if cur == '$':
                self.currency = 'USD'
        if pmin:
            self.sale_price_min = pmin
        if pmax:
            self.sale_price_max = pmax

    @staticmethod
    def parse_price(value):
        currency = None
        price_min = None
        price_max = None
        if value:
            value = re.sub('\s+', ' ', value.strip())
            r = Product._do_parse_price_range(value)
            if r:
                currency, price_min, _sep, _cur2, price_max = r
            else:
                p = Product._do_parse_price(value)
                if p:
                    currency, price_min = p
                    price_max = price_min
        return currency, price_min, price_max

    @staticmethod
    def _do_parse_price(price):
        # FIXME: price parsing via regex is not good enough; use a proper parser...
        m = re.match('([$]?)((?:\d{1,3},)?\d{1,6}(?:\.\d{1,3})?)', price)
        if m:
            cur1, pr1 = m.groups()
            if not cur1: cur1 = None
            return cur1, pr1.replace(',','')
        return None

    @staticmethod
    def _do_parse_price_range(price):
        # FIXME: price parsing via regex is not good enough; use a proper parser...
        m = re.match('([$]?)((?:\d{1,3},)?\d{1,6}(?:\.\d{1,3})?)\s*([-]|to)\s*([$]?)((?:\d{1,3},)?\d{1,6}(?:\.\d{1,3})?)', price)
        # ('$', '100.00', '-', '$', '200')
        if m:
            cur1, pr1, sep, cur2, pr2 = m.groups()
            if not cur1: cur1 = None
            if not cur2: cur2 = None
            return cur1, pr1.replace(',',''), sep, cur2, pr2.replace(',','')
        return None

    def __repr__(self):
        return ('''Product(
    merchant_slug.....%s
    url_canonical.....%s
    url_host..........%s
    merchant_sku......%s
    upc...............%s
    gtin8.............%s
    gtin12............%s
    gtin13............%s
    gtin14............%s
    mpn...............%s
    price_str.........%s
    price_min.........%s
    price_max.........%s
    sale_price_str....%s
    sale_price_min....%s
    sale_price_max....%s
    currency..........%s
    brand.............%s
    category..........%s
    bread_crumb.......%s
    in_stock..........%s
    stock_level.......%s
    name..............%s
    title.............%s
    descr.............%s
    features..........%s
    color.............%s
    available_colors..%s
    size..............%s
    available_sizes...%s
    img_url...........%s
    img_urls..........%s
)''' % (self.merchant_slug,
       self.url_canonical,
       self.url_host,
       self.merchant_sku,
       self.upc,
       self.gtin8,
       self.gtin12,
       self.gtin13,
       self.gtin14,
       self.mpn,
       self.price_str,
       self.price_min,
       self.price_max,
       self.sale_price_str,
       self.sale_price_min,
       self.sale_price_max,
       self.currency,
       self.brand,
       self.category,
       self.bread_crumb,
       self.in_stock,
       self.stock_level,
       self.name,
       self.title,
       self.descr,
       self.features,
       self.color,
       self.available_colors,
       self.size,
       self.available_sizes,
       self.img_url,
       self.img_urls)).encode('utf8')

    def _psql_update(self, cursor):
        cursor.execute('''
update url_product
set
    updated = now(),
    merchant_slug = %s,
    url_host = %s,
    merchant_sku = %s,
    upc = %s,
    gtin8 = %s,
    gtin12 = %s,
    gtin13 = %s,
    gtin14 = %s,
    mpn = %s,
    price_min = %s,
    price_max = %s,
    sale_price_min = %s,
    sale_price_max = %s,
    currency = %s,
    brand = %s,
    category = %s,
    bread_crumb = %s,
    in_stock = %s,
    stock_level = %s,
    name = %s,
    title = %s,
    descr = %s,
    features = %s,
    color = %s,
    available_colors = %s,
    size = %s,
    available_sizes = %s,
    img_url = %s,
    img_urls = %s
where
    url_canonical = %s
''',  (self.merchant_slug,
       self.url_host,
       self.merchant_sku,
       self.upc,
       self.gtin8,
       self.gtin12,
       self.gtin13,
       self.gtin14,
       self.mpn,
       self.price_min,
       self.price_max,
       self.sale_price_min,
       self.sale_price_max,
       self.currency,
       self.brand,
       self.category,
       self.bread_crumb,
       self.in_stock,
       self.stock_level,
       self.name,
       self.title,
       self.descr,
       self.features,
       self.color,
       self.available_colors,
       self.size,
       self.available_sizes,
       self.img_url,
       self.img_urls,
       self.url_canonical))

    def _psql_insert(self, cursor):
        cursor.execute('''
insert into url_product (
    created,
    updated,
    merchant_slug,
    url_host,
    url_canonical,
    merchant_sku,
    upc,
    gtin8,
    gtin12,
    gtin13,
    gtin14,
    mpn,
    price_min,
    price_max,
    sale_price_min,
    sale_price_max,
    currency,
    brand,
    category,
    bread_crumb,
    in_stock,
    stock_level,
    name,
    title,
    descr,
    features,
    color,
    available_colors,
    size,
    available_sizes,
    img_url,
    img_urls
) values (
    now(),
    now(),
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s
)
''',  (self.merchant_slug,
       self.url_host,
       self.url_canonical,
       self.merchant_sku,
       self.upc,
       self.gtin8,
       self.gtin12,
       self.gtin13,
       self.gtin14,
       self.mpn,
       self.price_min,
       self.price_max,
       self.sale_price_min,
       self.sale_price_max,
       self.currency,
       self.brand,
       self.category,
       self.bread_crumb,
       self.in_stock,
       self.stock_level,
       self.name,
       self.title,
       self.descr,
       self.features,
       self.color,
       self.available_colors,
       self.size,
       self.available_sizes,
       self.img_url,
       self.img_urls))

    def save(self, conn, commit=True):
        with conn.cursor() as cursor:
            self._psql_update(cursor)
            if cursor.rowcount == 0:
                self._psql_insert(cursor)
            if commit:
                conn.commit()


class ProductMapResultPage(object):
    '''
    metadata about the processing/product-mapping of an HTML page,
    regardless of whether it had products on it or not
    '''
    def __init__(self,
                 merchant_slug=None,
                 url=None,
                 size=None,
                 proctime=None,
                 signals=None):
        assert merchant_slug
        assert url
        assert size and size > 0
        assert proctime and proctime > 0
        assert signals is None or isinstance(signals, dict)
        self.merchant_slug = merchant_slug
        self.url = url
        self.url_host = URL(url).host
        self.size = size
        self.proctime = proctime
        self.signals = signals

    def __repr__(self):
        return ('''ProductMapResultPage(
    merchant_slug...%s
    url.............%s
    size............%s
    proctime........%s
    signals.........%s
)''' % (self.merchant_slug,
        self.url,
        self.size,
        self.proctime,
        self.signals)).encode('utf8')

    def _psql_update(self, cursor):
        cursor.execute('''
update url_page
set
    updated = now(),
    merchant_slug = %s,
    url_host = %s,
    size = %s,
    proctime = %s,
    signals = %s
where
    url_canonical = %s
''',  (self.merchant_slug,
       self.url_host,
       self.size,
       self.proctime,
       json.dumps(self.signals), # Json...
       self.url))

    def _psql_insert(self, cursor):
        cursor.execute('''
insert into url_page (
    created,
    updated,
    merchant_slug,
    url_host,
    url_canonical,
    size,
    proctime,
    signals
) values (
    now(),
    now(),
    %s,
    %s,
    %s,
    %s,
    %s,
    %s
)
''',  (self.merchant_slug,
       self.url_host,
       self.url,
       self.size,
       self.proctime,
       json.dumps(self.signals)))

    def save(self, conn, commit=True):
        with conn.cursor() as cursor:
            self._psql_update(cursor)
            if cursor.rowcount == 0:
                self._psql_insert(cursor)
            if commit:
                conn.commit()


class ProductMapResult(object):
    '''
    the result of a product map attempt, contains
        * metadata about the page itself
        * product data in the form of Product, and also underlying per-merchant FooProduct data
    '''
    def __init__(self, page=None, products=None):
        assert isinstance(page, ProductMapResultPage)
        assert isinstance(products, list)
        assert all(isinstance(p, Product) for p in products)
        self.page = page
        self.products = products

    def __repr__(self):
        return '''ProductMapResult(
    page=%s
    products=%s
)''' % (self.page,
       self.products)

    def save(self):
        # TODO: optimize by 
        conn = get_psql_conn()
        self.page.save(conn, commit=False)
        for p in self.products:
            p.save(conn, commit=False)
        conn.commit()

if __name__ == '__main__':
    p = Product(merchant_slug='foo_merch',
                url_canonical='http://example.com/',
                merchant_sku='12345',
                merchant_product_obj='lol',
                name=None)
    print p

