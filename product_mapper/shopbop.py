# ex: set ts=4 et:

'''
map a document archived from shopbop.com to zero or more products
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


class ProductShopbop(object):
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
        return '''ProductShopbop:
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
            merchant_slug='shopbop',
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



def get_script_ProductDetail(soup):
    '''
    <script type="text/javascript">
        var productDetail={
            "colors": {
        ...
    '''
    product = {}

    dd = {}
    pd = {}
    pp = {}

    prodid = None
    brand = None
    name = None
    in_stock = None
    price = None
    sale_price = None
    sizes = None
    colors = None
    img_url = None
    img_urls = None

    pi = soup.find(id='product-information')
    #print pi
    if pi:
        tag = pi.find(itemprop='brand')
        if tag:
            brand = normstring(tag.get_text())
        tag = pi.find(itemprop='name')
        if tag:
            name = normstring(tag.get_text())

    script = soup.find('script', text=lambda t: t and 'var productDetail' in t)
    if script:
        m = re.search('{[^;]+}\s*;', script.text, re.DOTALL)
        if m:
            objstr = m.group(0).rstrip(';')
            pd = json.loads(objstr)
            #pprint(pd)
            if 'sizes' in pd:
                sizes = sorted(pd.get('sizes').keys())
            if 'colors' in pd:
                try:
                    colors = [
                        v.get('colorName')
                            for k, v in pd['colors'].iteritems()
                                if v.get('colorName')]
                    img_urls = [
                        v2['main']
                            for k2, v2 in
                                v['images'].iteritems()
                                    for k, v in pd['colors'].iteritems()]
                    if img_urls:
                        img_url = img_urls[0]
                except:
                    traceback.print_exc()

    script = soup.find('script', text=lambda t: t and 'var productPage' in t)
    if script:
        m = re.search('var productPage.*', script.text, re.DOTALL)
        if m:
            objstr = m.group(0)
            objstr = 'var digitalData={};' + objstr + '; return productPage;'
            pp = execjs.exec_(objstr) or {}
            #pprint(pp)
            if pp:
                prodid = pp.get('productCode') or None
                in_stock = xboolstr(pp.get('isInStock')) or None
                price = pp.get('listPrice') or None
                sale_price = pp.get('sellingPrice') or None

    '''
    <script type='text/javascript'><!--
        var t0_date = new Date();
        window.ue_t0 = t0_date.getTime();
        var headerCountryCode = 'US';
        var chosenLanguageCode = 'en';
        var s_account = "amznshopbopprod";
        var digitalData = {"page":{"pageInfo":{"authState":"anonymous","variant":"prod","authType":"anonymous"},"attributes":{"country":"US","language":"en","currency":"USD","brand":"womens","platform":"www"},"category":{"primaryCategory":"Product:SERGI20248"}}} ;
        //--></script>
    '''
    script = soup.find('script', text=lambda t: t and 'var digitalData' in t)
    if script:
        m = re.search('var digitalData\s*=\s*({[^;]+})\s*;', script.text, re.DOTALL)
        if m:
            objstr = m.group(1)
            #print 'objstr:', objstr
            dd = json.loads(objstr)
            #pprint(dd)

    product = {
        'prodid': prodid,
        'brand': brand,
        'name': name,
        'in_stock': in_stock,
        'price': price,
        'sale_price': sale_price,
        'sizes': sizes,
        'colors': colors,
        'img_url': img_url,
        'img_urls': img_urls,
        'dd': dd,
        'pd': pd,
        'pp': pp,
    }
    #pprint(product)
    return product


class ProductsShopbop(object):

    VERSION = 0

    @classmethod
    def from_html(cls, url, html):

        starttime = time.time()

        products = []

        soup = BeautifulSoup(html)
        meta = HTMLMetadata.do_html_metadata(soup)
        sp = SchemaOrg.get_schema_product(html)
        og = OG.get_og(soup)
        pd = get_script_ProductDetail(soup)

        sp = sp[0] if sp else {}

        signals = {
            'meta':meta,
            'sp':  SchemaOrg.to_json(sp),
            'og':  og,
            'pd':  pd,
        }

        prodid = pd.get('prodid') or None

        # is there one or more product on the page?
        if prodid:

            p = ProductShopbop(
                prodid=prodid,
                canonical_url=url,
                brand=pd.get('brand') or None,
                instock=(pd.get('in_stock')
                            or og.get('availability') == u'instock'),
                stocklevel=pd.get('stock_level'),
                name=(nth(sp.get(u'name'), 0)
                        or pd.get('name')
                        or og.get('title')
                        or meta.get('title') or None),
                title=(og.get('title')
                        or meta.get('title')
                        or None),
                descr=(nth(sp.get(u'description'), 0)
                        or og.get('description')
                        or meta.get('description') or None),
                sale_price=pd.get('sale_price') or None,
                price=(pd.get('price')
                       or og.get('price:amount') or None),
                currency=pd.get('currency') or og.get('price:currency') or None,
                size=pd.get('size') or None,
                sizes=pd.get('sizes') or None,
                color=pd.get('color') or None,
                colors=pd.get('colors') or None,
                img_url=pd.get('img_url') or og.get('image') or None,
                img_urls=pd.get('img_urls') or None,
                category=pd.get('category') or None,
                category_id=pd.get('category_id') or None,
                department=pd.get('department') or None
            )
            products.append(p)

        realproducts = [p.to_product() for p in products]

        page = ProductMapResultPage(
                    version=cls.VERSION,
                    merchant_slug='shopbop',
                    url=url,
                    size=len(html),
                    proctime = time.time() - starttime,
                    signals=signals)

        return ProductMapResult(page=page,
                                products=realproducts)


if __name__ == '__main__':

    import gzip

    url = 'https://www.shopbop.com/tresor-pump-sergio-rossi/vp/v=1/1576638246.htm'
    filepath = 'test/www.shopbop.com-tresor-pump-sergio-rossi-vp-v-1-1576638246.htm.gz'

    with gzip.open(filepath) as f:
        html = f.read()

    products = ProductsShopbop.from_html(url, html)
    print products
