# ex: set ts=4 et:

'''
map a document archived from neimanmarcus.com to zero or more products
'''

from BeautifulSoup import BeautifulSoup
import base64
import gzip
import json
import microdata
from pprint import pprint
import re
import requests
import time
from urlparse import urljoin
from yurl import URL

from htmlmetadata import HTMLMetadata
from og import OG
from product import Product, ProductMapResultPage, ProductMapResult
from schemaorg import SchemaOrg
from tealium import Tealium
from util import nth, xboolstr


class ProductNetaPorter(object):
    def __init__(self, id=None, canonical_url=None,
                 stocklevel=None, instock=None,
                 brand=None, name=None, title=None, descr=None,
                 price=None, currency=None,
                 img_url=None,
                 bread_crumb=None):

        assert id is None or isinstance(id, basestring)
        assert canonical_url is None or isinstance(canonical_url, basestring)
        assert stocklevel is None or isinstance(stocklevel, basestring)
        assert instock is None or isinstance(instock, bool)
        assert brand is None or isinstance(brand, basestring)
        assert name is None or isinstance(name, basestring)
        assert title is None or isinstance(title, basestring)
        assert descr is None or isinstance(descr, basestring)
        assert price is None or isinstance(price, float)
        assert currency is None or isinstance(currency, basestring)
        assert img_url is None or isinstance(img_url, basestring)
        assert bread_crumb is None or isinstance(bread_crumb, list)

        self.id = id
        self.canonical_url = canonical_url
        self.stocklevel = stocklevel
        self.instock = instock
        self.brand = brand
        self.name = re.sub('\s+', ' ', name.strip()) if name else None
        self.title = title
        self.descr = descr
        self.price = price
        self.currency = currency
        self.img_url = img_url
        self.bread_crumb = bread_crumb

        # fixup
        if self.img_url:
            # some img_urls are in the form '//foo'; ensure they're absolute
            self.img_url = urljoin(self.canonical_url, self.img_url)

    def __repr__(self):
        return '''ProductNetaPorter(
    id..........%s
    url.........%s
    instock.....%s
    stocklevel..%s
    brand.......%s
    name........%s
    title.......%s
    descr.......%s
    price.......%s
    currency....%s
    img_url.....%s
    bread_crumb.%s
)''' % (self.id, self.canonical_url,
        self.instock, self.stocklevel,
        self.brand, self.name, self.title, self.descr,
        self.price, self.currency,
        self.img_url,
        self.bread_crumb)

    def to_product(self):
        return Product(
            merchant_slug='netaporter',
            url_canonical=self.canonical_url,
            merchant_sku=str(self.id),
            merchant_product_obj=self,
            price=self.price,
            sale_price=None,
            currency=self.currency,
            category=self.bread_crumb[0] if self.bread_crumb else None,
            bread_crumb=self.bread_crumb,
            brand=self.brand,
            in_stock=self.instock,
            stock_level=None,
            name=self.name,
            title=self.title,
            descr=self.descr,
            features=None,
            color=None,
            available_colors=None,
            size=None,
            available_sizes=None,
            img_url=self.img_url,
            img_urls=[self.img_url] if self.img_url else None
        )


