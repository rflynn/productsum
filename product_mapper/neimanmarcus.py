# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from neimanmarcus.com to zero or more products
'''

from bs4 import BeautifulSoup
import base64
import gzip
import json
import microdata
import opengraph
from pprint import pprint
import re
import requests
import time

from htmlmetadata import HTMLMetadata
from og import OG
from product import Product, ProductMapResultPage, ProductMapResult
from schemaorg import SchemaOrg
from tealium import Tealium
from util import nth, normstring, xboolstr, maybe_join, dehtmlify


class ProductNeimanMarcus(object):
    VERSION = 0
    def __init__(self, prodid=None, canonical_url=None,
                 stocklevel=None, instock=None,
                 brand=None,
                 name=None, title=None, descr=None, features=None,
                 price=None, currency=None,
                 img_url=None,
                 bread_crumb=None,
                 cmos_catalog_id=None,
                 cmos_item=None,
                 cmos_sku=None,
                 nm_product_type=None):

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
        assert img_url is None or isinstance(img_url, basestring)
        assert bread_crumb is None or isinstance(bread_crumb, list)
        assert cmos_catalog_id is None or isinstance(cmos_catalog_id, basestring)
        assert cmos_item is None or isinstance(cmos_item, basestring)
        assert cmos_sku is None or isinstance(cmos_sku, basestring)
        assert isinstance(nm_product_type, (type(None), basestring))

        self.prodid = prodid
        self.canonical_url = canonical_url
        self.stocklevel = stocklevel
        self.instock = instock
        self.brand = normstring(brand)
        self.name = normstring(name)
        self.title = normstring(title)
        self.descr = descr
        self.features = features
        self.price = price
        self.currency = currency
        self.img_url = img_url
        self.bread_crumb = bread_crumb
        self.cmos_catalog_id = cmos_catalog_id
        self.cmos_item = cmos_item
        self.cmos_sku = cmos_sku
        self.is_prod_group = nm_product_type == 'group'

        # fixups

        if self.stocklevel is not None:
            self.stocklevel = int(self.stocklevel)

        # normalize bread_crumb
        if self.bread_crumb is not None:
            self.bread_crumb = [normstring(x) for x in self.bread_crumb if x]

        # normalize brand
        # if we have a bread crumb containing 'Designers', use the next entry
        if self.bread_crumb:
            if u'Designers' in self.bread_crumb:
                idx = self.bread_crumb.index(u'Designers')
                if len(self.bread_crumb) >= idx:
                    self.brand = self.bread_crumb[idx+1]
        if self.brand and self.brand.endswith('/c.cat'):
            cats = self.brand.split('/')
            if cats:
                while cats and not cats[0]:
                    cats.pop(0)
                if cats:
                    self.brand = cats[0].replace('-', ' ')

    def __repr__(self):
        return '''ProductNeimanMarcus(
    prodid...........%s
    url..............%s
    instock..........%s
    stocklevel.......%s
    brand............%s
    name.............%s
    descr............%s
    features.........%s
    price............%s
    currency.........%s
    img_url..........%s
    bread_crumb......%s
    cmos_catalog_id..%s
    cmos_item........%s
    cmos_sku.........%s
    is_prod_group....%s
)''' % (self.prodid, self.canonical_url,
       self.instock, self.stocklevel,
       self.brand,
       self.name, self.descr, self.features,
       self.price, self.currency,
       self.img_url,
       self.bread_crumb,
       self.cmos_catalog_id,
       self.cmos_item,
       self.cmos_sku,
       self.is_prod_group)

    def to_product(self):

        category = None
        if self.bread_crumb:
            category = self.bread_crumb[-1]

        return Product(
            merchant_slug='neimanmarcus',
            url_canonical=self.canonical_url,
            merchant_sku=self.prodid,
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
            size=None,
            available_sizes=None,
            img_urls=[self.img_url] if self.img_url else None
        )




class ProductsNeimanMarcus(object):

    @staticmethod
    def from_html(url, html):

        starttime = time.time()

        products = []

        soup = BeautifulSoup(html)
        sp = SchemaOrg.get_schema_product(html)
        og = OG.get_og(soup)
        meta = HTMLMetadata.do_html_metadata(soup)
        utag = Tealium.get_utag_data(soup)
        custom = ProductsNeimanMarcus.get_custom(soup, og)

        sp = sp[0] if sp else {}

        signals = {
            'sp':   SchemaOrg.to_json(sp),
            'og':   og,
            'meta': meta,
            'custom': custom,
        }
        #pprint(signals)

        # is there one or more product on the page?
        if (sp
            or utag.get(u'product_id')
            or og.get('type') == u'product'
            or utag.get(u'page_type') == u'Product Detail'):
            # ok, there's 1+ product. extract them...

            name = (nth(sp.get('name'), 0)
                or nth(utag.get(u'product_name'), 0)
                or og.get('title')
                or meta.get('title') or None)

            if utag and utag.get(u'product_id'):
                for i in xrange(len(utag.get(u'product_id'))):
                    p = ProductNeimanMarcus(
                        prodid=nth(utag.get('product_id'), i),
                        canonical_url=custom.get('url_canonical') or url,
                        stocklevel=nth(utag.get('stock_level'), i) or None,
                        instock=xboolstr(nth(utag.get('product_available'), i)),
                        brand=nth(sp.get(u'brand'), i) or custom.get('brand') or None,
                        name=nth(utag.get(u'product_name'), i) or name,
                        title=og.get('title') or meta.get('title') or None,
                        descr=maybe_join(' ', sp.get('description')) or None,
                        features=custom.get('features') or None,
                        price=nth(utag.get('product_price'), i) or None,
                        currency=utag.get('order_currency_code') or None,
                        img_url=og.get('image') or None,
                        bread_crumb=utag.get('bread_crumb') or None,
                        cmos_catalog_id=nth(utag.get('product_cmos_catalog_id'), i) or None,
                        cmos_item=nth(utag.get('product_cmos_item'), i) or None,
                        cmos_sku=nth(utag.get('product_cmos_sku'), i) or None,
                        nm_product_type=utag.get('product_type'),
                    )
                    products.append(p)
            else:
                p = ProductNeimanMarcus(
                    prodid=nth(utag.get('product_id'), 0),
                    canonical_url=custom.get('url_canonical') or url,
                    stocklevel=nth(utag.get('stock_level'), 0),
                    instock=xboolstr(nth(utag.get('product_available'), 0)),
                    brand=nth(sp.get(u'brand'), 0) or custom.get('brand') or None,
                    name=name,
                    title=og.get('title') or meta.get('title') or None,
                    descr=maybe_join(' ', sp.get('description')) or None,
                    features=custom.get('features') or None,
                    price=nth(utag.get('product_price'), 0),
                    currency=utag.get('order_currency_code') or None,
                    img_url=og.get('image') or None,
                    bread_crumb=utag.get('bread_crumb') or None,
                    cmos_catalog_id=nth(utag.get('product_cmos_catalog_id'), 0),
                    cmos_item=nth(utag.get('product_cmos_item'), 0),
                    cmos_sku=nth(utag.get('product_cmos_sku'), 0),
                    nm_product_type=utag.get('product_type'),
                )
                products.append(p)

        realproducts = [p.to_product() for p in products]

        page = ProductMapResultPage(
                 merchant_slug='neimanmarcus',
                 url=url,
                 size=len(html),
                 proctime = time.time() - starttime,
                 signals=signals)

        return ProductMapResult(page=page,
                                products=realproducts)


    @staticmethod
    def get_custom(soup, og):
        # url
        url_canonical = None
        tag = soup.find('link', rel='canonical', href=True)
        if tag:
            url_canonical = tag.get('href')
        if not url_canonical:
            url_canonical = og.get('url')
            if url_canonical and url_canonical.endswith('?ecid=NMSocialFacebookLike'):
                url_canonical = url_canonical[:-len('?ecid=NMSocialFacebookLike')]
        # brand
        brand = None
        tag = soup.find('span', {'class':'prodDesignerName'})
        if tag:
            brand = normstring(dehtmlify(tag.text))
        # features
        features = None
        tag = soup.find('div', itemprop='description')
        if tag:
            features = [t.text for t in tag.findAll('li') or []]
        data = {
            'brand': brand,
            'features': features,
            'url_canonical': url_canonical,
        }
        return data


if __name__ == '__main__':

    filepath = 'test/www.neimanmarcus.com-Eileen-Fisher-Linen-Jersey-Box-Top-Stretch-Boyfriend-Jeans-Petite--prod177290080--p.prod.gz'
    filepath = 'test/www.neimanmarcus.com-Stuart-Weitzman-Nouveau-Floral-Print-Python-Pump-Rose-Multo-prod167650036-p.prod.gz'
    filepath = 'test/www.neimanmarcus.com-Christian-Louboutin-Debout-Patent-PVC-Red-Sole-Pump-Multicolor-Shoes-prod182870064_cat39620738__-p.prod.gz'

    url = 'http://neimanmarcus.example/'

    # doesn't populate url_product...
    filepath = 'test/www.neimanmarcus.com-Sklo-Sway-Long-Bowl-Accents-prod185550170_cat40520739__-p.prod-icid--searchType-EndecaDrivenCat.gz'

    with gzip.open(filepath) as f:
        html = f.read()

    products = ProductsNeimanMarcus.from_html(url, html)

    print products


'''
>>> pprint(json.loads(re.search('({.*})', [s.text for s in soup.findAll('script') if 'utag_data' in s.text][0]).groups(0)[0]))
{u'ab_test_group': [u'11400001', u'8900001', u'7700001'],
 u'ab_test_id': [u'11200001', u'8700001', u'7500001'],
 u'account_registration': u'false',
 u'bread_crumb': [],
 u'cat_id': [],
 u'complete_the_look': u'true',
 u'country_code': u'US',
 u'customer_country': u'United States',
 u'customer_email': u'',
 u'customer_linked_email': u'',
 u'customer_registered': u'false',
 u'customer_segment': u'0',
 u'customer_segment_id': u'',
 u'customer_segment_name': u'',
 u'emerging_elite': u'0',
 u'interaction_message': [],
 u'localized_price': u'false',
 u'logged_in_previous_page_flag': u'false',
 u'logged_in_status': u'false',
 u'order_currency_code': u'USD',
 u'page_definition_id': u'product',
 u'page_type': u'Product Detail',
 u'parent_cmos_item_code': u'-5JD7',
 u'product_available': [u'true', u'true'],
 u'product_cmos_catalog_id': [u'NMF16', u'NMF16'],
 u'product_cmos_item': [u'T92ST', u'T892E'],
 u'product_cmos_sku': [u'3656A653135161', u''],
 u'product_configurable': [u'false', u'false'],
 u'product_expected_availability': [u'', u''],
 u'product_id': [u'prod175120147', u'prod170450177'],
 u'product_inventory_status': [u'Instock', u''],
 u'product_monogrammable': [u'false', u'false'],
 u'product_name': [u'Linen Jersey Box Top & Stretch Boyfriend Jeans, Petite'],
 u'product_price': [u'62.00', u'178.00'],
 u'product_pricing_adornment_flag': [u'true', u'false'],
 u'product_sellable_sku': [u'true', u''],
 u'product_showable': [u'true', u''],
 u'product_swatch': [u'false', u'false'],
 u'product_type': u'group',
 u'profile_type': u'customer',
 u'same_day_delivery': u'false',
 u'server_date_time': u'1448402044',
 u'site_environment': u'prod',
 u'stock_level': [u'2', u''],
 u'suppress_checkout_flag': u'false',
 u'universal_customer_id': u'128f1247-19e9-4bed-9dec-2ba4082a338c',
 u'unsellable_skus': u'true',
 u'unsupported_browser': [],
 u'url_email_decoded': u'',
 u'video_on_page': u'true',
 u'web_id': u''}
