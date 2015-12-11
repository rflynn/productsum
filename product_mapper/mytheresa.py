# ex: set ts=4 et:
# -*- coding: utf-8 *-*

'''
map a document archived from mytheresa.com to zero or more products
'''

from bs4 import BeautifulSoup
import execjs
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
from util import nth, normstring, xboolstr, u


def handle_color(c):
    if c is None:
        return c
    if isinstance(c, basestring):
        return c
    if isinstance(c, list):
        # some multi-color items get a list...
        c = [x for x in c
                if x and isinstance(x, basestring)] # sanitize
        if not c:
            return None
        if len(c) == 1:
            return c[0]
        if len(c) == 2:
            return c[0].title() + u' and ' + c[1].title()
        if len(c) >= 3:
            return u', '.join([x.title() for x in c])
    raise Exception(str(c))


class ProductMyTheresa(object):
    VERSION = 0
    def __init__(self,
                 prodid=None,
                 canonical_url=None,
                 brand=None,
                 instock=None,
                 stocklevel=None,
                 price=None,
                 sale_price=None,
                 currency=None,
                 name=None,
                 title=None,
                 descr=None,
                 features=None,
                 color=None,
                 colors=None,
                 size=None,
                 sizes=None,
                 img_url=None,
                 img_urls=None,
                 category=None,
                 category_id=None,
                 department=None):

        assert isinstance(prodid, basestring)

        self.prodid = prodid
        self.canonical_url = canonical_url
        self.brand = brand
        self.instock = instock
        self.stocklevel = stocklevel
        self.price = price
        self.sale_price = sale_price
        self.currency = currency
        self.name = normstring(name)
        self.title = normstring(title)
        self.descr = normstring(descr)
        self.features = features
        self.color = color
        self.colors = colors
        self.size = size
        self.sizes = sizes
        self.img_url = img_url
        self.img_urls = img_urls
        self.category = category
        self.category_id = category_id
        self.department = department

        '''
        ◊ Christian Louboutin » mytheresa.com
        '''
        if self.descr:
            if ' ... ' in self.descr:
                self.descr = self.descr[:self.descr.index(' ... ')]
            if self.descr.endswith(','):
                self.descr = self.descr.rstrip(', ') + '.'

    def __repr__(self):
        return '''ProductMyTheresa:
    prodid...........%s
    url..............%s
    brand............%s
    instock..........%s
    stocklevel.......%s
    price............%s
    sale_price.......%s
    currency.........%s
    name.............%s
    title............%s
    descr............%s
    features.........%s
    color............%s
    colors...........%s
    size.............%s
    sizes............%s
    img_url..........%s
    img_urls.........%s
    category.........%s
    category_id......%s
    department.......%s
''' % (self.prodid,
       self.canonical_url,
       self.brand,
       self.instock,
       self.stocklevel,
       self.price,
       self.sale_price,
       self.currency,
       self.name,
       self.title,
       self.descr,
       self.features,
       self.color,
       self.colors,
       self.size,
       self.sizes,
       self.img_url,
       self.img_urls,
       self.category,
       self.category_id,
       self.department)

    def to_product(self):
        return Product(
            merchant_slug='mytheresa',
            url_canonical=self.canonical_url,
            merchant_sku=self.prodid,
            merchant_product_obj=self,
            price=self.price,
            sale_price=self.sale_price,
            currency=self.currency,
            category=self.category,
            brand=self.brand,
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
            img_url=self.img_url,
            img_urls=self.img_urls
        )


