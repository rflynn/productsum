# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from saks.com to zero or more products
'''

from bs4 import BeautifulSoup
import gzip
import execjs
from pprint import pprint
import re
import time
import traceback

from htmlmetadata import HTMLMetadata
from og import OG
from product import Product, ProductMapResultPage, ProductMapResult
from schemaorg import SchemaOrg
from tealium import Tealium
from util import nth, normstring, xstrip, xboolstr, maybe_join, dehtmlify


class ProductSaks(object):
    def __init__(self, prodid=None, canonical_url=None, upc=None,
                 stocklevel=None, instock=None,
                 price=None, sale_price=None, currency=None,
                 bread_crumb=None, brand=None,
                 name=None, title=None, descr=None,
                 features=None, size=None, sizes=None,
                 color=None, colors=None,
                 img_url=None, skus=None):

        assert prodid is None or isinstance(prodid, basestring)
        assert canonical_url is None or isinstance(canonical_url, basestring)
        assert upc is None or isinstance(upc, basestring)
        assert stocklevel is None or isinstance(stocklevel, basestring)
        assert instock is None or isinstance(instock, bool)
        assert bread_crumb is None or isinstance(bread_crumb, list)
        assert brand is None or isinstance(brand, basestring)
        assert price is None or isinstance(price, basestring)
        assert sale_price is None or isinstance(sale_price, basestring)
        assert currency is None or isinstance(currency, basestring)
        assert name is None or isinstance(name, basestring)
        assert title is None or isinstance(title, basestring)
        assert descr is None or isinstance(descr, basestring)
        assert features is None or isinstance(features, list)
        assert size is None or isinstance(size, basestring)
        assert sizes is None or isinstance(sizes, list)
        assert color is None or isinstance(color, basestring)
        assert colors is None or isinstance(colors, list)
        assert img_url is None or isinstance(img_url, basestring)
        assert skus is None or isinstance(skus, list)

        self.prodid = prodid
        self.upc = upc
        self.canonical_url = canonical_url
        self.stocklevel = stocklevel
        self.instock = instock
        self.price = price
        self.sale_price = sale_price
        self.currency = currency
        self.bread_crumb = bread_crumb
        self.brand = normstring(brand)
        self.name = normstring(name)
        self.title = normstring(title)
        self.descr = descr
        self.features = features
        self.size = size
        self.sizes = sizes
        self.color = color
        self.colors = colors
        self.img_url = img_url
        self.skus = skus

        # fixups
        # ...

    def __repr__(self):
        return '''ProductSaks(
    url...........%s
    prodid........%s
    upc...........%s
    instock.......%s
    stocklevel....%s
    price.........%s
    sale_price....%s
    currency......%s
    brand.........%s
    bread_crumb...%s
    name..........%s
    title.........%s
    descr.........%s
    features......%s
    size..........%s
    sizes.........%s
    color.........%s
    colors........%s
    img_url.......%s
    skus..........%s
)''' % (self.canonical_url, self.prodid,  self.upc,
       self.instock, self.stocklevel,
       self.price, self.sale_price, self.currency,
       self.brand, self.bread_crumb,
       self.name, self.title, self.descr,
       self.features, self.size, self.sizes,
       self.color, self.colors,
       self.img_url, self.skus)

    def to_product(self):

        category = None
        if self.bread_crumb:
            category = self.bread_crumb[-1]

        return Product(
            merchant_slug='saks',
            url_canonical=self.canonical_url,
            merchant_sku=str(self.prodid),
            upc=self.upc,
            merchant_product_obj=self,
            price=self.price,
            sale_price=self.sale_price,
            currency=self.currency,
            category=category,
            brand=self.brand,
            bread_crumb=self.bread_crumb,
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
            img_urls=[self.img_url] if self.img_url else None
        )




class ProductsSaks(object):

    @staticmethod
    def from_html(url, html):

        starttime = time.time()

        products = []

        soup = BeautifulSoup(html)
        meta = HTMLMetadata.do_html_metadata(soup)
        og = OG.get_og(html)
        mlrs = ProductsSaks.get_custom(soup)

        signals = {
            'meta': meta,
            'og':   og,
            'mlrs': mlrs,
        }
        #pprint(signals)

        # is there one or more product on the page?
        if (mlrs.get('product_id') or og.get('type') == u'product'):

            p = ProductSaks(
                prodid=mlrs.get('product_id'),
                upc=mlrs.get('upc'),
                canonical_url=mlrs.get('url_canonical') or og.get('url') or url,
                stocklevel=None,
                instock=(mlrs.get('instock')
                            or (og.get('availability') in ('instock',)
                                if 'availability' in og else None)),
                price=mlrs.get('price') or og.get('price:amount') or None,
                sale_price=mlrs.get('sale_price') or None,
                currency=og.get('price:currency') or None,
                bread_crumb=mlrs.get('breadcrumb') or None,
                brand=mlrs.get('brand') or og.get('brand') or None,
                name = (mlrs.get('name')
                            or og.get('title')
                            or meta.get('title') or None),
                title=og.get('title') or meta.get('title') or None,
                descr=mlrs.get('descr') or og.get('description') or meta.get('description') or None,
                features=mlrs.get('features') or None,
                color=mlrs.get('color') or None,
                colors=mlrs.get('colors') or None,
                size=mlrs.get('size') or None,
                sizes=mlrs.get('sizes') or None,
                skus=mlrs.get('skus') or None,
                img_url=og.get('image') or None,
            )
            products.append(p)

        realproducts = [p.to_product() for p in products]

        page = ProductMapResultPage(
                 merchant_slug='saks',
                 url=url,
                 size=len(html),
                 proctime = time.time() - starttime,
                 signals=signals)

        return ProductMapResult(page=page,
                                products=realproducts)


    @staticmethod
    def get_custom(soup):

        # url
        # TODO: move this to standardized HTMLMetadata
        url_canonical = None
        tag = soup.find('link', rel='canonical', href=True)
        if tag:
            url_canonical = tag.get('href')
        if not url_canonical:
            tag = soup.find('meta', itemprop='url', content=True)
            if tag:
                url_canonical = tag.get('content')

        mlrs = {}

        '''
        <script type="text/javascript">
            var mlrs = {"request":{"url":
        '''

        tag = soup.find('script', text=lambda txt: txt and 'var mlrs =' in txt)
        if tag:
            m = re.search('{.*}', tag.text, re.DOTALL)
            if m:
                try:
                    objstr = m.group(0)
                    obj = execjs.eval(objstr)
                    #pprint(obj)
                    body = obj['response']['body']['main_products']
                    prodlen = len(body)
                    obj = body[0]
                    #pprint(body)

                    # description containing list of features...
                    descr = xstrip(obj.get('description'))
                    features = None
                    if descr:
                        tag = BeautifulSoup(descr)
                        li = tag.findAll('li')
                        if li:
                            features = [xstrip(normstring(dehtmlify(f.text))) for f in li if f]
                            for x in li:
                                x.extract() # strip from description...
                        #print 'descr:'
                        #pprint(tag.body.contents)
                        #pprint([(x.name, x) for x in tag.body.contents])
                        for t in tag.findAll(lambda tag: tag.name in ('ul',)): t.extract()
                        #tag.extract('li')
                        #print 'extracted:'
                        #pprint(tag)
                        descr = xstrip(normstring(tag.get_text()))

                    sold_out = obj['sold_out_message'].get('enabled') if 'sold_out_message' in obj else None
                    skus = obj['skus'].get('skus') if 'skus' in obj else None

                    name = None
                    if 'clarity_event_tags' in obj:
                        if 'product_name_event' in obj['clarity_event_tags']:
                            name = obj['clarity_event_tags']['product_name_event'].get('value')


                    sizes = obj['sizes'].get('sizes') if 'sizes' in obj else None
                    if sizes is not None and not isinstance(sizes, list):
                        sizes = None
                    if sizes and not all(isinstance(s, basestring) for s in sizes):
                        if all(isinstance(s, dict) for s in sizes):
                            '''
[{u'size_id': 0, u'is_sold_out_waitlistable': False, u'value': u'35 (5)'}, {u'size_id': 1, u'is_sold_out_waitlistable': False, u'value': u'36 (6)'}, {u'size_id': 4, u'is_sold_out_waitlistable': True, u'value': u'39 (9)'}, {u'size_id': 5, u'is_sold_out_waitlistable': True, u'value': u'40 (10)'}, {u'size_id': 6, u'is_sold_out_waitlistable': False, u'value': u'41 (11)'}]
                            '''
                            # ref: http://www.saksfifthavenue.com/Jewelry-and-Accessories/Jewelry/Rings/shop/_/N-52flr4/Ne-6lvnb5?FOLDER%3C%3Efolder_id=2534374306418144&Nao=120
                            if all(s.get('size_id') is not None and s.get('value') for s in sizes):
                                sizes = [normstring(s.get('value')) for s in sizes]
                            else:
                                sizes = None
                        else:
                            sizes = None
                    if sizes and not all(isinstance(s, basestring) for s in sizes):
                        sizes = None

                    colors = obj['colors'].get('colors') if 'colors' in obj else None
                    if colors is not None and not isinstance(colors, list):
                        colors = None
                    if colors and not all(isinstance(c, basestring) for c in colors):
                        if all(isinstance(c, dict) for c in colors):
                            '''
[{u'colorized_image_url': u'saks/0400087614067', u'is_sold_out_waitlistable': False, u'label': u'PINK', u'value': u'', u'color_id': 0, u'is_value_an_image': False}]
                            '''
                            # ref: http://www.saksfifthavenue.com/main/ProductDetail.jsp?PRODUCT<>prd_id=845524446857648
                            if all(c.get('label') for c in colors):
                                colors = [normstring(c.get('label')) for c in colors]
                            else:
                                colors = None
                        else:
                            colors = None
                    if colors and not all(isinstance(c, basestring) for c in colors):
                        colors = None


                    mlrs = {
                        'url_canonical': url_canonical,
                        'product_id': obj.get('product_id'),
                        'product_code': obj.get('product_code'),
                        'descr': descr,
                        'descr_short': obj.get('short_description'),
                        'features': features,
                        'colors': colors,
                        'brand': obj['brand_name'].get('label') if 'brand_name' in obj else None,
                        #'brandid': obj.get('brandid'),
                        #'brandcatid': obj.get('brandcatid'),
                        #'breadcrumb': re.split('\s+>\s+', obj.get('pageName') or '') or None,
                        'sold_out': sold_out,
                        'instock': not sold_out if sold_out is not None else None,
                        'name': name,
                        #'pagetype': obj.get('pagetype'),
                        'price': dehtmlify(obj['price'].get('list_price')) if 'price' in obj else None,
                        'sale_price': dehtmlify(obj['price'].get('sale_price')) if 'price' in obj else None,
                        'sizes': sizes,
                        'skus': skus,
                        'upc': skus[0].get('upc') if skus and len(skus) == 1 else None,
                    }
                except Exception as e:
                    traceback.print_exc()
        return mlrs


if __name__ == '__main__':

    url = 'http://saks.example/'
    # test no-op
    filepath = 'www.dermstore.com-product_Lipstick_31136.htm.gz'
    # test 1 product
    filepath = 'www.saksfifthavenue.com-main-ProductDetail.jsp-folder_id-2534374306418242-prd_id-845524446849942.gz'

    with gzip.open(filepath) as f:
        html = f.read()

    products = ProductsSaks.from_html(url, html)
    print products
