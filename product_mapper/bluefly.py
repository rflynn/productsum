# ex: set ts=4 et:
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import execjs
import gzip
import json
from pprint import pprint
import re
import time
import traceback

from datavocabulary import DataVocabulary
from htmlmetadata import HTMLMetadata
from og import OG
from product import Product, ProductMapResultPage, ProductMapResult
from util import nth, xstrip, normstring, dehtmlify


def script_dataDictionary(soup):
    '''
    <script type="text/javascript">
        var dataDictionary = {
            pageType: 'pdp',
            pageName: 'A. Testoni brown leather chelsea boots',
            categoryId: 'cat10024',
            productId: '357144202',
            isMarketplace: false,
            brandType: 'Designer',
            color: 'Brown',
            brand: 'A. Testoni',
            fulfiller: 'QL',
            intFufiller: 'PB',
            intShippingSupport: 'YES',
            euroShippingSupported: ''
        };
    </script>
    '''
    script = soup.find(lambda tag: tag.name == 'script' and 'dataDictionary' in tag.text)
    data = {}
    if script:
        m = re.search('{.*}', script.text, re.DOTALL)
        if m:
            objstr = m.group(0)
            o = execjs.eval(objstr)
            data = {
                'product_id': o.get('productId'),
                'category_id': o.get('categoryId'),
                'brand': o.get('brand'),
                'brand_type': o.get('brandType'),
                'color': o.get('color'),
                'name': o.get('pageName'),
                'is_marketplace': o.get('isMarketplace'), # ?
            }
    return data

def script_gaProduct(soup):
    '''
    <script type="text/javascript">
        var gaProduct = {
          'id': '357144202',
          'name': '357144202' + ' ' + 'A. Testoni' + ' ' + 'brown leather chelsea boots',
          'category': '',
          'brand': 'A. Testoni',
          'variant': 'Brown',
          'position': 1,
          'dimension1': 'BlueflyProduct'
        };
    </script>
    '''
    script = soup.find(lambda tag: tag.name == 'script' and 'var gaProduct' in tag.text)
    data = {}
    if script:
        m = re.search('{.*}', script.text, re.DOTALL)
        if m:
            objstr = m.group(0)
            o = execjs.eval(objstr)
            data = {
                'product_id': o.get('id') or None,
                'category': o.get('category') or None,
                'name': o.get('name') or None,
                'brand': o.get('brand') or None,
                'position': o.get('position') or None,
                'variant': o.get('variant') or None,
            }
    return data


def custom_skus_ugh(soup):
    '''
    <div class="pdpSizeListContainer">
        <span onclick="showPdpPrices(891954528678)" class="pdpSizeTile na" data-skuid="891954528678">
            8
        </span>
        <span onclick="showPdpPrices(891954528685)" class="pdpSizeTile na" data-skuid="891954528685">
            8.5
        </span>
        <span onclick="showPdpPrices(891954528692)" class="pdpSizeTile available" data-skuid="891954528692">
            9
        </span>
    '''
    skus = [
    ]
    sizelist = soup.find('div', {'class': 'pdpSizeListContainer'})
    if sizelist:
        prices = sizelist.findAll(name='span', class_=lambda txt: 'pdpSizeTile' in txt)
        skus = [
            {'sku': p.get('data-skuid'),
             'size': p.text.strip() if p.text else None,
             'availability': 'available' in p.get('class') if p.get('class') else None
            }  for p in prices]
    return skus


def custom_breadcrumb_ugh(soup):
    '''
    <div class="pdpBreadCrumbsContainer">
        <a href="/" class="taxonomyLink">Home</a>
        <span class="taxonomySeperator">/</span>

        <a href="/designer-mens" class="taxonomyLink">Men</a>
        <span class="taxonomySeperator">/</span>

        <a href="/mens/designer-shoes" class="taxonomyLink">Shoes</a>
        <span class="taxonomySeperator">/</span>
    '''
    br = soup.findAll('a', class_='taxonomyLink')
    if br:
        try:
            return [b.text for b in br if b and b.text]
        except:
            traceback.print_exc()
    return None


