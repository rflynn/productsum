# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from dermstore.com to zero or more products
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


class ProductDermstore(object):
    def __init__(self, prodid=None, canonical_url=None,
                 stocklevel=None, instock=None,
                 price=None, currency=None,
                 bread_crumb=None, brand=None,
                 name=None, title=None, descr=None,
                 features=None, size=None,
                 img_url=None):

        assert prodid is None or isinstance(prodid, basestring)
        assert canonical_url is None or isinstance(canonical_url, basestring)
        assert stocklevel is None or isinstance(stocklevel, basestring)
        assert instock is None or isinstance(instock, bool)
        assert brand is None or isinstance(brand, basestring)
        assert name is None or isinstance(name, basestring)
        assert title is None or isinstance(title, basestring)
        assert descr is None or isinstance(descr, basestring)
        assert features is None or isinstance(features, list)
        assert price is None or isinstance(price, basestring)
        assert currency is None or isinstance(currency, basestring)
        assert bread_crumb is None or isinstance(bread_crumb, list)
        assert features is None or isinstance(features, list)
        assert size is None or isinstance(size, basestring)
        assert img_url is None or isinstance(img_url, basestring)

        self.prodid = prodid
        self.canonical_url = canonical_url
        self.stocklevel = stocklevel
        self.instock = instock
        self.price = price
        self.currency = currency
        self.bread_crumb = bread_crumb
        self.brand = normstring(brand)
        self.name = normstring(name)
        self.title = normstring(title)
        self.descr = descr
        self.features = features
        self.size = size
        self.img_url = img_url

        # fixups
        self.descr = self.descr.replace('&sol;', '/')

        # normalize bread_crumb
        if self.bread_crumb is not None:
            self.bread_crumb = [normstring(x) for x in self.bread_crumb if x]

    def __repr__(self):
        return '''ProductDermstore(
    prodid........%s
    url...........%s
    instock.......%s
    stocklevel....%s
    price.........%s
    currency......%s
    brand.........%s
    bread_crumb...%s
    name..........%s
    title.........%s
    descr.........%s
    features......%s
    size..........%s
    img_url.......%s
)''' % (self.prodid, self.canonical_url,
       self.instock, self.stocklevel,
       self.price, self.currency,
       self.brand, self.bread_crumb,
       self.name, self.title, self.descr,
       self.features, self.size,
       self.img_url)

    def to_product(self):

        category = None
        if self.bread_crumb:
            category = self.bread_crumb[-1]

        return Product(
            merchant_slug='dermstore',
            url_canonical=self.canonical_url,
            merchant_sku=str(self.prodid),
            merchant_product_obj=self,
            price=self.price,
            sale_price=None,
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
            color=None,
            available_colors=None,
            size=self.size,
            available_sizes=None,
            img_urls=[self.img_url] if self.img_url else None
        )