class ProductsNetaPorter(object):

    @staticmethod
    def from_html(url, html):

        starttime = time.time()

        sp = SchemaOrg.get_schema_product(html)
        og = OG.get_og(html)
        soup = BeautifulSoup(html)
        pd = ProductsNetaPorter.do_meta_product_data(soup)
        meta = HTMLMetadata.do_html_metadata(soup)
        utag = Tealium.get_utag_data(soup)
        ba = ProductsNetaPorter.do_body_attrs(soup)
        mi = ProductsNetaPorter.get_meta_itemprop(soup)

        #pprint(utag)

        sp = sp[0] if sp else {}

        signals = {
            'sp':   SchemaOrg.to_json(sp),
            'og':   og,
            'pd':   pd,
            'meta': meta,
            'ba':   ba,
            'mi':   mi,
        }

        #pprint(signals)

        products = []

        # is there one or more product on the page?
        if (sp
            or pd
            or mi.get('product_id')
            or og.get('type') == u'product'):
            # ok, there's 1+ product. extract them...

            p = ProductNetaPorter(
                id=(nth(sp.get('id'), 0)
                    or pd.get('id')
                    or mi.get('product_id') or None),
                canonical_url=nth(sp.get('url'), 0) or url,
                stocklevel=None,
                instock=pd.get('availability'),
                brand=pd.get('brand') or None,
                name=(nth(sp.get('name'), 0)
                        or og.get('title')
                        or mi.get('name')
                        or meta.get('title')
                        or None),
                title=meta.get('title') or None,
                descr=meta.get('description'),
                price=pd.get('price') or None,
                currency=ba.get('currency') or None,
                img_url=nth(sp.get('image'), 0) or mi.get('image') or None,
                bread_crumb=(pd.get('bread_crumb')
                                or mi.get('bread_crumb')
                                or None)
            )
            products.append(p)

        realproducts = [p.to_product() for p in products]

        page = ProductMapResultPage(
                    merchant_slug='netaporter',
                    url=url,
                    size=len(html),
                    proctime = time.time() - starttime,
                    signals=signals)

        return ProductMapResult(page=page,
                                products=realproducts)


    @staticmethod
    def get_meta_itemprop(soup):
        '''
            <meta itemprop="name" content="So Kate 120 leather pumps ">
            <meta itemprop="url" property="og:url" content="http://www.net-a-porter.com/product/638211">
            <meta itemprop="productID" content="638211">
            <meta itemprop="image" content="//cache.net-a-porter.com/images/products/638211/638211_in_pp.jpg">
        '''
        mi = soup.find('meta', itemprop=True)
        data = {}
        if mi:
            d = {m.attrMap.get('itemprop'): m.attrMap.get('content')
                    for m in soup.findAll('meta', itemprop=True)}
            data = {
                'bread_crumb': re.split('\s+/\s+', d['category']) if 'category' in d else None,
                'name': d['name'].strip() if 'name' in d else None,
                'product_id': d.get('productID') or None,
            }
        return data

    @staticmethod
    def do_body_attrs(soup):
        '''
        body class="US lang-en am responsive "
            data-region="am"
            data-language="en"
            data-country="US"
            data-currency-code="USD"
            data-currency-symbol="$"
            data-layout-id="responsive"
        '''
        b = soup.find('body')
        attrs = dict(b.attrs) if b else {}
        data = {
            'country': attrs.get('data-country'),
            'currency': attrs.get('data-currency-code'),
            'language': attrs.get('data-language'),
            'region': attrs.get('data-region'),
        }
        return data

    @staticmethod
    def do_meta_product_data(soup):
        pd = soup.find('meta', {'class': 'product-data'})
        attrs = dict(pd.attrs) if pd else {}
        '''
        meta class="product-data"
            data-designer-name="Christian_Louboutin"
            data-designer-id="72"
            data-analytics-key="So Kate 120 leather pumps "
            data-pid="638211"
            data-breadcrumb-names="Shoes / Pumps / High Heel"
            data-breadcrumb-keys="Shoes / Pumps / High_Heel"
            data-breadcrumb-ids="1283 / 6298 / 6358"
            data-sold-out="false"
            data-price-full="67500"
            data-price="67500"
        '''
        data = {}
        if attrs.get('product-data') == 'product-data':
            print 'not product-data, got %s' % (attrs.get('product-data'),)
        else:
            sold_out = xboolstr(attrs.get('data-sold-out'))
            available = not sold_out if sold_out is not None else None
            brand_name = attrs.get('data-designer-name').replace('_', ' ') if 'data-designer-name' in attrs else None
            bread_crumb = re.split('\s*/\s*', attrs.get('data-breadcrumb-names').strip()) if 'data-breadcrumb-names' in attrs else None
            price = float(attrs.get('data-price')) / 100 if 'data-price' in attrs else None
            name = attrs.get('data-analytics-key').strip() if 'data-analytics-key' in attrs else None
            data = {
                'id': attrs.get('data-pid'),
                'availability': available,
                'brand': brand_name,
                'bread_crumb': bread_crumb,
                'price': price,
                'name': name,
            }
        return data

    @staticmethod
    def do_schema_product(html):
        '''
        bergdorfgoodman uses schema.org metadata
        ref: http://schema.org/
        ref: https://en.wikipedia.org/wiki/Resource_Description_Framework
        '''

        '''
        div id="product" itemscope itemtype="http://schema.org/Product"
            data-designer-name="Christian_Louboutin"
            data-analytics-key="So Kate 120 leather pumps "
            data-pid="638211"
            data-breadcrumb-keys="Shoes / Pumps / High_Heel"
            data-feature-colours="true"
        '''

        product_uri = microdata.URI(u'http://schema.org/Product')
        instock_uri = microdata.URI(u'http://schema.org/InStock')

        sp = SchemaOrg.get_schema_product(html)

        sp = sp[0] if sp else {}

        data = {}
        if sp:
            p = sp
            if p.get(u'availability'):
                data['availability'] = p[u'availability'][0] == product_uri
            if p.get(u'brand'):
                if p[u'brand'][0].get(u'url'):
                    data['brand_url'] = p[u'brand'][0][u'url']
                if p[u'brand'][0].get(u'name'):
                    data['brand_name'] = p[u'brand'][0][u'name']
            if p.get(u'category'):
                data['category'] = re.split('\s*/\s*', p[u'category'][0])
            if p.get(u'image'):
                data['image_url'] = p[u'image'][0]
            if p.get(u'name'):
                data['name'] = p[u'name'][0]
            if p.get(u'productID'):
                data['id'] = p[u'productID'][0]
            if p.get(u'url'):
                data['url'] = p[u'url'][0]

        return data


if __name__ == '__main__':

    url = 'http://www.net-a-porter.com/product/638211'
    filepath = 'www.net-a-porter.com-us-en-product-638211-christian_louboutin-so-kate-120-leather-pumps.gz'

    with gzip.open(filepath) as f:
        html = f.read()
        products = ProductsNetaPorter.from_html(url, html)

    print products

