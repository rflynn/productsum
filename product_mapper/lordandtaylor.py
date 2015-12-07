# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from lordandtaylor.com to zero or more products
'''

from bs4 import BeautifulSoup
import gzip
import execjs
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
from util import nth, normstring, xstrip, xboolstr, maybe_join, dehtmlify


class ProductLordandTaylor(object):
    def __init__(self, prodid=None, canonical_url=None, upc=None,
                 stocklevel=None, instock=None,
                 price=None, sale_price=None, currency=None,
                 bread_crumb=None, brand=None,
                 name=None, title=None, descr=None,
                 features=None, size=None, sizes=None,
                 color=None, colors=None,
                 img_url=None, img_urls=None,
                 skus=None):

        assert prodid is None or isinstance(prodid, basestring)
        assert canonical_url is None or isinstance(canonical_url, basestring)
        assert upc is None or isinstance(upc, basestring)
        assert stocklevel is None or isinstance(stocklevel, int)
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
        assert img_urls is None or isinstance(img_urls, list)
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
        self.img_urls = img_urls
        self.skus = skus

        # fixups
        # ...

    def __repr__(self):
        return '''ProductLordandTaylor(
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
    img_urls......%s
    skus..........%s
)''' % (self.canonical_url, self.prodid,  self.upc,
       self.instock, self.stocklevel,
       self.price, self.sale_price, self.currency,
       self.brand, self.bread_crumb,
       self.name, self.title, self.descr,
       self.features, self.size, self.sizes,
       self.color, self.colors,
       self.img_url, self.img_urls,
       self.skus)

    def to_product(self):

        category = None
        if self.bread_crumb:
            category = self.bread_crumb[-1]

        return Product(
            merchant_slug='lordandtaylor',
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
            img_urls=self.img_urls
        )




class ProductsLordandTaylor(object):

    @staticmethod
    def from_html(url, html):

        starttime = time.time()

        products = []

        soup = BeautifulSoup(html)
        meta = HTMLMetadata.do_html_metadata(soup)
        og = OG.get_og(soup)
        custom = ProductsLordandTaylor.get_custom(soup, html, url)

        signals = {
            'meta': meta,
            'og':   og,
            'custom': custom,
        }
        #pprint(signals)

        # is there one or more product on the page?
        if (og.get('type') == u'product' or custom.get('product_id')):

            p = ProductLordandTaylor(
                prodid=custom.get('product_id'),
                upc=custom.get('upc'),
                canonical_url=og.get('url') or custom.get('url_canonical') or url,
                stocklevel=custom.get('stock_level_total'),
                instock=(custom.get('instock')
                            or (og.get('availability') in ('instock',)
                                if 'availability' in og else None)),
                price=custom.get('price') or og.get('price:amount') or None,
                sale_price=custom.get('sale_price') or None,
                currency=og.get('price:currency') or None,
                bread_crumb=custom.get('breadcrumb') or None,
                brand=custom.get('brand') or og.get('brand') or None,
                name=(custom.get('name')
                            or og.get('title')
                            or meta.get('title') or None),
                title=og.get('title') or meta.get('title') or None,
                descr=og.get('description') or custom.get('descr') or meta.get('description') or None,
                features=custom.get('features') or None,
                color=custom.get('color') or None,
                colors=custom.get('colors') or None,
                size=custom.get('size') or None,
                sizes=custom.get('sizes') or None,
                skus=custom.get('skus') or None,
                img_url=og.get('image') or None,
                img_urls=custom.get('img_urls') or None,
            )
            products.append(p)

        realproducts = [p.to_product() for p in products]

        page = ProductMapResultPage(
                 merchant_slug='lordandtaylor',
                 url=url,
                 size=len(html),
                 proctime = time.time() - starttime,
                 signals=signals)

        return ProductMapResult(page=page,
                                products=realproducts)


    @staticmethod
    def get_custom(soup, html, url):

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

        data = {}

        '''