def get_custom(soup, orig_url):

    product = {}

    prodid = None
    url = None
    brand = None
    in_stock = None
    stock_level = None
    price = None
    currency = None
    name = None
    descr = None
    size = None
    sizes = None
    color = None
    colors = None
    img_url = None
    img_urls = None

    '''
    <div class="product-sku">
        <span class="h1">item no.&nbsp;P00163941</span>
    </div>
    '''
    tag = soup.find('div', attrs={'class': 'product-sku'})
    if tag:
        try:
            m = re.search(r'item no\..(P[0-9]{4,12})', tag.text)
            if m:
                prodid = m.groups(0)[0]
        except:
            traceback.print_exc()

    '''
<script type="application/ld+json">[{"@context":"http:\/\/schema.org","@type":"Product","name":"Pigalle Follies 100 patent leather pumps","description":"Christian Louboutin is r
enowned for his footwear designs and iconic red leather sole. Taking on a girly charm, the classic 'Pigalle Follies' pumps are swathed in a bubblegum pink high-shine patent leat
her, which contrasts against that iconic bright red sole. Keep the look feminine and team with a floral dress.","color":"pink","manufacturer":"Christian Louboutin","sku":"P00163
941","url":"http:\/\/www.mytheresa.com\/en-de\/pigalle-follies-100-patent-leather-pumps-513456.html","image":"\/\/i.mytheresa.com\/544\/544\/90\/jpeg\/catalog\/product\/12\/P001
63941-Pigalle-Follies-100-patent-leather-pumps-STANDARD.jpg","brand":{"@type":"Brand","name":"Christian Louboutin","image":"","url":"http:\/\/www.mytheresa.com\/en-de\/designers
\/christian-louboutin.html"},"offers":{"@type":"Offer","availability":"http:\/\/schema.org\/InStock","price":515,"priceCurrency":"EUR"},"isConsumableFor":[{"@context":"http:\/\/
schema.org","@type":"Product","name":"Knot satin and snakeskin clutch","description":null,"color":false,"manufacturer":"Bottega Veneta","sku":"P00163879","url":null,"image":"\/\
/i.mytheresa.com\/544\/544\/90\/jpeg\/catalog\/product\/7a\/P00163879-Knot-satin-and-snakeskin-clutch-STANDARD.jpg","brand":{"@type":"Brand","name":"Bottega Veneta","image":"","
url":"http:\/\/www.mytheresa.com\/en-de\/catalog\/category\/view\/"},"offers":{"@type":"Offer","availability":"http:\/\/schema.org\/OutOfStock","price":"1400.0000","priceCurrenc
y":"EUR"}},{"@context":"http:\/\/schema.org","@type":"Product","name":"Embroidered tulle dress","description":null,"color":false,"manufacturer":"Fendi","sku":"P00173517","url":n
ull,"image":"\/\/i.mytheresa.com\/544\/544\/90\/jpeg\/catalog\/product\/e4\/P00173517--STANDARD.jpg","brand":{"@type":"Brand","name":"Fendi","image":"","url":"http:\/\/www.mythe
resa.com\/en-de\/catalog\/category\/view\/"},"offers":{"@type":"Offer","availability":"http:\/\/schema.org\/OutOfStock","price":"1800.0000","priceCurrency":"EUR"}}]},{"@context"
:"http:\/\/schema.org","@type":"Organization","name":"mytheresa.com","url":"http:\/\/www.mytheresa.com\/","contactPoint":{"@type":"ContactPoint","telephone":"+49 89 127695-100",
"contactType":"customer service"},"sameAs":["https:\/\/twitter.com\/mytheresa_com","https:\/\/www.pinterest.com\/mytheresacom\/","https:\/\/www.facebook.com\/mytheresa"]},{"@con
text":"http:\/\/schema.org","@type":"WebSite","name":"mytheresa.com","url":"http:\/\/www.mytheresa.com\/","potentialAction":{"@type":"SearchAction","target":"http:\/\/www.myther
esa.com\/en-de\/catalogsearch\/result\/?q={search_term}","query-input":"required name=search_term"}},{"@context":"http:\/\/schema.org","@type":"BreadcrumbList","itemListElement"
:[{"@type":"ListItem","position":1,"item":{"@id":"http:\/\/www.mytheresa.com\/en-de\/","name":"Home"}},{"@type":"ListItem","position":2,"item":{"@id":"http:\/\/www.mytheresa.com
\/en-de\/designers\/christian-louboutin.html","name":"Christian Louboutin"}},{"@type":"ListItem","position":3,"item":{"@id":"http:\/\/www.mytheresa.com\/en-de\/shoes.html","name
":"Shoes"}},{"@type":"ListItem","position":4,"item":{"@id":"http:\/\/www.mytheresa.com\/en-de\/shoes\/pumps.html","name":"Pumps"}},{"@type":"ListItem","position":5,"item":{"@id"
:"http:\/\/www.mytheresa.com\/en-de\/shoes\/pumps\/high-heel.html","name":"High-heel"}},{"@type":"ListItem","position":6,"item":{"@id":null,"name":"Pigalle Follies 100 patent le
ather pumps"}}]}]</script>
    '''
    tag = soup.find('script', type='application/ld+json')
    if tag:
        try:
            obj = json.loads(tag.text)
            #pprint(obj)
            o = obj[0]
            prodid = prodid or o.get('sku')
            name = o.get('name')
            descr = o.get('description')
            color = o.get('color')
            url = o.get('url')
            if url:
                try:
                    url = urljoin(orig_url, url) # ensure absolute
                except:
                    traceback.print_exc()
            if 'brand' in o:
                brand = o['brand'].get('name')
            if not brand:
                brand = brand or o.get('manufacturer')
            if 'offers' in o:
                price = str(o['offers'].get('price'))
                currency = o['offers'].get('priceCurrency')
                in_stock = o['offers'].get('availability') == 'http://schema.org/InStock'
        except:
            traceback.print_exc()

    '''
    <script type="text/javascript">
        ...
        optionsProduct = {
            ...
    '''
    tag = soup.find('script', text=lambda t: t and 'optionsProduct = {' in t)
    if tag:
        m = re.search('optionsProduct\s*=\s*({.*})\s*;', tag.text, re.DOTALL)
        if m:
            try:
                objstr = m.group(1)
                #print objstr
                obj = json.loads(objstr)
                #pprint(obj)
                if obj:
                    # they're all the same...
                    anyofthem = obj.values()[0]
                    prodid = prodid or anyofthem.get('sku')
                    brand = anyofthem.get('designer')
                    name = anyofthem.get('name')
                    img_url = anyofthem.get('image')
                    img_urls = [img_url] # all the same...
                    sizes = sorted(v.get('size')
                                        for v in obj.values()
                                            if v.get('size'))
                    if sizes:
                        if sizes == ['-']:
                            sizes = ['One size fits all']
                    def stocklevel_translate(s):
                        if s is False:
                            return 0
                        if s == u'only one piece left':
                            return 1
                        if s == u'only a few pieces left':
                            return 3 # arbitrary...
                        return 10 # arbitrary...
                    stock_level = sum(stocklevel_translate(s.get('stocklevel'))
                                        for s in obj.values())
                    if in_stock is None:
                        in_stock = stock_level > 0
            except:
                traceback.print_exc()

    product = {
        'prodid': prodid,
        'url': url,
        'brand': brand,
        'in_stock': in_stock,
        'stock_level': stock_level,
        'price': price,
        'currency': currency,
        'name': name,
        'descr': descr,
        'size': size,
        'sizes': sizes,
        'color': color,
        'colors': colors,
        'img_url': img_url,
        'img_urls': img_urls,
    }
    #pprint(product)
    return product


