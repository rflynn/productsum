# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from yoox.com to zero or more products
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
from util import nth, normstring, xint, xboolstr, maybe_join, dehtmlify


class ProductYoox(object):
    def __init__(self, prodid=None, canonical_url=None,
                 stocklevel=None, instock=None,
                 price=None, sale_price=None, currency=None,
                 brand=None, category=None, bread_crumb=None,
                 name=None, title=None, descr=None,
                 features=None, size=None, sizes=None,
                 img_url=None):

        assert prodid is None or isinstance(prodid, basestring)
        assert canonical_url is None or isinstance(canonical_url, basestring)
        assert stocklevel is None or isinstance(stocklevel, int)
        assert instock is None or isinstance(instock, bool)
        assert brand is None or isinstance(brand, basestring)
        assert category is None or isinstance(category, basestring)
        assert bread_crumb is None or isinstance(bread_crumb, list)
        assert price is None or isinstance(price, basestring)
        assert sale_price is None or isinstance(price, basestring)
        assert currency is None or isinstance(currency, basestring)
        assert name is None or isinstance(name, basestring)
        assert title is None or isinstance(title, basestring)
        assert descr is None or isinstance(descr, basestring)
        assert features is None or isinstance(features, list)
        assert size is None or isinstance(size, basestring)
        assert sizes is None or isinstance(sizes, list)
        assert img_url is None or isinstance(img_url, basestring)

        self.prodid = prodid
        self.canonical_url = canonical_url
        self.stocklevel = stocklevel
        self.instock = instock
        self.price = price
        self.sale_price = sale_price
        self.currency = currency
        self.brand = normstring(brand)
        self.category = category
        self.bread_crumb = bread_crumb
        self.name = normstring(name)
        self.title = normstring(title)
        self.descr = descr
        self.features = features
        self.size = size
        self.sizes = sizes
        self.img_url = img_url

        # fixups
        if self.price:
            self.price = re.sub('\s+', '', self.price)

    def __repr__(self):
        return '''ProductYoox(
    prodid........%s
    url...........%s
    instock.......%s
    stocklevel....%s
    price.........%s
    sale_price....%s
    currency......%s
    brand.........%s
    category......%s
    bread_crumb...%s
    name..........%s
    title.........%s
    descr.........%s
    features......%s
    size..........%s
    sizes.........%s
    img_url.......%s
)''' % (self.prodid, self.canonical_url,
       self.instock, self.stocklevel,
       self.price, self.sale_price, self.currency,
       self.brand, self.category, self.bread_crumb, 
       self.name, self.title, self.descr,
       self.features, self.size, self.sizes,
       self.img_url)

    def to_product(self):

        return Product(
            merchant_slug='yoox',
            url_canonical=self.canonical_url,
            merchant_sku=str(self.prodid),
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
            color=None,
            available_colors=None,
            size=self.size,
            available_sizes=self.sizes,
            img_urls=[self.img_url] if self.img_url else None
        )


