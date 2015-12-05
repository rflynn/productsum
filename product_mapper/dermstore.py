# ex: set ts=4 et:

from BeautifulSoup import BeautifulSoup
import execjs
import gzip
import json
from pprint import pprint
import re

from htmlmetadata import HTMLMetadata
from og import OG
from product import Product
from schemaorg import SchemaOrg
from tealium import Tealium
from util import nth, xstrip, dehtmlify


class ProductDermstore(object):
    def __init__(self, id=None, url=None,
                 currency=None, current_price=None,
                 brand=None, bread_crumb=None,
                 in_stock=None,
                 name=None, title=None, descr=None,
                 features=None, color=None, colors=None, sizes=None,
                 img_urls=None):

        self.id = id
        self.url = url
        self.currency = currency
        self.current_price = current_price
        self.brand = brand
        self.bread_crumb = bread_crumb
        self.in_stock = in_stock
        self.name = name
        self.title = title
        self.descr = descr
        self.features = features
        self.color = color
        self.colors = colors
        self.sizes = sizes
        self.img_urls = img_urls

        if colors and not color:
            m = [c for c in colors if c and c in name]
            if len(m) == 1:
                self.color = m[0]

        if img_urls and isinstance(img_urls, basestring):
            self.img_urls = [img_urls]

        if in_stock:
            if in_stock in ('instock', 'in stock'):
                self.in_stock = True
            elif in_stock in ('oos',): # out of stock
                self.in_stock = False
            else:
                self.in_stock = None

    def __repr__(self):
        return '''ProductDermstore:
    id...............%s
    url..............%s
    currency.........%s
    current_price....%s
    in_stock.........%s
    brand............%s
    bread_crumb......%s
    name.............%s
    title............%s
    descr............%s
    features.........%s
    color............%s
    colors...........%s
    sizes............%s
    img_urls.........%s
''' % (self.id,
       self.url,
       self.currency,
       self.current_price,
       self.in_stock,
       self.brand,
       self.bread_crumb,
       self.name,
       self.title,
       self.descr,
       self.features,
       self.color,
       self.colors,
       self.sizes,
       self.img_urls)

    def to_product(self):
        return Product(
            merchant_slug='dermstore',
            canonical_url=self.url,
            sku=str(self.id),
            sale_price=None,
            price=self.current_price,
            currency=self.currency,
            brand=self.brand,
            bread_crumb=self.brand,
            in_stock=self.in_stock,
            stock_level=None,
            name=self.name,
            title=self.title,
            descr=self.descr,
            features=self.features,
            color=self.color,
            available_colors=list(self.colors),
            size=None,
            available_sizes=list(self.sizes),
            img_urls=self.img_urls
        )


class ProductsDermstore(object):

    @staticmethod
    def script_dataLayer(soup):
        '''
        a js obj is pushed to the dataLayer
        '''
        data = {}
        script = soup.find(lambda tag: tag.name == 'script' and 'dataLayer.push(' in tag.text)
        if script:
            m = re.search('{.*}', script.text, re.DOTALL)
            if m:
                objstr = m.group(0)
                #print objstr
                obj = execjs.eval(objstr)
                #pprint(obj)
                data = {
                    'prodid': obj.get('prodid'),
                    'pagetype': obj.get('pagetype'),
                    'name': obj.get('pname') or None,
                    'current_price': obj.get('pvalue') or None,
                    'brand_id': obj.get('brandid'),
                    'brand_cat_id': obj.get('brandcatid'),
                }
        return data

    @staticmethod
    def custom_itemprop(soup):
        '''
        itemprops scattered around...
        '''
        data = {}
        tags = soup.findAll(lambda tag: tag.get('itemprop'))
        if tags:
            #pprint(tags)
            ip = {t.get('itemprop'): t.text or t.get('content') for t in tags}
            #pprint(ip)
            data = {
                'brand': ip.get('brand') or None,
                'description': ip.get('description') or None,
                'name': ip.get('name') or None,
                'url': ip.get('url') or None,
            }
        return data

    @staticmethod
    def custom_breadcrumbs(soup):
        '''
        ugh, breadcrumbs from html...
        '''
        try:
            return [t.text for t in soup.find('ol', {'class': 'breadcrumb'}).findAll('li')]
        except:
            return None

    @staticmethod
    def custom_colors(soup):
        '''
        ugh, breadcrumbs from html...
        '''
        try:
            return [t.get('alt') for t in soup.find('div', {'id': 'color-swatches'}).findAll('img')]
        except:
            return None


    @staticmethod
    def from_html(url, html):

        soup = BeautifulSoup(html)

        # standard shit
        sp = SchemaOrg.get_schema_product(html)
        og = OG.get_og(html)
        meta = HTMLMetadata.do_html_metadata(soup)

        # custom
        dl = ProductsDermstore.script_dataLayer(soup)
        ip = ProductsDermstore.custom_itemprop(soup)
        br = ProductsDermstore.custom_breadcrumbs(soup)
        colors = ProductsDermstore.custom_colors(soup)

        pprint(sp)
        pprint(og)
        pprint(meta)
        pprint(dl)
        pprint(ip)
        pprint(colors)

        products = []

        # NOTE: on the test product at least og[type] is 'website', oh well...

        if (og.get('type') == u'product'
            or dl.get('pagetype') == u'product'):

            p = ProductDermstore(
                    id=dl.get('prodid') or None,
                    url=url or og.get('url') or None,
                    currency=og.get('price:currency') or None,
                    current_price=og.get('price:amount') or dl.get('current_price') or None,
                    brand=ip.get('brand') or dl.get('brand') or None,
                    bread_crumb=br or None,
                    name=ip.get('name') or dl.get('name') or og.get('title') or None,
                    title=meta.get('title') or None,
                    descr=ip.get('description') or meta.get('description') or None,
                    in_stock=og.get('availability'),
                    features=None,
                    color=dl.get('color') or None,
                    colors=colors or None,
                    sizes=None,
                    img_urls=og.get('image') or None
            )
            products.append(p)

        return products


if __name__ == '__main__':

    url = 'http://www.dermstore.com/product_Lipstick_31136.htm'
    filepath = 'www.dermstore.com-product_Lipstick_31136.htm.gz'
    filepath = 'www.dermstore.com-product_Hair+Straightening+Ceramic+Brush_63616.htm-sold-out.gz'
    with gzip.open(filepath) as f:
        html = f.read()

    products = ProductsDermstore.from_html(url, html)
    pprint(products)

    #for p in products:
    #    print p.to_product()