def bluefly_custom(soup):
    '''
    <div class="pdp-list-price">
        $346.50
    </div>
    '''
    data = {}
    div = soup.find('div', {'class': 'pdp-list-price'})
    if div:
        m = re.search('\$([0-9,]+(?:\.\d+)?)', div.text, re.DOTALL)
        if m:
            data = {
                'price': m.groups(0)[0],
                'currency': 'USD'
            }
    '''
    <span class="pdpBulletContainer">
        <span class="pdpBulletHeaderText">
                color:
        </span>
        <span class="pdpBulletContentsText">
                Brown
        </span>
    </span>
    <span class="pdpBulletContainer">
        <span class="pdpBulletContentsText">
                Calfskin leather upper
        </span>
    </span>
    '''
    bulcon = soup.findAll('span', class_='pdpBulletContainer')
    if bulcon:
        data['features'] = [node.text for node in bulcon]

    '''
    <meta itemprop="category" content='Shoes'>
    '''
    tag = soup.find('meta', itemprop='category')
    if tag:
        data['category'] = tag.get('content')

    '''
    <div class="skuPriceInfo" id="891954528692">
    '''
    tag = soup.find('div', class_='skuPriceInfo')
    if tag:
        data['sku'] = tag.get('id')

    data['skus'] = custom_skus_ugh(soup)

    data['breadcrumb'] = custom_breadcrumb_ugh(soup)

    return data


class ProductBluefly(object):
    def __init__(self, id=None, url=None,
                 in_stock=None,
                 brand=None, brand_type=None, 
                 category=None, category_id=None, bread_crumb=None,
                 price=None, currency=None,
                 name=None, title=None, descr=None,
                 color=None, variant=None,
                 img_url=None,
                 features=None, size=None, available_sizes=None,
                 skus=None):

        assert isinstance(id, (type(None), basestring))
        assert isinstance(url, (type(None), basestring))
        assert isinstance(in_stock, (type(None), bool))
        assert isinstance(brand, (type(None), basestring))
        assert isinstance(brand_type, (type(None), basestring))
        assert isinstance(category, (type(None), basestring))
        assert isinstance(category_id, (type(None), basestring))
        assert isinstance(bread_crumb, (type(None), list))
        assert isinstance(name, (type(None), basestring))
        assert isinstance(title, (type(None), basestring))
        assert isinstance(descr, (type(None), basestring))
        assert isinstance(img_url, (type(None), basestring))
        assert isinstance(features, (type(None), list))
        assert isinstance(size, (type(None), list))
        assert isinstance(available_sizes, (type(None), list))
        assert isinstance(skus, (type(None), list))

        self.id = id
        self.url = url
        self.in_stock = in_stock
        self.img_url = img_url
        self.brand = brand
        self.brand_type = brand_type
        self.bread_crumb = bread_crumb
        self.category = category
        self.category_id = category_id
        self.price = price
        self.currency = currency
        self.name = normstring(name)
        self.title = title
        self.descr = descr
        self.features = features
        self.color = color
        self.variant = variant
        self.size = size
        self.available_sizes = available_sizes
        self.skus = skus

        if self.features:
            self.features = [normstring(f) for f in self.features]

    def __repr__(self):
        return ('''ProductBluefly(
    id...............%s
    url..............%s
    in_stock.........%s
    brand............%s
    brand_type.......%s
    category.........%s
    category_id......%s
    price............%s
    currency.........%s
    name.............%s
    title............%s
    descr............%s
    color............%s
    variant..........%s
    features.........%s
    size.............%s
    available_sizes..%s
    skus.............%s
    img_url..........%s
)''' % (self.id,
       self.url,
       self.in_stock,
       self.brand,
       self.brand_type,
       self.category,
       self.category_id,
       self.price,
       self.currency,
       self.name,
       self.title,
       self.descr,
       self.color,
       self.variant,
       self.features,
       self.size,
       self.available_sizes,
       self.skus,
       self.img_url)).encode('utf8')

    def to_product(self):

        return Product(
            merchant_slug='bluefly',
            url_canonical=self.url,
            merchant_sku=str(self.id),
            name=self.name,
            title=self.title,
            descr=self.descr,
            in_stock=self.in_stock,
            stock_level=None,
            merchant_product_obj=self,
            price=self.price,
            sale_price=None,
            currency=self.currency,
            category=self.category,
            brand=self.brand,
            bread_crumb=self.bread_crumb,
            features=self.features,
            color=self.color,
            available_colors=None,
            size=self.size,
            available_sizes=self.available_sizes,
            img_urls=[self.img_url] if self.img_url else None
        )