class ProductsYoox(object):

    @staticmethod
    def from_html(url, html):

        starttime = time.time()

        soup = BeautifulSoup(html)
        sp = SchemaOrg.get_schema_product(html)
        og = OG.get_og(soup)
        meta = HTMLMetadata.do_html_metadata(soup)
        custom = ProductsYoox.get_custom(soup, og)

        sp = sp[0] if sp else {}

        signals = {
            'sp':   SchemaOrg.to_json(sp),
            'og':   og,
            'meta': meta,
            'custom': custom,
        }
        #pprint(signals)

        products = []

        prodid = custom.get('prodid') or None

        # is there one or more product on the page?
        if prodid:

            offerprop = {}
            try:
                offerprop = nth(sp.get('offers'), 0)['properties']
            except:
                pass

            p = ProductYoox(
                prodid=prodid,
                canonical_url=custom.get('url_canonical') or og.get('url') or url,
                stocklevel=custom.get('stock_level'),
                instock=custom.get('in_stock') or og.get('availability') in ('instock',),
                price=(nth(offerprop.get('price'), 0)
                        or custom.get('price')
                        or og.get('price:amount') or None),
                sale_price=custom.get('sale_price') or None,
                currency=nth(offerprop.get('priceCurrency'), 0) or None,
                brand=nth(sp.get(u'brand'), 0) or og.get('brand') or custom.get('brand') or None,
                category=custom.get('category'),
                bread_crumb=custom.get('bread_crumb') or None,
                name=(nth(sp.get('name'), 0)
                        or custom.get('name')
                        or og.get('title')
                        or meta.get('title') or None),
                title=og.get('title') or meta.get('title') or None,
                descr=maybe_join(' ', sp.get('description')) or custom.get('descr') or og.get('description') or meta.get('description') or None,
                features=custom.get('features') or None,
                size=custom.get('size') or None,
                sizes=custom.get('sizes') or None,
                img_url=og.get('image') or None,
            )
            products.append(p)

        realproducts = [p.to_product() for p in products]

        page = ProductMapResultPage(
                 merchant_slug='yoox',
                 url=url,
                 size=len(html),
                 proctime = time.time() - starttime,
                 signals=signals)

        return ProductMapResult(page=page,
                                products=realproducts)


    @staticmethod
    def get_tcvars(soup):
        '''
<script>

    ...

    //****************************************************************//
    //TAG Commander Variables stuffing
    //Product
    tc_vars["product_cod8"] = "44943424";
    tc_vars["product_cod10"] = "44943424XH";
    tc_vars["product_brand"] = "JIMMY CHOO LONDON";
    tc_vars["product_brand_id"] = "443";
    tc_vars["product_category"] = "Pump";
    tc_vars["product_category_code"] = "dcllts";
    tc_vars["product_author"] = "";
    tc_vars["product_title"] = "";
    tc_vars["product_price"] = "427";
    tc_vars["product_discountprice"] = "427";
    tc_vars["product_url"] = "/us/44943424XH/item#sts=women";
    tc_vars["product_url_picture"] = "http://images.yoox.com/44/44943424xh_14_f.jpg";
    tc_vars["product_instock_num"] = "1";
</script>
        '''
        tc_vars = {}
        tag = soup.find('script', text=lambda t: t and re.search(r'tc_vars\[.+?\] =', t))
        #print 'tag:'
        #pprint(tag)
        if tag and hasattr(tag, 'text'):
            m = re.findall(r'tc_vars\[.+?\] = .*;', tag.text)
            #print 'tc_vars:'
            #pprint(m)
            if m:
                try:
                    lolsource = 'tc_vars={};' + '\n'.join(m) + '; return tc_vars;'
                    tc_vars = execjs.exec_(lolsource) # o_O
                except execjs.ProgramError as e:
                    print e # not surprised by these...
                except Exception as e:
                    traceback.print_exc()
        return tc_vars 

    @staticmethod
    def get_custom(soup, og):

        tc_vars = ProductsYoox.get_tcvars(soup)

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

        name = None
        tag = soup.find(itemprop='name')
        if tag and hasattr(tag, 'text'):
            name = normstring(tag.text)

        price = None
        tag = soup.find(itemprop='brand')
        if tag and hasattr(tag, 'text'):
            price = normstring(tag.text)

        # an actual description
        descr = None
        tag = soup.find(itemprop='description')
        if tag:
            descr = tag.text
        # even better description...
        tag = soup.find('div', class_='panel-body')
        if tag:
            descr = normstring(tag.text)
        if descr and descr.endswith('Read More >'):
            descr = descr[:-11]

        # features
        features = None
        tag = soup.find(id='collapseGlance')
        if tag:
            features = [normstring(t.text.replace('\n',' '))
                            for t in tag.findAll(class_='prd') or []]

        bread_crumb = None
        tag = soup.find('div', id='breadcrumbs')
        if tag:
            bread_crumb = [normstring(a.text)
                            for a in tag.findAll('a', href=True)
                                if a and hasattr(a, 'text')]

        brand = tc_vars.get('product_brand') or None

        category = None
        if bread_crumb and brand:
            if bread_crumb[-1] == brand:
                category = bread_crumb[-2]

        stock_level = xint(tc_vars.get('product_instock_num'))

        '''
        <ul class="colorsizelist">
            <li id="size13" class="floatLeft" title="10 (US Size)">10</li>
        </ul>
        '''
        sizes = None
        try:
            sizes = [normstring(li.text)
                        for li in soup.select('ul.colorsizelist > li[id^="size"]')
                            if li and li.text] or None
        except:
            pass

        data = {
            'url_canonical': url_canonical,
            'prodid': tc_vars.get('product_cod10') or None,
            'prodid_8': tc_vars.get('product_cod8') or None,
            'prodid_10': tc_vars.get('product_cod10') or None,
            'bread_crumb': bread_crumb,
            'category': tc_vars.get('product_category') or category or None,
            'brand': brand,
            'price': price or tc_vars.get('product_price') or None,
            'sale_price': tc_vars.get('product_discountprice') or None,
            'img_url': tc_vars.get('product_url_picture') or None,
            'stock_level': stock_level or None,
            'in_stock': bool(stock_level),
            'name': name,
            'title': tc_vars.get('product_title') or None,
            'descr': descr,
            'features': features,
            'sizes': sizes,
            'tc_vars': tc_vars,
        }
        return data


if __name__ == '__main__':

    url = 'http://www.yoox.com/us/44943424XH/item'
    # test no-op
    #filepath = 'www.dermstore.com-product_Lipstick_31136.htm.gz'

    #filepath = 'www.yoox.com-us-44848938PU-item.gz'
    filepath = 'www.yoox.com-us-44814772VC-item.gz'

    with gzip.open(filepath) as f:
        html = f.read()

    products = ProductsYoox.from_html(url, html)
    print products
