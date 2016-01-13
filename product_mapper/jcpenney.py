# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from jcpenney.com to zero or more products
'''

from bs4 import BeautifulSoup
import execjs
import gzip
import json
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
from util import nth, normstring, dehtmlify, xboolstr, u


MERCHANT_SLUG = 'jcpenney'


class ProductJCPenney(object):
    VERSION = 0
    def __init__(self, id=None, url=None, merchant_name=None, slug=None,
                 merchant_sku=None, upc=None, isbn=None, ean=None,
                 currency=None, sale_price=None, price=None,
                 brand=None, category=None, breadcrumb=None,
                 in_stock=None, stock_level=None,
                 name=None, title=None, descr=None,
                 material=None, features=None,
                 color=None, colors=None,
                 size=None, sizes=None,
                 img_url=None, img_urls=None):

        self.id = id
        self.url = url
        self.merchant_name = merchant_name
        self.slug = slug
        self.merchant_sku = merchant_sku
        self.upc = upc
        self.isbn = isbn
        self.ean = ean
        self.currency = currency
        self.sale_price = normstring(sale_price)
        self.price = normstring(price)
        self.brand = brand
        self.category = category
        self.breadcrumb = breadcrumb
        self.in_stock = in_stock
        self.stock_level = stock_level
        self.name = name
        self.title = title
        self.descr = descr
        self.material = material
        self.features = features
        self.color = color
        self.colors = colors
        self.size = size
        self.sizes = sizes
        self.img_url = img_url
        self.img_urls = img_urls

        # fixup
        if self.id is not None:
            self.id = str(self.id) # ensure we're a string, some signals produce numeric
        assert self.id != 'None'

        if self.price:
            self.price = normstring(self.price).replace(' ', '') or None
            if self.price:
                if self.price.endswith('sale'):
                    self.price = self.price[:-len('sale')].strip()

        if self.sale_price:
            if self.sale_price.endswith('sale'):
                self.sale_price = self.sale_price[:-len('sale')].strip()

        if isinstance(self.brand, list):
            self.brand = u' '.join(self.brand) or None
        self.brand = dehtmlify(normstring(self.brand))

        if isinstance(self.name, list):
            self.name = u' '.join(self.name) or None
        self.name = dehtmlify(normstring(self.name))

        # clean up "$brand $upper_name"
        if self.name:
            if self.brand:
                if self.name.upper().startswith(self.brand.upper()):
                    self.name = self.name[len(self.brand):].lstrip()
            if self.name.upper() == self.name:
                self.name = self.name.title()

        self.title = dehtmlify(normstring(self.title))
        if isinstance(self.descr, list):
            self.descr = u' '.join(self.descr) or None

        self.descr = dehtmlify(normstring(self.descr))
        if self.descr:
            if self.descr.startswith('jcp | '):
                self.descr = self.descr[6:].lstrip()

        if self.features:
            self.features = [dehtmlify(f) for f in self.features]

        if self.upc:
            self.upc = str(self.upc)

    def __repr__(self):
        return ('''ProductJCPenney:
    id............... %s
    url.............. %s
    merchant_name.... %s
    merchant_sku..... %s
    slug............. %s
    upc.............. %s
    isbn............. %s
    ean.............. %s
    currency......... %s
    sale_price....... %s
    price............ %s
    brand............ %s
    category......... %s
    breadcrumb....... %s
    in_stock......... %s
    stock_level...... %s
    name............. %s
    title............ %s
    descr............ %s
    material......... %s
    features......... %s
    color............ %s
    colors........... %s
    size............. %s
    sizes............ %s
    img_url.......... %s
    img_urls......... %s''' % (
       self.id,
       self.url,
       self.merchant_name,
       self.merchant_sku,
       self.slug,
       self.upc,
       self.isbn,
       self.ean,
       self.currency,
       self.sale_price,
       self.price,
       self.brand,
       self.category,
       self.breadcrumb,
       self.in_stock,
       self.stock_level,
       self.name,
       self.title,
       self.descr,
       self.material,
       self.features,
       self.color,
       self.colors,
       self.size,
       self.sizes,
       self.img_url,
       self.img_urls)).encode('utf8')

    def to_product(self):

        if not self.colors:
            available_colors = None
        elif self.colors == [u'No Color']:
            available_colors = []
        else:
            available_colors = [c for c in self.colors if c]

        if not self.sizes:
            available_sizes = None
        elif self.sizes == ['NO SIZE']:
            available_sizes = []
        else:
            available_sizes = [s for s in self.sizes if s]

        return Product(
            merchant_slug=MERCHANT_SLUG,
            url_canonical=self.url,
            upc=self.upc,
            merchant_sku=self.id,
            merchant_product_obj=self,
            price=self.price,
            sale_price=self.sale_price,
            currency=self.currency,
            brand=self.brand,
            category=self.category,
            bread_crumb=self.breadcrumb,
            in_stock=self.in_stock,
            stock_level=self.stock_level,
            name=self.name,
            title=self.title,
            descr=self.descr,
            features=self.features,
            color=self.color,
            available_colors=available_colors,
            size=self.size,
            available_sizes=available_sizes,
            img_url=self.img_url,
            img_urls=sorted(self.img_urls) if self.img_urls is not None else None
        )


class ProductsJCPenney(object):

    VERSION = 0

    @staticmethod
    def get_custom(soup, url, og):

        sku = None
        productid = None
        brand = None
        category = None
        breadcrumbs = None
        name = None
        title = None
        descr = None
        features = None
        in_stock = None
        stock_level = None
        slug = None
        currency = None
        price = None
        sale_price = None
        color = None
        colors = None
        size = None
        sizes = None
        img_url = None
        upc = None
        upcs = None

        try:
            url_canonical = soup.find('link', rel='canonical').get('href')
        except:
            url_canonical = url

        if not sku:
            # var prodId = 'pp5006081078';
            m = re.search(r"var prodId = 'pp([0-9]{8,16})';", str(soup))
            #print 'm:', m
            if m:
                try:
                    sku = m.groups(0)[0]
                    #print 'sku:', sku
                except:
                    traceback.print_exc()

        '''