class ProductsBluefly(object):

    @staticmethod
    def from_html(url, html):

        starttime = time.time()

        soup = BeautifulSoup(html)

        meta = HTMLMetadata.do_html_metadata(soup)
        og = OG.get_og(soup)
        dv = DataVocabulary.get_schema_product(html)
        dd = script_dataDictionary(soup)
        gaprod = script_gaProduct(soup)
        custom = bluefly_custom(soup)

        # TODO: mult-product support? haven't seen it yet...
        dv = dv[0] if dv else {}

        signals = {
            'meta':   meta,
            'og':     og,
            'dv':     dv,
            'dd':     dd,
            'gaprod': gaprod,
            'custom': custom,
        }
        #pprint(signals)

        products = []

        if (og.get('type') == 'product'
            or dd.get('productId')
            or gaprod.get('id')):

            p = ProductBluefly(
                id=(dd.get('product_id')
                    or gaprod.get('product_id')
                    or custom.get('sku')
                    or None),
                url=og.get('url') or url or None,
                in_stock=any(s.get('availability')
                                for s in custom['skus'])
                                    if custom['skus'] else None,
                bread_crumb=custom.get('breadcrumb') or None,
                category=(nth(dv.get('category'), 0)
                            or gaprod.get('category')
                            or custom.get('category') or None),
                category_id=dd.get('categoryId') or None,
                brand=(xstrip(nth(dv.get(u'brand'), 0))
                        or dd.get('brand')
                        or gaprod.get('brand')
                        or None),
                brand_type=dd.get('brand_type') or None,
                price=custom.get('price') or None,
                currency=custom.get('currency') or None,
                name=(og.get('name')
                        or dd.get('pageName')
                        or nth(dv.get('name'), 0)
                        or meta.get('title')
                        or meta.get('description') or None),
                title=(og.get('title')
                        or meta.get('title') or None),
                descr=(og.get('description')
                        or meta.get('description') or None),
                features=dd.get('features') or custom.get('features') or None,
                color=dd.get('color') or None,
                variant=gaprod.get('variant') or None,
                size=None,
                available_sizes=[s.get('size')
                                    for s in custom['skus']]
                                        if custom['skus'] else None,
                skus=custom['skus'],
                img_url=og.get('image') or None
            )
            products.append(p)

        realproducts = [p.to_product() for p in products]

        page = ProductMapResultPage(
                 merchant_slug='bluefly',
                 url=url,
                 size=len(html),
                 proctime = time.time() - starttime,
                 signals=signals)

        return ProductMapResult(page=page,
                                products=realproducts)
    


if __name__ == '__main__':

    url = 'http://www.bluefly.com/a-testoni-brown-leather-chelsea-boots/p/357144202/detail.fly'
    filepath = 'test/www.bluefly.com-a-testoni-brown-leather-chelsea-boots-p-357144202-detail.fly.gz'

    with gzip.open(filepath) as f:
        html = f.read()

    products = ProductsBluefly.from_html(url, html)

    print products