class ProductsMyTheresa(object):

    @staticmethod
    def from_html(url, html):

        starttime = time.time()

        products = []

        soup = BeautifulSoup(html)
        meta = HTMLMetadata.do_html_metadata(soup)
        sp = SchemaOrg.get_schema_product(html)
        og = OG.get_og(soup)
        custom = get_custom(soup, url)

        sp = sp[0] if sp else {}

        signals = {
            'meta':meta,
            'sp':  SchemaOrg.to_json(sp),
            'og':  og,
            'custom': custom,
        }
        #pprint(signals)

        prodid = custom.get('prodid') or nth(sp.get('sku'), 0) or None

        # is there one or more product on the page?
        if prodid:
            p = ProductMyTheresa(
                prodid=prodid,
                canonical_url=custom.get('url') or url,
                brand=u(nth(sp.get('brand'), 0) or custom.get('brand')) or None,
                instock=(custom.get('in_stock')
                            or og.get('availability') == u'instock' or None),
                stocklevel=custom.get('stock_level'),
                name=u(nth(sp.get(u'name'), 0)
                        or custom.get('name')
                        or og.get('title')
                        or meta.get('title') or None),
                title=u(og.get('title')
                        or meta.get('title')
                        or None),
                descr=u(custom.get('descr')
                        or meta.get('description') # this is better than sp and og
                        or nth(sp.get(u'description'), 0)
                        or og.get('description')
                        or None),
                sale_price=custom.get('sale_price') or None,
                price=u(custom.get('price')
                       or og.get('price:amount') or None),
                currency=custom.get('currency') or og.get('price:currency') or None,
                size=custom.get('size') or None,
                sizes=custom.get('sizes') or None,
                color=u(handle_color(nth(sp.get('color'), 0) or custom.get('color'))) or None,
                colors=custom.get('colors') or None,
                img_url=u(custom.get('img_url')
                            or og.get('image')
                            or nth(sp.get('image'), 0) or None),
                img_urls=custom.get('img_urls') or None,
            )
            products.append(p)

        realproducts = [p.to_product() for p in products]

        page = ProductMapResultPage(
                    merchant_slug='mytheresa',
                    url=url,
                    size=len(html),
                    proctime = time.time() - starttime,
                    signals=signals)

        return ProductMapResult(page=page,
                                products=realproducts)


if __name__ == '__main__':

    import gzip

    url = 'http://www.mytheresa.com/en-de/pigalle-follies-100-patent-leather-pumps-513456.html'
    filepath = 'test/www.mytheresa.com-en-de-pigalle-follies-100-patent-leather-pumps-513456.html.gz'

    url = 'http://www.mytheresa.com/en-de/dottie-silk-blouse.html'
    filepath = 'test/www.mytheresa.com-en-de-dottie-silk-blouse.html.gz'

    url = 'http://www.mytheresa.com/en-de/leather-wallet-468258.html'
    filepath = 'test/www.mytheresa.com-en-de-leather-wallet-468258.html.gz'

    # test no-op
    #filepath = 'test/www.dermstore.com-product_Lipstick_31136.htm.gz'

    with gzip.open(filepath) as f:
        html = unicode(f.read(), 'utf8')

    products = ProductsMyTheresa.from_html(url, html)
    print products
