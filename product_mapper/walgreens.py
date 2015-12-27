# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from walgreens.com to zero or more products
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


MERCHANT_SLUG = 'walgreens'


class ProductWalgreens(object):
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
        self.sale_price = sale_price
        self.price = price
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
            self.price = normstring(self.price).replace(' ', '')
        if isinstance(self.brand, list):
            self.brand = u' '.join(self.brand) or None
        self.brand = dehtmlify(normstring(self.brand))
        if isinstance(self.name, list):
            self.name = u' '.join(self.name) or None
        self.name = dehtmlify(normstring(self.name))
        self.title = dehtmlify(normstring(self.title))
        if isinstance(self.descr, list):
            self.descr = u' '.join(self.descr) or None
        self.descr = dehtmlify(normstring(self.descr))
        if self.features:
            self.features = [dehtmlify(f) for f in self.features]

        if self.name:
            if self.name.endswith(" | Walgreens"):
                self.name = self.name[:-len(" | Walgreens")]

        if self.title:
            if self.title.endswith(" | Walgreens"):
                self.title = self.title[:-len(" | Walgreens")]

        if self.upc:
            self.upc = str(self.upc)

    def __repr__(self):
        return ('''ProductWalgreens:
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


class ProductsWalgreens(object):

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

        # <input type="hidden" ng-model="hiddenProductId" id="hiddenProductId" value="prod6150246" />
        tag = soup.find('input', {'type': 'hidden', 'id': 'hiddenProductId', 'value': True})
        if tag:
            sku = sku or tag.get('value') or None
        if not sku:
            # <input type="hidden" id="prdId" value="prod6237994">
            tag = soup.find('input', {'type': 'hidden', 'id': 'prdId', 'value': True})
            if tag:
                sku = sku or tag.get('value') or None

        # <img src="//pics.drugstore.com/prodimg/405988/450.jpg" alt="Wet n Wild MegaLast Lip Color" itemprop="image" style="display: none" />
        tag = soup.find('img', itemprop='image', src=True)
        if tag:
            img_url = tag['src']
        if not img_url:
            tag = soup.find('img', id='main-product-image', src=True)
            if tag:
                img_url = tag['src']
        if img_url:
            img_url = urljoin(url_canonical, tag['src'])

        pn = soup.find('h1', id='productName')
        if pn:
            try:
                name = normstring(pn.contents[0])
            except Exception as e:
                print e
            # <span class="wag-product-size-in-title">0.11&nbsp;oz.</span>
            try:
                size = normstring(pn.findChild('span').text)
            except Exception as e:
                print e

        if not name:
            tag = soup.find(lambda t: t and 'itemprop' in t and t.get('itemprop') == 'name')
            if tag:
                try:
                    name = normstring(tag.get_text())
                except Exception as e:
                    print e

        '''
        <div class="wag-price-amount-strike" ng-if="productModel.jsonData.regularPrice">
        <!-- ngIf: productModel.jsonData.salePrice == null -->$1.99<!-- ngIf: productModel.jsonData.salePrice == null && productModel.jsonData.unitPrice && productModel.jsonData.unitPriceSize -->
        </div>
        '''
        tag = soup.find('div', {'ng-if': 'productModel.jsonData.regularPrice'})
        if tag:
            try:
                price = normstring(tag.get_text())
            except Exception as e:
                print e

        '''
<h2 class="wag-text-red mt10 ng-scope ng-binding" ng-if="productModel.jsonData.salePrice">
<!-- ngIf: productModel.jsonData.salePrice != null --><span ng-if="productModel.jsonData.salePrice != null" class="fonts9 wag-blk ng-scope ng-binding">
</span><!-- end ngIf: productModel.jsonData.salePrice != null -->$1.49
        '''
        tag = soup.find('h2', {'ng-if': 'productModel.jsonData.salePrice'})
        if tag:
            try:
                sale_price = normstring(tag.get_text())
            except Exception as e:
                print e


        if not price:
            tag = soup.find(attrs={'itemprop': 'price'})
            if tag:
                try:
                    price = normstring(tag.get_text())
                except Exception as e:
                    print e

        tag = soup.find('div', id='colorDropDown')
        if tag:
            colors = [normstring(li.get_text())
                        for li in tag.findAll('li')[1:]] or None

        if not color:
            tag = soup.find('select', id='colorId')
            if tag:
                colors = [normstring(o.get_text())
                            for o in tag.findAll('option')[1:]] or None

        tag = soup.find('ul', id='wag-vpd-overview-ul')
        if tag:
            try:
                features = [x for x in
                                [normstring(li.string)
                                    for li in tag.findAll('li')]
                                        if x] or None
            except Exception as e:
                print e
        if not features:
            tag = soup.find('div', {'class': lambda c: c and 'vpd_overview' in c})
            if tag:
                try:
                    features = [x for x in
                                    [normstring(li.string)
                                        for li in tag.findAll('li')]
                                            if x] or None
                except Exception as e:
                    print e
                
        overview = soup.find('div', {'class': lambda c: c and 'vpd_overview' in c})
        if tag:
            t = overview.find(lambda tag: tag and hasattr(tag, 'text') and tag.text.startswith('Size/Count'))
            if t:
                txt = normstring(t.get_text()[10:])
                # NOTE: we don't differentiate between count and size...
                if 'ea' in txt:
                    size = txt 
                elif 'oz' in txt:
                    size = txt

        tag = soup.find('ul', {'class': lambda c: c and 'breadcrumb' in c})
        if tag:
            try:
                breadcrumbs = [normstring(a.get_text())
                                    for a in tag.findAll('a')] or None
            except Exception as e:
                print e
        if not breadcrumbs:
            try:
                tag = soup.find('div', id='header_bar')
                if tag:
                    breadcrumbs = []
                    for li in tag.findAll('li'):
                        a = li.find('a')
                        if a:
                            try:
                                breadcrumbs.append(normstring(a.get_text()))
                            except:
                                pass
                    breadcrumbs = breadcrumbs or None
            except Exception as e:
                print e
            


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
    def from_html(cls, url, html):

        starttime = time.time()

        if '/walgreenstv/walgreenstv.jsp' in url:
            # nuthin'
            page = ProductMapResultPage(
                    version=cls.VERSION,
                    merchant_slug=MERCHANT_SLUG,
                    url=url,
                    size=len(html),
                    proctime = time.time() - starttime,
                    signals={})
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
                    or custom.get('sku') # this one is expected for walgreens.com
                    or nth(sp.get('sku'), 0)
                    or nth(utag.get('product_id'), 0)
                    or nth(utag.get('productID'), 0)
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

            p = ProductWalgreens(
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
                name=(custom.get('name')
                            or sp.get('name')
                            or og.get('title')
                            or nth(utag.get('product_name'), 0)
                            or None),
                title=(custom.get('title')
                            or og.get('title')
                            or meta.get('title')
                            or None),
                descr=(custom.get('descr')
                            or og.get('description')
                            or sp.get('description')
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
                    signals=signals)

        return ProductMapResult(page=page,
                                products=realproducts)


def do_file(url, filepath):
    print 'filepath:', filepath
    with gzip.open(filepath) as f:
        html = f.read()
    return ProductsWalgreens.from_html(url, html)


if __name__ == '__main__':

    import sys

    url = 'http://www.walgreens.com/store/c/wet-n-wild-megalast-lip-color/ID=prod6150246-product'
    filepath = 'test/www.walgreens.com-store-c-wet-n-wild-megalast-lip-color-ID-prod6150246-product.html.gz'

    url = 'http://www.walgreens.com/store/c/sally-hansen-miracle-gel/ID=prod6237994-product'
    filepath = 'test/www.walgreens.com-store-c-sally-hansen-miracle-gel-ID-prod6237994-product.gz'

    # test no-op
    #filepath = 'test/www.yoox.com-us-44814772VC-item.gz'

    if len(sys.argv) > 1:
        for filepath in sys.argv[1:]:
            print do_file(url, filepath)
    else:
        print do_file(url, filepath)
