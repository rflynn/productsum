# ex: set ts=4 et:

'''
map a document archived from ssense.com to zero or more products
'''

from bs4 import BeautifulSoup
import json
from pprint import pprint
import re
import time
import traceback

from htmlmetadata import HTMLMetadata
from og import OG
from product import Product, ProductMapResultPage, ProductMapResult
from schemaorg import SchemaOrg
from util import nth, normstring


MERCHANT_SLUG = 'ssense'

class ProductSsense(object):
    VERSION = 0
    def __init__(self,
                 id=None,
                 canonical_url=None,
                 sku=None,
                 brand=None,
                 instock=None,
                 stocklevel=None,
                 name=None,
                 title=None,
                 descr=None,
                 price=None,
                 sale_price=None,
                 currency=None,
                 sizes=None,
                 img_url=None,
                 img_urls=None,
                 category=None,
                 material=None,
                 condition=None):
        self.id = id
        self.canonical_url = canonical_url
        self.sku = sku
        self.brand = brand
        self.instock = instock
        self.stocklevel = stocklevel
        self.name = name
        self.title = title
        self.descr = descr
        self.price = price
        self.sale_price = sale_price
        self.currency = currency
        self.sizes = sizes
        self.img_url = img_url
        self.img_urls = img_urls
        self.category = category
        self.material = material
        self.condition = condition

        if self.name:
            self.name = normstring(self.name)
        if self.title:
            self.title = normstring(self.title)
        if self.descr:
            self.descr = normstring(self.descr)

    def __repr__(self):
        return '''ProductSsense:
    id...............%s
    url..............%s
    sku..............%s
    brand............%s
    instock..........%s
    stocklevel.......%s
    name.............%s
    title............%s
    descr............%s
    price............%s
    sale_price.......%s
    currency.........%s
    sizes............%s
    img_url..........%s
    category.........%s
    material.........%s
    condition........%s
''' % (self.id,
       self.canonical_url,
       self.sku,
       self.brand,
       self.instock,
       self.stocklevel,
       self.name,
       self.title,
       self.descr,
       self.price,
       self.sale_price,
       self.currency,
       self.sizes,
       self.img_url,
       self.category,
       self.material,
       self.condition)

    def to_product(self):
        return Product(
            merchant_slug=MERCHANT_SLUG,
            url_canonical=self.canonical_url,
            merchant_sku=self.id,
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
            features=None,
            color=None,
            available_colors=None,
            size=None,
            available_sizes=self.sizes,
            img_url=self.img_url,
            img_urls=self.img_urls
        )


def get_meta_twitter(soup):

    t = {}

    # twitter card
    # ref: https://dev.twitter.com/cards/types/product
    # <meta property="twitter:card" content="product" />
    card = soup.find('meta', {'property': 'twitter:card'})
    if card:
        t['twitter:card'] = card.get('content')

    tags = soup.findAll(lambda tag: tag.name == 'meta' and tag.get('name') and tag.get('name').startswith('twitter:'))
    tm = {t.get('name'): t.get('content') for t in tags}
    # twitter is weird like this, mapping k:v pairs to 2 separate meta tags, yuck
    for i in xrange(len(tm) + 1):
        k = 'twitter:label%d' % i
        v = 'twitter:data%d' % i
        if k in tm and v in tm:
            t[tm[k]] = tm[v]
    return t