<input type="hidden" name="productId" value="1495444" id="productId"/>
<input type="hidden" name="sku" value="0856-1693" id="sku"/>
<input type="hidden" name="name" value="This Is Not A Bra Strapless Underwire" id="name"/>
        '''
        hidden = {i['name']: i['value'] for i in
                    soup.findAll('input',
                        {
                            'name': lambda x: x in {'name', 'sku', 'productId'},
                            'type': 'hidden',
                            'value': True
                        })}
        #print 'hidden:'
        #pprint(hidden)

        '''
<!-- VendorColor: Rich Black--><!-- Size: 34B--><!-- BOPISEligible: N--><!-- PromoMinOrder: N--><!-- ShipSurcharge: 0.00--><!-- ShoprunnerEligible: Y--><!-- SizeGuideLi
nk: 105--><!-- SpecialHandling: N--><!-- DisplayRatingReview: Y--><!-- GiftBoxable: Y--><!-- NonDiscountable: N--><!-- Style: Strapless/Convertible--><!-- Sale: N--><!-- Cleara
nce: N--><!-- Padding: Lightly lined--><!-- Wire: Underwire-->
        '''
        comments = {k.strip(): v.strip()
                        for k, v in [c.split(':', 1)
                            for c in re.findall(r'<!--([^!:]+:[^!]+)-->', html)]
                                if k and len(k) <= 32 and v and len(v) < 100} # avoid garbage

        #print 'comments:'
        #pprint(comments)

        '''
        <!-- ProductDisplay productId: 1495444 -->
        '''
        product_id = None
        try:
            m = re.search(r'<!-- ProductDisplay productId: ([0-9]+) -->', html)
            if m:
                product_id = m.groups(1)[0]
        except:
            traceback.print_exc()

        '''
        <div id="detial_main_content">
            <p>
            Detachable bra straps allow you to wear this strapless style from Warner's as a halter, crisscross, or standard bra. Featuring full cove rage, a Satin Comfort; Wire System that includes an encased underwire covered in luxurious satin that will provide all day comfort and prevent dig-in.<br/>
            <ul><li>Nylon/spandex</li><li>Hand wash</li><li>Imported</li></ul>
            </p>
        </div>
        '''
        descr = None
        features = None
        tag = soup.find('div', id=re.compile('^det(?:ia|ai)l_main_content$'))
        if tag:
            # description containing list of features...
            descr = xstrip(unicode(tag))
            #print 'descr:', descr
            if descr:
                ul = tag.find('ul')
                features = [xstrip(normstring(dehtmlify(f.text)))
                                for f in tag.findAll('li') if f]
                ul.replace_with('') # remove list...
                descr = xstrip(normstring(tag.get_text()))

        img_urls = None
        price = None
        skus = None
        in_stock = None
        stock_level_min = None
        stock_level_max = None
        stock_level_total = None
        size = None
        sizes = None
        color = comments.get('VendorColor') or None
        colors = None
        mpns = None
        upcs = None
        ei = None
        '''
        <div id="entitledItem_1495444" style="display:none;">
        [
            ...
        '''
        tag = soup.find('div', id=re.compile('^entitledItem_[0-9]+'))
        if tag:
            try:
                obj = execjs.eval(tag.get_text())
                #pprint(obj)
                ei = obj

                # we expect obj to be [{...},...] representing skus
                if isinstance(obj, list) and all(isinstance(o, dict) for o in obj):

                    img_urls = [urljoin(url, o[u'ItemImage'])
                                    for o in obj if o.get(u'ItemImage')]
                    skus = [o.get(u'partNumber') for o in obj]
                    upcs = [o.get(u'ItemThumbUPC') for o in obj]
                    prices = list(set(o.get(u'listPrice') for o in obj))
                    in_stock = any((o.get(u'inventoryStatus') == u'In Stock'
                                        and not o.get(u'outOfStock'))
                                            for o in obj) if obj else None
                    quantities = [o.get(u'availableQuantity') for o in obj
                                    if o.get(u'availableQuantity')]
                    if quantities:
                        try:
                            stock_level_min = int(float(min(quantities))) # floats, lol
                            stock_level_max = int(float(max(quantities)))
                            stock_level_total = sum(int(float(q)) for q in quantities)
                        except:
                            pass

                    if prices:
                        if len(prices) == 1:
                            price = prices[0]
                        else:
                            # build price range
                            price = '%s - %s' % (min(prices), max(prices))

                    # attrs are encoded verrry strangely...
                    sizes = set()
                    colors = set()
                    for a in [o.get(u'Attributes') for o in obj]:
                        for k in a.keys():
                            if k.startswith('Size_'):
                                sizes.add(k[5:])
                            elif k.startswith('VendorColor_'):
                                colors.add(k[12:])
                    sizes = sorted(sizes)
                    colors = sorted(colors)

                    if not color:
                        if colors and len(colors) == 1:
                            color = colors[0]
            except Exception as e:
                traceback.print_exc()

        brand = None
        name = None
        '''
        <h2 class="detial">JIMMY CHOO&nbsp;56mm Cat Eye Sunglasses</h2>
        '''
        # NOTE: this is dodgy as fuck, but it's the best we've got...
        tag = soup.find('h2', {'class': 'detial'})
        #print 'h2:', tag
        if tag:
            try:
                # oh dear...
                # interesting story: l&t encode the string with a literal '&nbsp;' in there
                # ...and it works with BeautifulSoup v3
                # ...but bs4 decodes the '&nbsp;' automatically...
                # so we have to use something else...
                # generate u'JIMMY CHOO\xa0Blah blah'
                txt = repr(unicode(list(tag.stripped_strings)[0]))[2:-1]
                if txt and txt.count(u'\\xa0'):
                    x, y = txt.split(u'\\xa0')
                    brand = xstrip(x) if x else None
                    name = xstrip(y) if y else None
            except:
                traceback.print_exc()

        data = {
            'url_canonical': url_canonical,
            'product_id': hidden.get('productId') or product_id or None,
            #'product_code': obj.get('product_code'),
            'descr': descr,
            'features': features,
            'brand': brand,
            #'brandid': obj.get('brandid'),
            #'brandcatid': obj.get('brandcatid'),
            #'breadcrumb': re.split('\s+>\s+', obj.get('pageName') or '') or None,
            'instock': in_stock,
            'stock_level_min': stock_level_min,
            'stock_level_max': stock_level_max,
            'stock_level_total': stock_level_total,
            'name': hidden.get('name') or name or None,
            #'pagetype': obj.get('pagetype'),
            'price': price,
            #'sale_price': dehtmlify(obj['price'].get('sale_price')) if 'price' in obj else None,
            'size': comments.get('Size') or None,
            'sizes': sizes,
            'color': color,
            'colors': colors,
            'sku': hidden.get('sku') or None,
            'skus': skus,
            #'upc': skus[0].get('upc') if skus and len(skus) == 1 else None,
            'img_urls': img_urls,
            'ei': ei,
            'comments': comments,
        }

        return data


if __name__ == '__main__':

    url = 'http://www.lordandtaylor.com/webapp/wcs/stores/servlet/en/lord-and-taylor/this-is-not-a-bra-strapless-underwire'

    # test no-op
    filepath = 'test/www.dermstore.com-product_Lipstick_31136.htm.gz'

    # test 1 product
    # NOTE: this one has no clear brand, except as a prefix...
    filepath = 'test/www.lordandtaylor.com-webapp-wcs-stores-servlet-en-lord-and-taylor-this-is-not-a-bra-strapless-underwire.gz'

    # try brand on another type of product?
    filepath = 'test/www.lordandtaylor.com-webapp-wcs-stores-servlet-en-lord-and-taylor-56mm-cat-eye-sunglasses-0237-danas--1.gz'

    with gzip.open(filepath) as f:
        html = f.read()

    products = ProductsLordandTaylor.from_html(url, html)
    print products
