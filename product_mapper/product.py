# ex: set ts=4 et:


'''
one product to rule them all
every FoobarMerchantProduct maps to this thing
'''

import calendar
from datetime import datetime
import json
import psycopg2
import re
from urlparse import urljoin
from yurl import URL

from util import dehtmlify, normstring, unquote
from dbconn import get_psql_conn


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
        assert isinstance(merchant_product_obj.VERSION, int)
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
        assert merchant_sku
        assert merchant_sku != 'None' # bug
        # no false-y entries e.g. [''] or [None]
        assert not available_colors or all(available_colors)
        assert not available_sizes or all(available_sizes)
        assert not img_urls or all(img_urls)

        self.merchant_product_obj = merchant_product_obj
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
        self.img_url = img_url
        self.img_urls = img_urls

        # cross-populate
        if img_url and not img_urls:
            self.img_urls = [img_url]
        elif img_urls and not img_url:
            self.img_url = self.img_urls[0]

        self.fixup_upc()
        self.fixup_prices_and_currency()
        self.fixup_img_urls()

        if self.category:
            self.category = dehtmlify(normstring(self.category))

        if self.brand:
            self.brand = unquote(dehtmlify(normstring(self.brand)))
            assert '&#39;' not in self.brand

        if self.brand and self.name:
            if self.name.lower().startswith(self.brand.lower()):
                if not self.title:
                    self.title = self.name
                self.name = self.name[len(self.brand):].lstrip()

        # verify errors fixed up
        if self.name is not None:
            self.name = normstring(dehtmlify(self.name))
            assert '<sup>' not in self.name
            assert '</sup>' not in self.name
            assert '<br>' not in self.name
            assert '<strong>' not in self.name
            assert '&amp;' not in self.name

        if self.title:
            self.title = normstring(dehtmlify(self.title))

        if self.descr:
            self.descr= normstring(dehtmlify(self.descr))

    def fixup_img_urls(self):
        # canonicalize; no protocol-less "//foo.bar/..."
        if self.img_url:
            self.img_url = urljoin(self.url_canonical, self.img_url)
        if self.img_urls:
            self.img_urls = [urljoin(self.url_canonical, u) for u in self.img_urls]

    def fixup_upc(self):
        # upc is intended to allow product mappers to specify a vague-ish UPC
        # value without really error-checking or understanding all formats in all mappers
        # here we map this value to the appropriate specific GTIN
        if self.upc:
            if not re.match('^[0-9]{8,14}$', self.upc):
                print "upc doesn't match known pattern..."
            else:
                l = len(self.upc)
                if l == 8 and not self.gtin8:
                    self.gtin8 = self.upc
                elif l == 12 and not self.gtin12:
                    self.gtin12 = self.upc
                elif l == 13 and not self.gtin13:
                    self.gtin13 = self.upc
                elif l == 14 and not self.gtin14:
                    self.gtin14 = self.upc
        # map GTINs up...
        # ref: http://www.gtin.info/
        if self.gtin13:
            if not re.match('^[0-9]{13}$', self.gtin13):
                print u"gtin13 '%s' does not match numeric pattern..." % (self.gtin13,)
            else:
                if not self.gtin14:
                    self.gtin14 = '0' + self.gtin13
        elif self.gtin12:
            if not re.match('^[0-9]{12}$', self.gtin12):
                print u"gtin12 '%s' does not match numeric pattern..." % (self.gtin12,)
            else:
                if not self.gtin13 and not self.gtin14:
                    self.gtin13 = '0' + self.gtin12
                    self.gtin14 = '00' + self.gtin12
        elif self.gtin8:
            if not re.match('^[0-9]{8}$', self.gtin8):
                print u"gtin8 '%s' does not match numeric pattern..." % (self.gtin8,)
            else:
                if not self.gtin12 and not self.gtin13 and not self.gtin14:
                    self.gtin12 = '000000' + self.gtin8
                    self.gtin13 = '0000000' + self.gtin8
                    self.gtin14 = '00000000' + self.gtin8

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
    VERSION........... %s
    merchant_slug..... %s
    url_canonical..... %s
    url_host.......... %s
    merchant_sku...... %s
    upc............... %s
    gtin8............. %s
    gtin12............ %s
    gtin13............ %s
    gtin14............ %s
    mpn............... %s
    price_str......... %s
    price_min......... %s
    price_max......... %s
    sale_price_str.... %s
    sale_price_min.... %s
    sale_price_max.... %s
    currency.......... %s
    brand............. %s
    category.......... %s
    bread_crumb....... %s
    in_stock.......... %s
    stock_level....... %s
    name.............. %s
    title............. %s
    descr............. %s
    features.......... %s
    color............. %s
    available_colors.. %s
    size.............. %s
    available_sizes... %s
    img_url........... %s
    img_urls.......... %s
)''' % (self.merchant_product_obj.VERSION,
       self.merchant_slug,
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
        try:
            cursor.execute('''
update url_product
set
    updated = now(),
    product_mapper_version = %s,
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
''',  (self.merchant_product_obj.VERSION,
       self.merchant_slug,
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
        except:
            print self
            raise

    def _psql_insert(self, cursor):
        try:
            cursor.execute('''
insert into url_product (
    created,
    updated,
    product_mapper_version,
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
    %s,
    %s,
    %s
)
''',  (self.merchant_product_obj.VERSION,
       self.merchant_slug,
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
        except:
            print self
            raise

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
                 version=None,
                 merchant_slug=None,
                 url=None,
                 size=None,
                 proctime=None,
                 signals=None):
        assert isinstance(version, int)
        assert version >= 0
        assert version < 32768
        assert merchant_slug
        assert url
        assert size and size > 0
        assert proctime and proctime > 0
        assert signals is None or isinstance(signals, dict)
        self.version = version
        self.merchant_slug = merchant_slug
        self.url = url
        self.url_host = URL(url).host
        self.size = size
        self.proctime = proctime
        self.signals = signals

    def __repr__(self):
        return ('''ProductMapResultPage(
    version.........%s
    merchant_slug...%s
    url.............%s
    size............%s
    proctime........%s
    signals.........%s
)''' % (self.version,
        self.merchant_slug,
        self.url,
        self.size,
        self.proctime,
        self.signals)).encode('utf8')

    def _psql_update(self, cursor):
        cursor.execute('''
update url_page
set
    updated = now(),
    product_mapper_version = %s,
    merchant_slug = %s,
    url_host = %s,
    size = %s,
    proctime = %s,
    signals = %s
where
    url_canonical = %s
''',  (self.version,
       self.merchant_slug,
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
    product_mapper_version,
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
    %s,
    %s
)
''',  (self.version,
       self.merchant_slug,
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

    @staticmethod
    def last_updated(conn, url_host, url_canonical):
        with conn.cursor() as cursor:
            cursor.execute('''
select updated
from url_page
where url_host = %s
and url_canonical = %s
''', (url_host, url_canonical))
            row = cursor.fetchone()
            if not row or row[0] is None:
                return None
            return calendar.timegm(row[0].timetuple())

    @staticmethod
    def first_any_updated(conn, url_host):
        with conn.cursor() as cursor:
            cursor.execute('''
select min(updated)
from url_page
where url_host = %s
''', (url_host,))
            row = cursor.fetchone()
            if not row or row[0] is None:
                return None
            return calendar.timegm(row[0].timetuple())


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
    class Foo:
        VERSION = 0
    p = Product(merchant_slug='foo_merch',
                url_canonical='http://example.com/',
                merchant_sku='12345',
                merchant_product_obj=Foo(),
                name=None)
    print p