class ProductsDermstore(object):

    @staticmethod
    def from_html(url, html):

        starttime = time.time()

        products = []

        sp = SchemaOrg.get_schema_product(html)
        og = OG.get_og(html)
        soup = BeautifulSoup(html)
        meta = HTMLMetadata.do_html_metadata(soup)
        utag = Tealium.get_utag_data(soup)
        dl = ProductsDermstore.get_dataLayer(soup)
        custom = ProductsDermstore.get_custom(soup, og)

        sp = sp[0] if sp else {}

        signals = {
            'sp':   SchemaOrg.to_json(sp),
            'og':   og,
            'meta': meta,
            'dl':   dl,
            'custom': custom,
        }
        #pprint(signals)

        # is there one or more product on the page?
        if (sp
            or dl.get('pagetype') == 'product'
            or og.get('type') == u'product'):

            name = (nth(sp.get('name'), 0)
                or custom.get('name')
                or dl.get('name')
                or nth(utag.get(u'product_name'), 0)
                or og.get('title')
                or meta.get('title') or None)

            p = ProductDermstore(
                prodid=nth(utag.get('product_id'), 0) or dl.get('id'),
                canonical_url=custom.get('url_canonical') or og.get('url') or url,
                stocklevel=nth(utag.get('stock_level'), 0),
                instock=xboolstr(nth(utag.get('product_available'), 0)) or og.get('availability') in ('instock',),
                price=nth(utag.get('product_price'), 0) or og.get('price:amount') or None,
                currency=utag.get('order_currency_code') or og.get('price:currency') or None,
                bread_crumb=dl.get('breadcrumb') or None,
                brand=nth(sp.get(u'brand'), 0) or og.get('brand') or dl.get('brand') or custom.get('brand') or None,
                name=name,
                title=og.get('title') or meta.get('title') or None,
                descr=maybe_join(' ', sp.get('description')) or custom.get('descr') or og.get('description') or meta.get('description') or None,
                features=custom.get('features') or None,
                size=custom.get('size') or None,
                img_url=og.get('image') or None,
            )
            products.append(p)

        realproducts = [p.to_product() for p in products]

        page = ProductMapResultPage(
                 merchant_slug='dermstore',
                 url=url,
                 size=len(html),
                 proctime = time.time() - starttime,
                 signals=signals)

        return ProductMapResult(page=page,
                                products=realproducts)


    @staticmethod
    def get_dataLayer(soup):
        data = {}
        '''
<script>
dataLayer.push({
    'event': 'ds.ready',
    'visitorSource': 'walkin',
    'visitorExistingCustomer': 'false',
    'pagetype': 'product',
    'siteType': 'Desktop',
    'pageName': 'Home > Skin Care > Cleansers and Exfoliators > Glytone > Mild Gel Wash',
    'prodid': '363',
    'brandid': '100043',
    'brandcatid': '500014',
    'pname': 'Mild Gel Wash',
    'pvalue': '32.00',
    'ecommerce':  {
    'detail': {
        'actionField': {
            'list': 'PDP_Skin_Care'
        },
        'products':[{
            'id': '363',
            'creative': 'detailview'
        }]
    } ,
    'impressions':[{
        'id': '64062',
        'position': '1',
        'creative': 'tile',
        'list': 'PDP_Skin_Care'
    }]
    }
});
</script>
        '''
        url_canonical = None
        tag = soup.find('script', text=lambda txt: txt and 'dataLayer.push(' in txt)
        if tag:
            m = re.search('{.*}', tag.text, re.DOTALL)
            if m:
                try:
                    objstr = m.group(0)
                    obj = execjs.eval(objstr)
                    data = {
                        'brand': None,
                        'brandid': obj.get('brandid'),
                        'brandcatid': obj.get('brandcatid'),
                        'breadcrumb': re.split('\s+>\s+', obj.get('pageName') or '') or None,
                        'id': obj.get('prodid'),
                        'name': obj.get('pname'),
                        'pagetype': obj.get('pagetype'),
                        'price': obj.get('pvalue'),
                    }
                except Exception as e:
                    traceback.print_exc()
        return data

    @staticmethod
    def get_custom(soup, og):

        # url
        url_canonical = None
        tag = soup.find('link', rel='canonical', href=True)
        if tag:
            url_canonical = tag.get('href')
        if not url_canonical:
            tag = soup.find('meta', itemprop='url', content=True)
            if tag:
                url_canonical = tag.get('content')
        if not url_canonical:
            url_canonical = og.get('url')

        # name
        name = None
        tag = soup.find(itemprop='name')
        if tag and hasattr(tag, 'text'):
            name = xstrip(normstring(tag.text))

        # an actual description
        descr = None
        tag = soup.find(itemprop='description')
        if tag:
            descr = tag.text
        # even better description...
        tag = soup.find('div', class_='panel-body')
        if tag:
            descr = xstrip(normstring(tag.text))
        if descr.endswith('Read More >'):
            descr = descr[:-11]

        # brand
        brand = None
        tag = soup.find('span', {'class':'prodDesignerName'})
        if tag:
            brand = normstring(dehtmlify(tag.text))

        # features
        features = None
        tag = soup.find(id='collapseGlance')
        if tag:
            features = [normstring(t.text.replace('\n',' '))
                            for t in tag.findAll(class_='prd') or []]

        # sizes are a suffix on name by convention
        # e.g. "Foo Bar Cleanser (6.4fl oz.)"
        size = None
        if name:
            namepatterns = [
                r'([0-9]+(?:[.][0-9]+)?\s*fl[.]?\s*oz[.]?)', # "6.7 fl oz."
                r'([0-9]+(?:[.][0-9]+)?\s*oz[.]?)',          # "0.15 oz."
                r'([0-9]+(?:[.][0-9]+)?\s*count)',           # "60count"
                r'([0-9]+(?:[.][0-9]+)?\s*capsules)',        # "50capsules"
                r'([0-9]+(?:[.][0-9]+)?\s*ml.)',             # "240ml."
                r'\((.*)\)$',                                # last resort: anything between (...)
            ]
            for p in namepatterns:
                m = re.search(p, name, re.I)
                if m:
                    size = m.groups(0)[0]
                    break

        data = {
            'url_canonical': url_canonical,
            'brand': brand,
            'name': name,
            'descr': descr,
            'features': features,
            'size': size,
        }
        return data


if __name__ == '__main__':

    url = 'http://dermstore.example/'
    filepath = 'www.dermstore.com-product_Mild+Gel+Wash_363.htm.gz'
    filepath = 'www.dermstore.com-product_Hair+Straightening+Ceramic+Brush_63616.htm-sold-out.gz'
    filepath = 'www.dermstore.com-product_Lipstick_31136.htm.gz'

    with gzip.open(filepath) as f:
        html = f.read()

    products = ProductsDermstore.from_html(url, html)

    print products