<script language="JavaScript">
var jcpPRODUCTPRESENTATIONSjcp = 'pp5005790320@$29.99@1';
var globalDataLayer = window["jcpDLjcp"];
// does global data layer exist
if (globalDataLayer) {
var jcpPPJSON = {"ppID":"pp5005790320","prodCount":1,"prodName":"Columbia® Three Rivers™ Fleece Jacket","products":[{"ppID":"pp5005790320","prodName":"Columbia® Three Rivers™ Fleece Jacket","lots":[{"lotID":"2635345","prodDiv":"008","prodSubdiv":"263","prodEntity":"15","skus":[{"skuID":"26353450059","skuStatus":"Available"},{"skuID":"26353450075","sk
}
</script>
        '''
        sc = soup.find('script', text=re.compile(r'jcpPPJSON\s*=\s*{'))
        if sc and hasattr(sc, 'text'):
            #print sc.text.encode('utf8')
            m = re.search('jcpPPJSON\s*=\s*({.*});', sc.text)
            if m:
                try:
                    objtxt = m.groups(0)[0]
                    obj = json.loads(objtxt)
                    #pprint(obj)
                    sku = sku or obj.get('ppID') or None
                    price = price or obj.get('price')
                    if price:
                        price = str(price)
                    name = name or obj.get('prodName')
                except:
                    traceback.print_exc()

        if not sku:
            # <div class="hidden" id="ppIdorLotId">pp5006081078</div>
            div = soup.find('div', id='ppIdorLotId')
            if div:
                try:
                    sku = div.get_text()
                except:
                    traceback.print_exc()

        '''
<div id="longCopy">
<div id="longCopyCont" class="pdp_brand_desc_info" itemprop="description">
The warm fleece of our Columbia zip-front jacket keeps you cozy and comfortable during all your outdoor adventures.
<ul>
        <li>lightweight</li>
        <li>elastic cuffs</li>
        <li>2 zip pockets</li>
        <li>adjustable drawcord hem</li>
        <li>25" length from shoulder</li>
        <li>MTR filament fleece</li>
        <li>polyester</li>
        <li>washable</li>
        <li>imported</li>
</ul>
</div>
</div>
        '''
        # descr and features
        de = soup.find('div', itemprop='description')
        if de:
            try:
                # contains descr and maybe list of features
                flist = de.find('ul')
                if flist:
                    flist.extract()
                    features = [x for x in
                                    [normstring(li.get_text())
                                        for li in flist.findAll('li')]
                                            if x] or None
                descr = normstring(de.get_text())
            except:
                traceback.print_exc()

        if not sizes:
            try:
                sizes = [x for x in
                            [normstring(li.get_text())
                                for li in soup.select('ul.sku_alt_options li#size')]
                                    if x] or None
                if sizes:
                    for i, s in enumerate(sizes):
                        if s.endswith('Currently out of stock'):
                            sizes[i] = s[:-len('Currently out of stock')].rstrip()
            except:
                traceback.print_exc()

        br = soup.find('div', id='breadcrumb')
        if br:
            try:
                breadcrumbs = [x for x in
                                [normstring(li.get_text())
                                    for li in br.findAll('li')]
                                        if x and x != '>'] or None
                if breadcrumbs:
                    if breadcrumbs[0].lower() == u'jcpenney':
                        breadcrumbs.pop(0)
                    breadcrumbs = breadcrumbs or None
                if breadcrumbs:
                    if breadcrumbs[-1].lower() == u'return to product results':
                        breadcrumbs.pop()
                    breadcrumbs = breadcrumbs or None
                if breadcrumbs and len(breadcrumbs) > 1:
                    category = breadcrumbs[-1]
            except:
                traceback.print_exc()

        swatches = soup.select('li a.swatch img')
        #pprint(swatches)
        if swatches:
            try:
                colors = [x for x in
                            [normstring(a.get('name'))
                                for a in swatches]
                                    if x] or None
            except:
                traceback.print_exc()

        return {
            'url_canonical': url_canonical,
            'brand': brand,
            'sku': sku,
            'upc': upc,
            'slug': slug,
            'category': category,
            'name': name,
            'descr': descr,
            'in_stock': in_stock,
            'stock_level': stock_level,
            'features': features,
            'currency': currency,
            'price': price,
            'sale_price': sale_price,
            'breadcrumbs': breadcrumbs,
            'color': color,
            'colors': colors,
            'size': size,
            'sizes': sizes,
            'img_url': img_url,
        }

    @classmethod
    def from_html(cls, url, html, updated=None):

        starttime = time.time()

        if '/cat.jump' in url:
            # not a product
            page = ProductMapResultPage(
                    version=cls.VERSION,
                    merchant_slug=MERCHANT_SLUG,
                    url=url,
                    size=len(html),
                    proctime = time.time() - starttime,
                    signals={},
                    updated=updated)
            return ProductMapResult(page=page,
                                    products=[])

        soup = BeautifulSoup(html)

        # standard shit
        meta = HTMLMetadata.do_html_metadata(soup)
        sp = SchemaOrg.get_schema_product(html)
        og = OG.get_og(soup)
        custom = cls.get_custom(soup, url, og)
        utag = Tealium.get_utag_data(soup)

        sp = sp[0] if sp else {}

        signals = {
            'meta': meta,
            'sp':   SchemaOrg.to_json(sp),
            'og':   og,
            'utag': utag,
            'custom': custom,
        }
        #pprint(signals)

        # TODO: tokenize and attempt to parse url itself for hints on brand and product
        # use everything at our disposal

        prodid = (og.get('product:mfr_part_no')
                    or og.get('mfr_part_no')
                    or og.get('product_id')
                    or nth(sp.get('sku'), 0) # should exist in jcpenney
                    or custom.get('sku') # should exist in jcpenney
                    or None)

        products = []

        if prodid:

            try:
                spoffer = sp['offers'][0]['properties']
            except:
                spoffer = {}

            try:
                spbrand = sp.get('brand')
                if spbrand:
                    spbrand = spbrand[0]
                    if isinstance(spbrand, basestring):
                        pass
                    elif isinstance(spbrand, dict):
                        spbrand = nth(spbrand['properties']['name'], 0)
                if isinstance(spbrand, list):
                    spbrand = u' '.join(spbrand)
            except:
                spbrand = None

            p = ProductJCPenney(
                id=prodid,
                url=(custom.get('url_canonical')
                            or og.get('url')
                            or sp.get('url')
                            or url
                            or None),
                upc=custom.get('upc') or None,
                slug=custom.get('slug') or None,
                merchant_name=(og.get('product:retailer_title')
                            or og.get('retailer_title')
                            or og.get('site_name')
                            or None),
                ean=(og.get('product:ean')
                            or og.get('ean')
                            or None),
                currency=(og.get('product:price:currency')
                            or og.get('product:sale_price:currency')
                            or og.get('sale_price:currency')
                            or og.get('price:currency')
                            or og.get('currency')
                            or og.get('currency:currency')
                            or nth(utag.get('order_currency_code'), 0)
                            or nth(spoffer.get('priceCurrency'), 0)
                            or custom.get('currency')
                            or None),
                price=(custom.get('price')
                            or og.get('product:original_price:amount')
                            or og.get('price:amount')
                            or nth(spoffer.get('price'), 0)
                            or nth(utag.get('product_price'), 0)
                            or None),
                sale_price=(custom.get('sale_price')
                            or og.get('product:sale_price:amount')
                            or og.get('sale_price:amount')
                            or og.get('product:price:amount')
                            or og.get('price:amount')
                            or custom.get('sale_price')
                            or nth(spoffer.get('price'), 0)
                            or None),
                brand=(custom.get('brand')
                            or og.get('product:brand')
                            or og.get('brand')
                            or spbrand
                            or None),
                category=custom.get('category') or None,
                breadcrumb=(custom.get('breadcrumbs')
                            or utag.get('bread_crumb')
                            or None),
                name=(sp.get('name')
                            or custom.get('name')
                            or og.get('title')
                            or nth(utag.get('product_name'), 0)
                            or None),
                title=(custom.get('title')
                            or og.get('title')
                            or meta.get('title')
                            or None),
                descr=(custom.get('descr')
                            or sp.get('description') # much better than og
                            or og.get('description')
                            or meta.get('description')
                            or None),
                in_stock=((spoffer.get('availability') == [u'http://schema.org/InStock'])
                            or (((og.get('product:availability')
                            or og.get('availability')) in ('instock', 'in stock'))
                            or xboolstr(nth(utag.get('product_available'), 0)))
                            or custom.get('in_stock')
                            or None),
                stock_level=(nth(utag.get('stock_level'), 0)
                            or custom.get('stock_level')
                            or None),
                material=(og.get('product:material')
                            or og.get('material')
                            or None),
                features=custom.get('features') or None,
                color=(custom.get('color')
                            or og.get('product:color')
                            or og.get('color')
                            or nth(sp.get('color'), 0)
                            or None),
                colors=custom.get('colors'),
                size=custom.get('size') or None,
                sizes=custom.get('sizes'),
                img_url=(og.get('image')
                            or nth(sp.get('image'), 0)
                            or custom.get('img_url')
                            or None),
                img_urls=sp.get('image'),
            )
            products.append(p)

        realproducts = [p.to_product() for p in products]

        page = ProductMapResultPage(
                    version=cls.VERSION,
                    merchant_slug=MERCHANT_SLUG,
                    url=url,
                    size=len(html),
                    proctime = time.time() - starttime,
                    signals=signals,
                    updated=updated)

        return ProductMapResult(page=page,
                                products=realproducts)


def do_file(url, filepath):
    print 'filepath:', filepath
    with gzip.open(filepath) as f:
        html = f.read()
    return ProductsJCPenney.from_html(url, html)


if __name__ == '__main__':

    import sys

    url = 'http://www.jcpenney.com/journee-collection-gladiator-wedges/prod.jump?ppId=pp5006081078&catId=cat100250187&deptId=dept20000018&Ns=PHL&Ns=PHL&_dyncharset=UTF-8&colorizedImg=DP0904201517022767M.tif'
    filepath = 'test/www.jcpenney.com-journee-collection-gladiator-wedges-prod.jump-ppId-pp5006081078.html.gz'

    url = 'http://www.jcpenney.com/columbia-three-rivers-fleece-jacket/prod.jump?ppId=pp5005790320'
    filepath = 'test/www.jcpenney.com-columbia-three-rivers-fleece-jacket-prod.jump-ppId-pp5005790320.gz'

    # test no-op
    #filepath = 'test/www.yoox.com-us-44814772VC-item.gz'

    if len(sys.argv) > 1:
        for filepath in sys.argv[1:]:
            print do_file(url, filepath)
    else:
        print do_file(url, filepath)
