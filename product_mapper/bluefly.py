# ex: set ts=4 et:

from BeautifulSoup import BeautifulSoup
import execjs # json not good enough here...
import gzip
import json
from pprint import pprint
import re

from datavocabulary import DataVocabulary
from htmlmetadata import HTMLMetadata
from og import OG
from util import nth, xstrip


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

def html_price_ugh(soup):
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
    return data

def html_features_ugh(soup):
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
    data = {
    }
    bulcon = soup.findAll('span', {'class': 'pdpBulletContainer'})
    if bulcon:
        data['features'] = [node.text for node in bulcon]
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
        prices = sizelist.findAll(lambda tag: tag.name == 'span' and 'pdpSizeTile' in tag.get('class'))
        skus = [
            {'sku': p.get('data-skuid'),
             'size': p.text.strip() if p.text else None,
             'availability': 'available' in p.get('class') if p.get('class') else None
            }  for p in prices]
    return skus

class ProductBluefly(object):
    def __init__(self, id=None, name=None, descr=None, features=None,
                 url=None, img_url=None,
                 brand=None, brand_type=None, 
                 category=None, category_id=None,
                 price=None, currency=None,
                 color=None, variant=None,
                 sizes=None, availability=None, skus=None):

        assert isinstance(id, (type(None), basestring))
        assert isinstance(name, (type(None), basestring))
        assert isinstance(descr, (type(None), basestring))
        assert isinstance(features, (type(None), list))
        assert isinstance(url, (type(None), basestring))
        assert isinstance(img_url, (type(None), basestring))
        assert isinstance(sizes, (type(None), list))
        assert isinstance(availability, (type(None), bool))
        assert isinstance(skus, (type(None), list))

        self.id = id
        self.name = name
        self.descr = descr
        self.features = features
        self.url = url
        self.img_url = img_url
        self.brand = brand
        self.brand_type = brand_type
        self.category = category
        self.category_id = category_id
        self.price = price
        self.currency = currency
        self.color = color
        self.variant = variant
        self.sizes = sizes
        self.availability = availability
        self.skus = skus

    def __repr__(self):
        return '''ProductBluefly:
    id...........%s
    name.........%s
    descr........%s
    url..........%s
    img_url......%s
    brand........%s
    brand_type...%s
    category.....%s
    category_id..%s
    price........%s
    currency.....%s
    color........%s
    variant......%s
    features.....%s
    sizes........%s
    availability.%s
    skus.........%s
''' % (self.id,
       self.name,
       self.descr,
       self.url,
       self.img_url,
       self.brand,
       self.brand_type,
       self.category,
       self.category_id,
       self.price,
       self.currency,
       self.color,
       self.variant,
       self.features,
       self.sizes,
       self.availability,
       self.skus)

class ProductsBluefly(object):

    @staticmethod
    def from_html(url, html):
        soup = BeautifulSoup(html)

        meta = HTMLMetadata.do_html_metadata(soup)
        og = OG.get_og(html)
        dv = DataVocabulary.get_schema_product(html)
        dd = script_dataDictionary(soup)
        gaprod = script_gaProduct(soup)
        htmlprice = html_price_ugh(soup)
        htmlfeatures = html_features_ugh(soup)
        skus = custom_skus_ugh(soup)

        pprint(dv)
        pprint(dd)
        pprint(gaprod)
        pprint(og)
        pprint(meta)
        pprint(htmlprice)
        pprint(htmlfeatures)
        pprint(skus)
        #pprint(soup.findAll(lambda tag: any(k for k, v in tag.attrs if k.startswith('data-'))))

        products = []

        if (og.get('type') == 'product'
            or dd.get('product_id')
            or gaprod.get('product_id')):

            # TODO: mult-product support? haven't seen it yet...
            dv = dv[0] if dv else {}

            p = ProductBluefly(
                id=(dd.get('product_id')
                    or gaprod.get('product_id')
                    or None),
                name=(og.get('name')
                        or meta.get('description')
                        or meta.get('title') or None),
                descr=(og.get('description')
                        or meta.get('description')
                        or meta.get('title') or None),
                features=htmlfeatures.get('features') or None,
                url=og.get('url') or url,
                img_url=og.get('image'),
                brand=(xstrip(nth(dv.get(u'brand'), 0))
                        or dd.get('brand')
                        or graprod.get('brand')
                        or None),
                brand_type=dd.get('brand_type') or None,
                category=nth(dv.get('category'), 0) or None,
                category_id=dd.get('category_id') or None,
                price=htmlprice.get('price') or None,
                currency=htmlprice.get('currency') or None,
                color=dd.get('color') or None,
                variant=gaprod.get('variant') or None,
                sizes=[s.get('size') for s in skus] if skus else None,
                availability=any(s.get('availability')
                                for s in skus) if skus else None,
                skus=skus
            )
            products.append(p)
        return products
    


if __name__ == '__main__':
    import sys
    testfile = 'www.bluefly.com-a-testoni-brown-leather-chelsea-boots-p-357144202-detail.fly.gz'
    filepath = sys.argv[1] if len(sys.argv) > 1 else testfile
    products = []
    with gzip.open(filepath) as f:
        html = f.read()
    products = ProductsBluefly.from_html('http://bluefly.example/', html)
    pprint(products)

