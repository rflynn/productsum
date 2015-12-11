# ex: set ts=4 et:

# TODO: speed this up. this mapper is just too darn slow

'''
map a document archived from macys.com to zero or more products
'''

from bs4 import BeautifulSoup
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
from util import nth, dehtmlify, normstring, xboolstr, maybe_join


def get_meta_twitter(soup):
    # twitter card
    # ref: https://dev.twitter.com/cards/types/product
    # <meta property="twitter:card" content="product" />
    t = {}

    '''
    card = soup.find('meta', {'property': 'twitter:card'})
    if card:
        t = {
            'card': card.get('content'),
            'domain': card.get('domain'),
            'url': card.get('url'),
            'title': card.get('title'),
            'description': card.get('description'),
            'image': card.get('image'),
            'site': card.get('site'),
        }
    '''

    '''
    tags = soup.findAll(lambda tag: tag.name == 'meta' and tag.get('name') and tag.get('name').startswith('twitter:'))
    tm = {t.get('name'): t.get('content') for t in tags}
    # twitter is weird like this, mapping k:v pairs to 2 separate meta tags, yuck
    for i in xrange(len(tm) + 1):
        k = 'twitter:label%d' % i
        v = 'twitter:data%d' % i
        if k in tm and v in tm:
            t[tm[k]] = tm[v]
    '''

    # macys uses this by name convention
    byname = soup.findAll(lambda tag: tag.name == 'meta' and tag.get('name') and tag.get('name').startswith('twitter:') and (tag.get('value') or tag.get('content')))
    nameh = {t.get('name').replace('twitter:', ''): t.get('value') or t.get('content')
        for t in byname}
    #print 'byname:'
    #pprint(byname)
    for k, v in nameh.iteritems():
        name = k.replace('twitter:', '').lower()
        if not (name.startswith('label') or name.startswith('data')):
            t[name] = v

    for i in xrange(len(nameh) + 1):
        k = 'label%d' % i
        v = 'data%d' % i
        if k in nameh and v in nameh:
            t[nameh[k].lower()] = nameh[v]

    return t


class ProductMacys(object):
    VERSION = 0
    def __init__(self, prodid=None, canonical_url=None,
                 upc=None,
                 stocklevel=None, instock=None,
                 bread_crumb=None, category=None, brand=None,
                 name=None, descr=None, title=None,
                 price=None, sale_price=None, currency=None,
                 color=None, size=None,
                 img_url=None,
                 features=None):

        assert prodid is None or isinstance(prodid, basestring)
        assert canonical_url is None or isinstance(canonical_url, basestring)
        assert upc is None or isinstance(upc, basestring)
        assert instock is None or isinstance(instock, bool)
        assert stocklevel is None or isinstance(stocklevel, basestring)
        assert bread_crumb is None or isinstance(bread_crumb, list)
        assert category is None or isinstance(category, basestring)
        assert brand is None or isinstance(brand, basestring)
        assert name is None or isinstance(name, basestring)
        assert title is None or isinstance(title, basestring)
        assert descr is None or isinstance(descr, basestring)
        assert price is None or isinstance(price, basestring)
        assert sale_price is None or isinstance(sale_price, basestring)
        assert currency is None or isinstance(currency, basestring)
        assert color is None or isinstance(color, basestring)
        assert size is None or isinstance(size, basestring)
        assert img_url is None or isinstance(img_url, basestring)
        assert features is None or isinstance(features, list)

        self.prodid = prodid
        self.canonical_url = canonical_url
        self.upc = upc
        self.instock = instock
        self.stocklevel = stocklevel
        self.bread_crumb = bread_crumb
        self.category = normstring(dehtmlify(category))
        self.brand = normstring(dehtmlify(brand))
        self.name = normstring(dehtmlify(name))
        self.title = normstring(dehtmlify(title))
        self.descr = dehtmlify(descr)
        self.price = price
        self.sale_price = sale_price
        self.currency = currency
        self.color = color
        self.size = size
        self.img_url = img_url
        self.features = features


    def __repr__(self):
        return '''ProductMacys(
    prodid...........%s
    url..............%s
    upc..............%s
    instock..........%s
    stocklevel.......%s
    bread_crumb......%s
    category.........%s
    brand............%s
    name.............%s
    descr............%s
    price............%s
    sale_price.......%s
    currency.........%s
    color............%s
    size.............%s
    img_url..........%s
    features.........%s
)''' % (self.prodid, self.canonical_url, self.upc,
       self.instock, self.stocklevel,
       self.bread_crumb, self.category, self.brand,
       self.name, self.descr,
       self.price, self.sale_price, self.currency,
       self.color, self.size,
       self.img_url,
       self.features)

    def to_product(self):

        return Product(
            merchant_slug='macys',
            url_canonical=self.canonical_url,
            upc=self.upc,
            merchant_sku=self.prodid,
            merchant_product_obj=self,
            price=self.price,
            sale_price=self.sale_price,
            currency=self.currency,
            category=self.category,
            brand=self.brand,
            bread_crumb=self.bread_crumb,
            in_stock=self.instock,
            stock_level=self.stocklevel,
            name=self.name,
            title=self.title,
            descr=self.descr,
            features=self.features,
            color=self.color,
            available_colors=None,
            size=self.size,
            available_sizes=None,
            img_urls=[self.img_url] if self.img_url else None
        )