class ProductsSsense(object):

    VERSION = 0

    @classmethod
    def from_html(cls, url, html):

        starttime = time.time()

        products = []

        soup = BeautifulSoup(html)
        sp = SchemaOrg.get_schema_product(html)
        og = OG.get_og(soup)
        meta = HTMLMetadata.do_html_metadata(soup)
        tw = get_meta_twitter(soup)
        mp = {t['property']: t['content']
                    for t in soup.findAll('meta', content=True,
                                          property=re.compile('^product:'))}

        sel_size = soup.find('select', id='size')
        sizes = None
        if sel_size:
            try:
                sizes = sorted(normstring(re.sub('_.*', '', o['value'])) for o in
                                sel_size.findAll('option', value=True)
                                    if o['value']) or None
            except:
                traceback.print_exc()

        sp = sp[0] if sp else {}

        signals = {
            'sp':  SchemaOrg.to_json(sp),
            'og':  og,
            'meta':meta,
            'mp':  mp,
            'tw':  tw,
        }

        '''
<title>Jimmy Choo: Pink Snakeskin Anouk Pumps | SSENSE</title>
<meta name="description" content="Snake leather pumps in ballet pink and grey. Pointed toe. Leather sole in tan. Tonal stitching. Approx. 5" heel. " />
<meta name="twitter:card"                   content="product">
<meta name="twitter:site"                   content="@ssense">
<meta name="twitter:creator"                content="@ssense">
<meta name="twitter:domain"                 content="ssense.com">
<meta name="twitter:title"                  content="Jimmy Choo - Pink Snakeskin Anouk Pumps">
<meta name="twitter:description"            content="Snake leather pumps in ballet pink and grey. Pointed toe. Leather sole in tan. Tonal stitching. Approx. 5&quot; heel. ...">
<meta name="twitter:img:src"                content="https://res.cloudinary.com/ssenseweb/image/upload/b_white,c_lpad,g_center,h_960,w_960/c_scale,h_820/v402/52528F000027_1.jpg">
<meta name="twitter:label1"                 content="Price">
<meta name="twitter:data1"                  content="$398 USD">
<meta name="twitter:label2"                 content="Designer">
<meta name="twitter:data2"                  content="Jimmy Choo">

<meta property="og:title"                   content="Jimmy Choo - Pink Snakeskin Anouk Pumps" />
<meta property="og:site_name"               content="ssense"/>
<meta property="og:url"                     content="http://www.ssense.com/en-us/women/product/jimmy-choo/pink-snakeskin-anouk-pumps/1219383" />
<meta property="og:description"             content="Snake leather pumps in ballet pink and grey. Pointed toe. Leather sole in tan. Tonal stitching. Approx. 5" heel. " />
<meta property="og:type"                    content="product" />
<meta property="og:locale"                  content="en_US" />
<meta property="og:locale:alternate"        content="en_US" />
<meta property="og:image"                   content="https://res.cloudinary.com/ssenseweb/image/upload/b_white/v402/52528F000027_1.jpg" />
<meta property="product:price:amount"       content="398.00"/>
<meta property="product:price:currency"     content="USD"/>
<meta property="product:age_group"          content="adult" />
<meta property="product:availability"       content="instock" />
<meta property="product:brand"              content="Jimmy Choo" />
<meta property="product:category"           content="Heels" />
<meta property="product:condition"          content="new" />
<meta property="product:material"           content="Upper: elaphe leather. Sole: leather." />
        '''

        prodid = nth(sp.get('sku'), 0) or None

        # is there one or more product on the page?
        if prodid:

            try:
                spoffer = sp['offers'][0]['properties']
            except:
                spoffer = {}

            p = ProductSsense(
                id=prodid,
                canonical_url=url,
                sku=nth(sp.get(u'sku'), 0) or None,
                brand=(nth(sp.get('brand'), 0)
                        or mp.get('product:brand')
                        or tw.get('Designer')
                        or None),
                instock=(mp['product:availability'].lower() == 'instock'
                            if 'product:availability' in mp else None) or None,
                stocklevel=None,
                name=(nth(sp.get(u'name'), 0)
                        or og.get('title')
                        or meta.get('title') or None),
                title=(og.get('title')
                        or meta.get('title')
                        or None),
                descr=(nth(sp.get(u'description'), 0)
                        or og.get('description')
                        or meta.get('description') or None),
                sale_price=(mp.get('product:price:amount')
                        or nth(spoffer.get('price'), 0)
                        or tw.get('Price')
                        or None),
                price=(mp.get('product:price:amount')
                        or nth(spoffer.get('price'), 0)
                        or tw.get('Price')
                        or None),
                currency=nth(spoffer.get('priceCurrency'), 0) or None,
                sizes=sizes or None,
                img_url=(og.get('image')
                        or tw.get('img:src') or None),
                category=mp.get('product:category') or None,
                material=mp.get('product:material') or None,
                condition=mp.get('product:condition') or None
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


if __name__ == '__main__':

    import gzip

    url = 'https://www.ssense.com/en-us/women/product/jimmy-choo/pink-snakeskin-anouk-pumps/1219383'
    filepath = 'test/www.ssense.com-en-us-women-product-jimmy-choo-pink-snakeskin-anouk-pumps-1219383.gz'

    with gzip.open(filepath) as f:
        html = f.read()

    products = ProductsSsense.from_html(url, html)
    print products
