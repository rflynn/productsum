# ex: set ts=4 et:
# -*- coding: utf-8 *-*

'''
map a document archived from stylebop.com to zero or more products
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


class ProductStylebop(object):
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
        return '''ProductStylebop:
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
            merchant_slug='stylebop',
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

    url_canonical = None
    prodid = None
    sku = None
    brand = None
    category = None
    breadcrumb = None
    color = None
    name = None
    descr = None
    in_stock = None
    price = None
    currency = None
    features = None
    size = None
    sizes = None
    color = None
    colors = None
    img_url = None
    img_urls = None


    tag = soup.find('link', rel='canonical', href=True)
    if tag:
        url_canonical = tag.get('href')
    if not url_canonical:
        tag = soup.find('meta', itemprop='url', content=True)
        if tag:
            url_canonical = tag.get('content')

    '''
    <script>
        window.tmParam = {...
    '''
    tag = soup.find('script', text=lambda t: t and 'window.tmParam = {' in t)
    if tag:
        obj = {}
        m = re.search('(window.tmParam = {.*})', tag.text, re.DOTALL)
        if m:
            objstr = 'var window={}; ' + m.groups(0)[0] + '; return window.tmParam;'
            #print objstr
            try:
                obj = execjs.exec_(objstr)
                pprint(obj)
            except:
                traceback.print_exc()
        try:
            prodid = prodid or obj.get('product_id') # what's the difference?
            sku = sku or obj.get('product_sku')
            brand = brand or obj.get('product_brand')
            name = name or obj.get('product_name')
            price = price or obj.get('product_price')
            currency = currency or obj.get('currency_code')
            category = category or obj.get('product_category')
        except:
            traceback.print_exc()
    
    '''
    <script>
        dataLayer = [{...
    '''
    dl = {}
    tag = soup.find('script', text=lambda t: t and 'dataLayer = [{' in t)
    if tag:
        #print objstr
        try:
            obj = json.loads(tag.text)
            pprint(obj)
            dl = obj[0]
        except:
            traceback.print_exc()
    prodid = sku or dl.get('productSKU')
    sku = sku or dl.get('productSKU')
    brand = brand or dl.get('pageDesigner')
    if in_stock is None:
        in_stock = dl.get('productinstock')
    category = category or dl.get('pageCategory')
    name = name or dl.get('productname')
    img_url = img_url or dl.get('productimgurl')
    breadcrumb = dl.get('categorypath')

    '''
    <table class="product_details_table">
    '''
    tag = soup.find('table', attrs={'class': 'product_details_table'})
    if tag:
        tds = tag.findAll('td', attrs={'class': 'productlisting'})
        features = [normstring(t.get_text()) for t in tds] or None
        if features:
            descr = features.pop(0)
            features = features or None

    product = {
        'url_canonical': url_canonical,
        'prodid': prodid,
        'sku': sku,
        'in_stock': in_stock,
        'brand': brand,
        'category': category,
        'breadcrumb': breadcrumb,
        'name': name,
        'descr': descr,
        'price': price,
        'currency': currency,
        'features': features,
        'size': size,
        'sizes': sizes,
        'color': color,
        'colors': colors,
        'img_url': img_url,
        'img_urls': img_urls,
    }
    #pprint(product)
    return product


class ProductsStylebop(object):

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

        spbrand = None
        try:
            spbrand = sp['brand']['properties']['name']
        except:
            pass

        # is there one or more product on the page?
        if prodid:
            p = ProductStylebop(
                prodid=prodid,
                canonical_url=custom.get('url') or og.get('url') or url,
                brand=u(custom.get('brand')) or spbrand or None,
                category=u(custom.get('category')) or None,
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
                descr=u(custom.get('descr')
                        or nth(sp.get(u'description'), 0)
                        or og.get('description')
                        or meta.get('description') or None),
                sale_price=custom.get('sale_price') or None,
                price=u(custom.get('price')
                       or og.get('price:amount') or None),
                currency=custom.get('currency') or og.get('price:currency') or None,
                features=custom.get('features') or None,
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
                    merchant_slug='stylebop',
                    url=url,
                    size=len(html),
                    proctime = time.time() - starttime,
                    signals=signals)

        return ProductMapResult(page=page,
                                products=realproducts)


if __name__ == '__main__':

    import gzip

    url = 'http://www.stylebop.com/product_details.php?id=658846'
    filepath = 'test/www.stylebop.com-product_details.php-id-658846.gz'

    # test no-op
    #filepath = 'test/www.dermstore.com-product_Lipstick_31136.htm.gz'

    with gzip.open(filepath) as f:
        html = unicode(f.read(), 'utf8')

    products = ProductsStylebop.from_html(url, html)
    print products