class ProductsMacys(object):

    @staticmethod
    def from_html(url, html):

        starttime = time.time()

        products = []

        soup = BeautifulSoup(html)
        sp = SchemaOrg.get_schema_product(html)
        og = OG.get_og(soup)
        meta = HTMLMetadata.do_html_metadata(soup)
        utag = Tealium.get_utag_data(soup)
        glob = ProductsMacys.script_Globals(soup)
        tw = get_meta_twitter(soup)
        macy = ProductsMacys.get_macy_extras(soup)
        pdp = ProductsMacys.get_script_pdpMainData(soup)
        upcmap = ProductsMacys.get_script_upcmap(soup)

        sp = sp[0] if sp else {}

        signals = {
            'sp':   SchemaOrg.to_json(sp),
            'og':   og,
            'tw':   tw,
            'meta': meta,
            'utag': utag,
            'glob': glob,
            'macy': macy,
            'pdp': pdp,
            'upcmap': upcmap,
        }
        #pprint(signals)

        prodid=(nth(utag.get('productID'), 0)
                or tw.get('product id')
                or pdp.get('id') or None)

        if prodid:

            offer = {}
            if sp.get('offers'):
                try:
                    offer = sp.get('offers')[0]['properties']
                except:
                    pass

            p = ProductMacys(
                    prodid=prodid,
                    canonical_url=url,
                    upc=upcmap.get('upc') or None,
                    stocklevel=nth(utag.get('stock_level'), 0) or None,
                    instock=(xboolstr(nth(utag.get('product_available'), 0))
                            or xboolstr(pdp.get('inStock'))
                            or xboolstr(upcmap.get('isAvailable'))
                            or None),
                    bread_crumb=(macy.get('breadcrumb')
                                or pdp.get('breadcrumb') or None),
                    category=(macy.get('category')
                            or pdp.get('category') or None),
                    brand=nth(sp.get(u'brand'), 0) or None,
                    name=(nth(sp.get('name'), 0)
                        or pdp.get('name')
                        or og.get('title')
                        or meta.get('title') or None),
                    title=(og.get('title')
                        or tw.get('title')
                        or meta.get('title')
                        or pdp.get('title') or None),
                    descr=(nth(sp.get('description'), 0)
                        or tw.get('description')
                        or meta.get('description') or None),
                    price=(nth(offer.get('price'), 0)
                        or pdp.get('regularPrice')
                        or tw.get('price') or None),
                    sale_price=pdp.get('salePrice') or None,
                    currency=nth(offer.get('priceCurrency'), 0) or None,
                    color=upcmap.get('color') or None,
                    size=upcmap.get('size') or None,
                    img_url=(pdp.get('imageUrl')
                            or nth(sp.get('image'), 0)
                            or og.get('image')
                            or tw.get('image') or None),
                    features=macy.get('features')
            )
            products.append(p)

        realproducts = [p.to_product() for p in products]

        page = ProductMapResultPage(
                 merchant_slug='macys',
                 url=url,
                 size=len(html),
                 proctime = time.time() - starttime,
                 signals=signals)

        return ProductMapResult(page=page,
                                products=realproducts)



    @staticmethod
    def get_script_upcmap(soup):
        '''
<script type="text/javascript">
MACYS.pdp.physicalName = "MA100MLVNAV007";
MACYS.pdp.cloneName = "macys-navapp_replica_prod_cellA_ma100mlvnav007_m01";
MACYS.pdp.upcmap = {};
MACYS.pdp.upcmap["2544700"] = [{ "upcID": 35024398, "color": "Black Antique Nickle/Gunmetal", "size": "", "type": "","upc": "889532064014", "isAvailable": "true", "shipDays": "4","availabilityMsg": "In Stock: Usually ships within 4 business days.","backOrderable": "false","availabilityOrderMethod": "POOL","inStoreEligible": "true" }];
        '''
        obj = {}
        script = soup.find(lambda tag: tag.name == 'script' and 'MACYS.pdp.upcmap' in tag.text)
        if script:
            m = re.search('MACYS.pdp.upcmap.*({[^{]+})', script.text)
            if m:
                try:
                    objstr = m.group(1)
                    #pprint(objstr)
                    obj = execjs.eval(objstr)
                    #print 'upc obj:'
                    #pprint(obj)
                except:
                    pass
        return obj 

    @staticmethod
    def get_script_pdpMainData(soup):
        data = {}
        script = soup.find(lambda tag: tag.name == 'script' and tag.get('id') == 'pdpMainData' and 'productDetail' in tag.text)
        if script:
            try:
                obj = execjs.eval(script.text)
            except Exception as e:
                traceback.print_exc()
                obj = {}
            if obj.get('productDetail'):
                obj = obj.get('productDetail')
            if obj.get('categoryName'):
                obj['breadcrumb'] = re.split('\s+[-]\s+', obj.get('categoryName'))
                if obj['breadcrumb']:
                    obj['category'] = obj['breadcrumb'][0] or None
            data = obj
        '''
<script id="pdpMainData" type="application/json">
{
"initializers": {
"mmlCarouselEnabled": "false",
"zTailorFeatureEnabled": "true"
},
"productDetail": {
"id": "2544700",
"giftCard": false,
"coach": true,
"suppressReviews": false,
"categoryId": "26846",
"custRatings": "",
"title": "COACH SWAGGER 27 CARRYALL IN METALLIC PATCHWORK LEATHER",
"imageUrl": "http://slimages.macysassets.com/is/image/MCY/products/7/optimized/3180187_fpx.tif",
"isChanel": false,
"isMaster": false,
"ratingPercent": "0",
"showReviews": true,
"showQuestionAnswers": false,
"showOffers": false,
"categoryName": "Handbags &amp; Accessories - COACH - Coach Handbags",
"name": "COACH SWAGGER 27 CARRYALL IN METALLIC PATCHWORK LEATHER",
"parentSku": "2544700",
"inStock": "true",
"regularPrice": "550.0",
"salePrice": "",
"registryMode": "",
"suppressedForIntlShipping": "false",
"pageType": "SINGLE ITEM",
"onlineExclusive": false,
"fullTaxonomy": "",
"orderByPhoneTemplate": "",
"sizeChartMap": {
"2544700": {
"sizeChart": "",
"intlSizeChart": "",
"sizeChartCanvasId": ""
}
},
"internationalMode": "false",
"scarcityType": "",
"specialOffers": [
]
}
}
</script>
        '''
        return data


    @staticmethod
    def get_macy_extras(soup):
        data = {}
        '''
<meta itemprop="breadcrumb" content="Handbags & Accessories - COACH - Coach Handbags" />
        '''
        tag = soup.find('meta', itemprop='breadcrumb')
        if tag:
            content = tag.get('content')
            if content:
                content = re.split('\s+[-]\s+', content)
                data['category'] = content[0] or None
            data['breadcrumb'] = content

        '''
<meta itemprop="image" content="http://slimages.macysassets.com/is/image/MCY/products/7/optimized/3180187_fpx.tif?wid=59&hei=72&fit=fit,1&$filtersm$" />
        '''
        tag = soup.find('meta', itemprop='image')
        if tag:
            data['image'] = tag.get('content')

        '''
<meta itemprop="productID" content="2544700"/>
        '''
        tag = soup.find('meta', itemprop='productID')
        if tag:
            data['productid'] = tag.get('content')

        '''
<div class="yui-content">
<div id="memberProductDetails" class="">
<div id="prdDesc" class="productDetailsBody">
<div id="longDescription" class="longDescription" itemprop="description">Statement belting updates a popular design with a little bit of swagger. Thoroughly organized inside and trimmed with a bold new version of the iconic Coach turnlock, this very modern carryall is finished by hand in metallic leather with a soft shimmer.</div>
<ul id="bullets" class="bullets">
<li>Metallic leather</li>
<li>Inside zip, cell phone and multifunction pockets</li>
<li>Zip-top closure, fabric lining</li>
<li>Handles with 4 drop</li>
<li>Longer strap with 19&#034; drop for shoulder wear</li>
<li>10 3/4&#034; (L) x 7 3/4&#034; (H) x 5 3/4&#034; (W)</li>
<li>Style No: 34547</li>
<li>Currently, Coach product bought on Macys.com cannot be shipped to Hawaii, US Territories or APO/FPO addresses</li>
<li>Imported</li>
<li class="productID">Web ID: 2544700</li>
</ul>
        '''
        container = soup.find('div', id='prdDesc')
        if container:
            tag = container.find('div', itemprop='description')
            data['description'] = tag.text

        tags = soup.select('#prdDesc > ul > li')
        data['features'] = [t.text for t in tags] or None

        return data


    @staticmethod
    def script_Globals(soup):
        '''
<script type="text/javascript">
( function () {
if ( window.require ) {
var Globals = require( "globals" );
if ( Globals ) {
Globals.setValue( "props", {
...
} );
}
}
} )();
</script>
        '''
        data = {}
        script = soup.find(lambda tag: tag.name == 'script' and 'Globals.setValue(' in tag.text)
        #pprint(script)
        if script:
            # FIXME: too fragile; instead, parse matching { ... } after "StyleModel"...
            m = re.search('Globals.setValue\( "props", ({.*}) \);', script.text, re.DOTALL)
            #print 'script.text:', script.text.encode('utf8')
            if m:
                objstr = m.group(1)
                #pprint(objstr)
                try:
                    data = execjs.eval(objstr)
                    #pprint(data)
                except:
                    traceback.print_exc()
        return data

if __name__ == '__main__':

    import gzip

    # test no-op, where page is empty-ish
    #filepath = ''

    # test "full" page
    url = 'http://www1.macys.com/shop/product/coach-swagger-27-carryall-in-metallic-patchwork-leather?ID=2544700&CategoryID=26846'
    filepath = 'test/www1.macys.com-shop-product-coach-swagger-27-carryall-in-metallic-patchwork-leather-ID-2544700.gz'

    with gzip.open(filepath) as f:
        html = f.read()

    products = ProductsMacys.from_html(url, html)

    print products
