# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from net-a-porter.com to zero or more products
'''

from bs4 import BeautifulSoup
from pprint import pprint
import re
import time
import traceback
from urlparse import urljoin

from htmlmetadata import HTMLMetadata
from og import OG
from product import Product, ProductMapResultPage, ProductMapResult
from schemaorg import SchemaOrg
from tealium import Tealium
from util import nth, xboolstr, normstring, xstrip


class ProductNetaPorter(object):
    VERSION = 0
    def __init__(self, id=None, canonical_url=None,
                 stocklevel=None, instock=None,
                 price=None, currency=None,
                 brand=None,
                 name=None, title=None, descr=None,
                 features=None,
                 img_url=None,
                 bread_crumb=None):

        assert id is None or isinstance(id, basestring)
        assert canonical_url is None or isinstance(canonical_url, basestring)
        assert stocklevel is None or isinstance(stocklevel, basestring)
        assert instock is None or isinstance(instock, bool)
        assert price is None or isinstance(price, float)
        assert currency is None or isinstance(currency, basestring)
        assert brand is None or isinstance(brand, basestring)
        assert name is None or isinstance(name, basestring)
        assert title is None or isinstance(title, basestring)
        assert descr is None or isinstance(descr, basestring)
        assert features is None or isinstance(features, list)
        assert img_url is None or isinstance(img_url, basestring)
        assert bread_crumb is None or isinstance(bread_crumb, list)

        self.id = id
        self.canonical_url = canonical_url
        self.stocklevel = stocklevel
        self.instock = instock
        self.price = price
        self.currency = currency
        self.brand = brand
        self.name = normstring(name)
        self.title = title
        self.descr = descr
        self.features = features
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
    price.......%s
    currency....%s
    name........%s
    title.......%s
    descr.......%s
    features....%s
    img_url.....%s
    bread_crumb.%s
)''' % (self.id, self.canonical_url,
        self.instock, self.stocklevel,
        self.brand,
        self.price, self.currency,
        self.name, self.title, self.descr,
        self.features,
        self.img_url,
        self.bread_crumb)

    def to_product(self):
        return Product(
            merchant_slug='netaporter',
            url_canonical=self.canonical_url,
            merchant_sku=self.id,
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
            features=self.features,
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

        soup = BeautifulSoup(html)
        meta = HTMLMetadata.do_html_metadata(soup)
        sp = SchemaOrg.get_schema_product(html)
        og = OG.get_og(soup)
        utag = Tealium.get_utag_data(soup)
        # TODO: consolidate this mess...
        pd = ProductsNetaPorter.do_meta_product_data(soup)
        ba = ProductsNetaPorter.do_body_attrs(soup)
        mi = ProductsNetaPorter.get_meta_itemprop(soup)
        pa = ProductsNetaPorter.get_product_attrs(soup)
        custom = ProductsNetaPorter.get_custom(soup)
        #pprint(utag)

        sp = sp[0] if sp else {}

        signals = {
            'meta': meta,
            'sp':   SchemaOrg.to_json(sp),
            'og':   og,
            'utag': utag,
            'pd':   pd,
            'ba':   ba,
            'mi':   mi,
            'pa':   pa,
            'custom': custom,
        }
        #pprint(signals)

        products = []

        prodid = (pa.get('prodid')
                    or nth(sp.get('id'), 0)
                    or pd.get('id')
                    or mi.get('product_id') or None)

        if prodid:

            p = ProductNetaPorter(
                id=prodid,
                canonical_url=nth(sp.get('url'), 0) or url,
                stocklevel=None,
                instock=pd.get('availability'),
                price=pd.get('price') or None,
                currency=ba.get('currency') or None,
                brand=(pa.get('brand')
                        or pd.get('brand')
                        or custom.get('brand') or None),
                name=(nth(sp.get('name'), 0)
                        or og.get('title')
                        or mi.get('name')
                        or meta.get('title')
                        or None),
                title=meta.get('title') or None,
                descr=(custom.get('descr')
                        or meta.get('description')),
                features=custom.get('features') or None,
                img_url=(nth(sp.get('image'), 0)
                            or mi.get('image') or None),
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
            d = {m.get('itemprop'): m.get('content')
                    for m in soup.findAll('meta', itemprop=True)}
            data = {
                'bread_crumb': re.split('\s+/\s+', d['category']) if 'category' in d else None,
                'name': xstrip(d['name']) if 'name' in d else None,
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
        body = soup.find('body') or {}
        data = {
            'country': body.get('data-country'),
            'currency': body.get('data-currency-code'),
            'language': body.get('data-language'),
            'region': body.get('data-region'),
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
        sold_out = None
        available = None
        brand_name = None
        bread_crumb = None
        price = None
        name = None
        if attrs.get('product-data') == 'product-data':
            print 'not product-data, got %s' % (attrs.get('product-data'),)
        else:
            try:
                sold_out = xboolstr(attrs.get('data-sold-out'))
                available = not sold_out if sold_out is not None else None
                brand_name = attrs.get('data-designer-name').replace('_', ' ') if 'data-designer-name' in attrs else None
                bread_crumb = re.split('\s*/\s*', attrs.get('data-breadcrumb-names').strip()) if 'data-breadcrumb-names' in attrs else None
                price = float(attrs.get('data-price')) / 100 if 'data-price' in attrs else None
                name = attrs.get('data-analytics-key').strip() if 'data-analytics-key' in attrs else None
            except:
                traceback.print_exc()

            data = {
                'id': attrs.get('data-pid') or None,
                'availability': available,
                'brand': brand_name,
                'bread_crumb': bread_crumb,
                'price': price,
                'name': name,
            }
        return data

    @staticmethod
    def get_product_attrs(soup):
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

        p = soup.find(
                {
                    'data-designer-name': True,
                    'itemtype': 'http://schema.org/Product',
                }) or {}

        return {
            'prodid': p.get('data-pid'),
            'brand': p.get('data-designer-name'),
            'breadcrumb': re.split(' / ', p.get('data-breadcrumb-keys') or ''),
        }


    @staticmethod
    def get_custom(soup):
        '''
        <h1 itemprop="brand" itemscope itemtype="http://schema.org/Brand">
            <a class="designer-name" href="/Shop/Designers/Jimmy_Choo" itemprop="url">
                <span itemprop="name">Jimmy Choo</span>
            </a>
        </h1>
        '''
        brand = None
        tag = soup.find(itemprop='brand',
                        itemtype='http://schema.org/Brand')
        if tag:
            name = tag.find(itemprop='name')
            if name and hasattr(name, 'text'):
                brand = name.text

        descr = None
        features = None
        '''
        <widget-show-hide id="accordion-2" class="editors-notes js-accordion-tab accordion-tab" open name="Editor's Notes">
            <div class="show-hide-title heading">
                EDITORS&#x27; NOTES
            </div>
            <div class="show-hide-content">
                <div class="wrapper">
                    <p>
                    Jimmy Choo's 'Lucy' pumps have been crafted in Italy from gleaming silver leather - a particularly versatile hue. This classic pair is designed with flattering d'Orsay cutouts and a slim ankle strap.<br><br>Shown here with: <a href="/us/en/product/582413">Anya Hindmarch Clutch</a>, <a href="/us/en/product/608807">Mary Katrantzou Dress</a>, <a href="/us/en/product/573377">Bottega Veneta Rings</a>, <a href="/us/en/product/646519">Pamela Love Cuff</a>, <a href="/us/en/product/571681">Arme De L'Amour Ring</a>, <a href="/us/en/product/608087">Gucci Ring</a>, <a href="/us/en/product/571678">Arme De L'Amour Bracelet</a>.
                    </p>
                    <ul class="font-list-copy">
                        <li>- Heel measures approximately 100mm/ 4 inches</li>
                        <li>- Silver leather</li>
                        <li>- Buckle-fastening ankle strap</li>
                        <li>- Designer color: Steel</li>
                        <li>- Made in Italy</li>
                    </ul>
                </div>
            </div>
        </widget-show-hide>
        '''
        ed = soup.find('widget-show-hide')#{'class': lambda c: c and 'editors-notes' in c})
        if ed:
            p = ed.find('p')
            if p:
                descr = normstring(p.get_text())
            features = [re.sub('^[-]\s+', '', normstring(li.get_text()))
                            for li in ed.findAll('li')] or None

        return {
            'brand': brand,
            'descr': descr,
            'features': features,
        }

if __name__ == '__main__':

    import gzip

    url = 'http://www.net-a-porter.com/product/638211'
    filepath = 'test/www.net-a-porter.com-us-en-product-638211-christian_louboutin-so-kate-120-leather-pumps.gz'
    filepath = 'test/www.net-a-porter.com-us-en-product-638341-jimmy_choo-lucy-metallic-leather-pumps.gz'

    with gzip.open(filepath) as f:
        html = f.read()

    products = ProductsNetaPorter.from_html(url, html)
    print products