'''

def js_timestamp_now():
    return int(time.time() * 1000)

def query_status(product_ids):
    '''
    neimanmarcus has an externally-accessible API endpoint for product status, yay
    '''
    assert isinstance(product_ids, list)
    query = {'ProductSizeAndColor': {'productIds': ','.join(product_ids)}}
    data = {
        'data': '$b64$' + base64.b64encode(json.dumps(query)),
        'timestamp': str(js_timestamp_now())
    }
    ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36'
    j = None
    try:
        resp = requests.post('http://www.neimanmarcus.com/product.service',
            headers={
                'User-Agent': ua,
            },
            data=data,
            timeout=5)
        j = json.loads(resp.text)
        # bloody hell, they return stringified json inside more json. WTF
        j[u'ProductSizeAndColor'][u'productSizeAndColorJSON'] = json.loads(j[u'ProductSizeAndColor'][u'productSizeAndColorJSON'])
        j[u'ProductSizeAndColor'][u'utag__data__ajax'] = json.loads(j[u'ProductSizeAndColor'][u'utag__data__ajax'])
    except Exception as e:
        print e
    return j

#query_status(['prod175120147', 'prod170450177'])

'''
$ echo 'eyJQcm9kdWN0U2l6ZUFuZENvbG9yIjp7InByb2R1Y3RJZHMiOiJwcm9kMTc1MTIwMTQ3LHByb2QxNzA0NTAxNzcifX0' | base64 -D
{"ProductSizeAndColor":{"productIds":"prod175120147,prod170450177"

$ curl -L -D - -X POST -A 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36' --data 'data=$b64$eyJQcm9kdWN0U2l6ZUFuZENvbG9yIjp7InByb2R1Y3RJZHMiOiJwcm9kMTc1MTIwMTQ3LHByb2QxNzA0NTAxNzcifX0$&timestamp=1448417146604' 'http://www.neimanmarcus.com/product.service' | less

HTTP/1.1 200 OK
X-dynaTrace: PT=189802847;PA=1011939984;SP=NeimanMarcus;PS=-1852003431
dynaTrace: PT=189802847;PA=1011939984;SP=NeimanMarcus;PS=-1852003431
X-Powered-By: Servlet 2.5; JBoss-5.0/JBossWeb-2.1
P3P: CP="CAO DSP CURa TAIa PSAo PSDo CONi OUR DELa IND PHY ONL UNI PUR COM NAV INT CNT STA PRE"
ucid: c5442104-12a0-44ca-9b76-dadda0b0887c
Server-Info: nmoapp67_CPU2
Cache-Control: no-store
Pragma: no-cache
Content-Type: application/json;charset=ISO-8859-1
URL_LANGUAGE: (null)
URL_COUNTRY: (null)
X-FRAME-OPTIONS: SAMEORIGIN
Date: Wed, 25 Nov 2015 02:09:14 GMT
Content-Length: 6151
Connection: keep-alive
Set-Cookie: TLTSID=85602AB69319109380FAE098D0D81F6F; Path=/; Domain=.neimanmarcus.com
Set-Cookie: TLTUID=85602AB69319109380FAE098D0D81F6F; Path=/; Domain=.neimanmarcus.com; Expires=Wed, 25-11-2025 02:09:12 GMT
Set-Cookie: JSESSIONID=F0846206FD768D42936D8A1496440F96; Path=/
Set-Cookie: AGA=""; Domain=neimanmarcus.com; Expires=Mon, 13-Dec-2083 05:23:19 GMT; Path=/
Set-Cookie: ABTEST_COOKIE=33575544408; Domain=neimanmarcus.com; Expires=Mon, 13-Dec-2083 05:23:19 GMT; Path=/
Set-Cookie: ABTEST_COOKIE_CONFIRM=b2f33a6bb1e1ee6ede1d097337a1e03a; Domain=neimanmarcus.com; Expires=Mon, 13-Dec-2083 05:23:19 GMT; Path=/
Set-Cookie: AGA=7500001:7700001; Domain=neimanmarcus.com; Expires=Mon, 13-Dec-2083 05:23:19 GMT; Path=/
Set-Cookie: AGA=7500001:7700001; Domain=neimanmarcus.com; Expires=Mon, 13-Dec-2083 05:23:19 GMT; Path=/
Set-Cookie: W2A=3305963530.3930.0000; path=/
Set-Cookie: dtCookie=3315D58769171FF67D8A211608955837|Tk1PK1dOfDE; Path=/; Domain=.neimanmarcus.com
Set-Cookie: CChipCookie=2113994762.61525.0000; path=/
Set-Cookie: TS4c652b=de90b532bc5bd86a471acfc9c3c4cf886e70632f843f57e556551848286023f2202df50dec253180202df50d60ac0ec5af02a49b9a99de50afd006700541e4489a037ff03c25de05d506af3a61a4045b054e5da661a4045b054e5da621999737551de343219396cddd7869788524428a382d3cef; Path=/

{"ProductSizeAndColor":{"utag__data__ajax":"{\"product_cmos_sku\":[\"3656A653135161\"],\"stock_level\":[\"2\"],\"request_type\":\"link\",\"product_sellable_sku\":[\"true\"],\"product_showable\":[\"true\"],\"unsellable_skus\":\"true\",\"product_expected_availability\":[\"\"],\"product_inventory_status\":[\"Instock\"],\"ajax_response_id\":\"SKUData\"}","productIds":"prod175120147,prod170450177","productSizeAndColorJSON":"[{\"skus\":[{\"stockAvailable\":2,\"status\":\"In Stock\",\"availDate\":\"\",\"perishable\":false,\"suggestedInterval\":null,\"backOrderFlag\":false,\"storeFulfill\":false,\"sku\":\"sku155070449\",\"maxPurchaseQty\":9999,\"size\":\"PM (10\\\/12)\",\"defaultSkuColor\":false,\"cmosSku\":\"3656A653135161\",\"color\":\"DEEP CITRINE?null?false\",\"onlyXLeftMessage\":\"\",\"cmosItemCode\":\"T92ST\",\"deliveryDate\":\"Expected to ship no later than Date Unavailable\",\"availPlainDate\":\"\",\"stockLevel\":2,\"delivDays\":0}],\"productName\":\"Linen Jersey Box Top, Petite\",\"variationType\":3,\"restrictedDates\":[\"20160101\",\"20160530\",\"20160705\",\"20160704\",\"20151225\",\"20151226\",\"20160906\",\"20160531\",\"20160102\",\"20160905\",\"20151127\",\"20151126\"],\"productId\":\"prod175120147\"},{\"skus\":[{\"stockAvailable\":0,\"status\":\"Back Order\",\"availDate\":\"01\\\/25\\\/2016\",\"perishable\":false,\"suggestedInterval\":null,\"backOrderFlag\":false,\"storeFulfill\":false,\"sku\":\"sku149890131\",\"maxPurchaseQty\":9999,\"size\":\"2P\",\"defaultSkuColor\":false,\"cmosSku\":\"3656A4843F502P\",\"color\":\"AGED INDIGO?null?false\",\"onlyXLeftMessage\":\"\",\"cmosItemCode\":\"T892E\",\"deliveryDate\":\"Expected to ship no later than 01\\\/25\\\/2016\",\"availPlainDate\":\"01\\\/25\\\/2016\",\"stockLevel\":1,\"delivDays\":0},{\"stockAvailable\":9,\"status\":\"In Stock\",\"availDate\":\"\",\"perishable\":false,\"suggestedInterval\":null,\"backOrderFlag\":false,\"storeFulfill\":false,\"sku\":\"sku149890132\",\"maxPurchaseQty\":9999,\"size\":\"4P\",\"defaultSkuColor\":false,\"cmosSku\":\"3656A4843F504P\",\"color\":\"AGED INDIGO?null?false\",\"onlyXLeftMessage\":\"\",\"cmosItemCode\":\"T892E\",\"deliveryDate\":\"Expected to ship no later than Date Unavailable\",\"availPlainDate\":\"\",\"stockLevel\":9,\"delivDays\":0},{\"stockAvailable\":1,\"status\":\"In Stock\",\"availDate\":\"\",\"perishable\":false,\"suggestedInterval\":null,\"backOrderFlag\":false,\"storeFulfill\":false,\"sku\":\"sku149890133\",\"maxPurchaseQty\":9999,\"size\":\"6P\",\"defaultSkuColor\":false,\"cmosSku\":\"3656A4843F506p\",\"color\":\"AGED INDIGO?null?false\",\"onlyXLeftMessage\":\"Only 1 Left\",\"cmosItemCode\":\"T892E\",\"deliveryDate\":\"Expected to ship no later than Date Unavailable\",\"availPlainDate\":\"\",\"stockLevel\":1,\"delivDays\":0},{\"stockAvailable\":23,\"status\":\"In Stock\",\"availDate\":\"\",\"perishable\":false,\"suggestedInterval\":null,\"backOrderFlag\":false,\"storeFulfill\":false,\"sku\":\"sku149890134\",\"maxPurchaseQty\":9999,\"size\":\"8P\",\"defaultSkuColor\":false,\"cmosSku\":\"3656A4843F508p\",\"color\":\"AGED INDIGO?null?false\",\"onlyXLeftMessage\":\"\",\"cmosItemCode\":\"T892E\",\"deliveryDate\":\"Expected to ship no later than Date Unavailable\",\"availPlainDate\":\"\",\"stockLevel\":23,\"delivDays\":0},{\"stockAvailable\":0,\"status\":\"Back Order\",\"availDate\":\"01\\\/25\\\/2016\",\"perishable\":false,\"suggestedInterval\":null,\"backOrderFlag\":false,\"storeFulfill\":false,\"sku\":\"sku149890135\",\"maxPurchaseQty\":9999,\"size\":\"10P\",\"defaultSkuColor\":false,\"cmosSku\":\"3656A4843F510p\",\"color\":\"AGED INDIGO?null?false\",\"onlyXLeftMessage\":\"\",\"cmosItemCode\":\"T892E\",\"deliveryDate\":\"Expected to ship no later than 01\\\/25\\\/2016\",\"availPlainDate\":\"01\\\/25\\\/2016\",\"stockLevel\":4,\"delivDays\":0},{\"stockAvailable\":21,\"status\":\"In Stock\",\"availDate\":\"\",\"perishable\":false,\"suggestedInterval\":null,\"backOrderFlag\":false,\"storeFulfill\":false,\"sku\":\"sku149890136\",\"maxPurchaseQty\":9999,\"size\":\"12P\",\"defaultSkuColor\":false,\"cmosSku\":\"3656A4843F512p\",\"color\":\"AGED INDIGO?null?false\",\"onlyXLeftMessage\":\"\",\"cmosItemCode\":\"T892E\",\"deliveryDate\":\"Expected to ship no later than Date Unavailable\",\"availPlainDate\":\"\",\"stockLevel\":21,\"delivDays\":0},{\"stockAvailable\":2,\"status\":\"In Stock\",\"availDate\":\"\",\"perishable\":false,\"suggestedInterval\":null,\"backOrderFlag\":false,\"storeFulfill\":false,\"sku\":\"sku149890137\",\"maxPurchaseQty\":9999,\"size\":\"14P\",\"defaultSkuColor\":false,\"cmosSku\":\"3656A4843F514p\",\"color\":\"AGED INDIGO?null?false\",\"onlyXLeftMessage\":\"\",\"cmosItemCode\":\"T892E\",\"deliveryDate\":\"Expected to ship no later than Date Unavailable\",\"availPlainDate\":\"\",\"stockLevel\":2,\"delivDays\":0},{\"stockAvailable\":2,\"status\":\"In Stock\",\"availDate\":\"\",\"perishable\":false,\"suggestedInterval\":null,\"backOrderFlag\":false,\"storeFulfill\":false,\"sku\":\"sku149890138\",\"maxPurchaseQty\":9999,\"size\":\"16P\",\"defaultSkuColor\":false,\"cmosSku\":\"3656A4843F516p\",\"color\":\"AGED INDIGO?null?false\",\"onlyXLeftMessage\":\"\",\"cmosItemCode\":\"T892E\",\"deliveryDate\":\"Expected to ship no later than Date Unavailable\",\"availPlainDate\":\"\",\"stockLevel\":2,\"delivDays\":0},{\"stockAvailable\":0,\"status\":\"Back Order\",\"availDate\":\"01\\\/25\\\/2016\",\"perishable\":false,\"suggestedInterval\":null,\"backOrderFlag\":false,\"storeFulfill\":false,\"sku\":\"sku149890139\",\"maxPurchaseQty\":9999,\"size\":\"18P\",\"defaultSkuColor\":false,\"cmosSku\":\"3656A4843F518p\",\"color\":\"AGED INDIGO?null?false\",\"onlyXLeftMessage\":\"\",\"cmosItemCode\":\"T892E\",\"deliveryDate\":\"Expected to ship no later than 01\\\/25\\\/2016\",\"availPlainDate\":\"01\\\/25\\\/2016\",\"stockLevel\":1,\"delivDays\":0}],\"productName\":\"Stretch Boyfriend Jeans, Petite, Aged Indigo\",\"variationType\":3,\"restrictedDates\":[\"20160101\",\"20160530\",\"20160705\",\"20160704\",\"20151225\",\"20151226\",\"20160906\",\"20160531\",\"20160102\",\"20160905\",\"20151127\",\"20151126\"],\"productId\":\"prod170450177\"}]"}}
'''
