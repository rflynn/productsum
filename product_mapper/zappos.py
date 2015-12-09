# ex: set ts=4 et:
# -*- coding: utf-8 *-*

'''
map a document archived from zappos.com to zero or more products
'''

from bs4 import BeautifulSoup
import execjs
import json
from pprint import pprint
import re
import time
import traceback

from htmlmetadata import HTMLMetadata
from og import OG
from product import Product, ProductMapResultPage, ProductMapResult
from schemaorg import SchemaOrg
from tealium import Tealium
from util import nth, normstring, xboolstr, u


class ProductZappos(object):
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

        if self.title and self.title.endswith(' | SHOPBOP'):
            self.title = self.title[:-11]

    def __repr__(self):
        return '''ProductZappos:
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
            merchant_slug='zappos',
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


def get_custom(soup):

    product = {}

    prodid = None
    brand = None
    name = None
    in_stock = None
    price = None
    currency = None
    size = None
    sizes = None
    color = None
    colors = None
    img_url = None
    img_urls = None

    '''
    <meta itemtype="brand" content="Converse">
    '''
    tag = soup.find('meta', itemtype='brand', content=True)
    if tag:
        brand = normstring(tag.get('content')) or None

    '''
    <span id="sku"> SKU <span itemprop="sku">108000</span></span>
    '''
    tag = soup.find('span', itemprop='sku')
    if tag:
        prodid = normstring(tag.get_text())
    if not prodid:
        '''
        <input type="hidden" name="productId" value="108000" />
        '''
        tag = soup.find('input',
                 attrs={'type': 'hidden', 'name': 'productId', 'value': True})
        if tag:
            prodid = normstring(tag.get_text())
 
    '''
<div itemprop="description">
<ul class="product-description">
<li class="video"><a class="prDescVideo" href="http://www.zappos.com/multiview/108000/3#autoplay" id="video-description"><img src="http://www.zappos.com/imgs/video/play.png" alt
="Video Description"><strong style="font-weight: normal;"> View the Video Description</a> for this product!</strong> (Please note that the color shown in the video may no longer
 be available.)</li>
<li><strong>Please select 1/2 size down from your normal size</strong> (if you wear Men's size 9, please choose Men's size 8.5, and if you wear a Women's size 8, please choose W
omen's 7.5).*</li>
<li><strong>Sizes Men's 3/Women's 5 - Men's 8/Women's 10 feature 6 eyelets, while sizes Men's 8.5/Women's 10.5 and up feature 7 eyelets.</strong></li>
<li><strong><em>Please note: The Charcoal style used to be the A/S Seasonal Ox, but it is now All Star Core Ox. Some shoe boxes may have the old title, while others have the upd
ated title.</em></strong></li>
<li>The original basketball shoe is now defined as a stylish modern-day fashion staple! The All Star&reg; Core Ox from <a class="zph" href="/converse">Converse</a>&reg; is a gre
at complement to any casual ensemble.</li>
<li>Durable canvas upper.</li>
<li>Lace-up front with metal eyelets.</li>
<li>Canvas lining and a cushioned footbed provides hours of comfort.</li>
<li>Original rubber toe box and toe guard, tonal sidewall trim and All Star&reg; heel patch.</li>
<li>Signature <a class="zph" href="/converse">Converse</a>&reg; rubber outsole.</li>
<li>Imported.</li>
<li class="measurements">Measurements:
<ul>
<li> Weight: 15 oz</li>
</ul>
</li>
<li>Product measurements were taken using size Men's 9, Women's 11, width Medium. Please note that measurements may vary by size.</li>
</ul>
</div>
    '''
    
    tag = soup.find('span', attrs={'class': 'price'})
    if tag:
        price = normstring(tag.get_text()) or None

    tags = soup.find('select', id='color')
    if tags:
        opts = tags.findAll('option', value=True)
        colors = [normstring(t.get_text()) for t in opts]

    tags = soup.find('select', id='d3')
    if tags:
        opts = tags.findAll('option', value=True)
        sizes = [normstring(t.get_text())
                    for i, t in enumerate(opts)
                        if i > 0]

    '''
<script type="text/javascript">
// Product page private namespace
// TODO: use this for more private variables on the page
var _p = _p || {};
var isProductPage = true;
var styleId = 15648;
var productId = 108000;
var productName = "Chuck Taylor® All Star® Core Ox";
var brandId = 36;
var brandName = "Converse";
var productTypeId = 1;
var productGender = "Mens";
var zetaCategories = [ {"27567": "Shoes"},
{"27580": "Sneakers & Athletic Shoes"}
];
var prodgroupkill = false;
var curStyle = styleId;
var videos = {
'mp4' : '1/0/8/108000.mp4'
,
'flv' : '1/0/8/108000.flv'
};
var category, subCategory;
category = "Shoes";
subCategory = "Sneakers and Athletic Shoes";
    '''
    tag = soup.find('script', text=lambda t: t and 'var isProductPage')

    product = {
        'prodid': prodid,
        'brand': brand,
        'name': name,
        'in_stock': in_stock,
        'price': price,
        'currency': currency,
        'size': size,
        'sizes': sizes,
        'color': color,
        'colors': colors,
        'img_url': img_url,
        'img_urls': img_urls,
    }
    pprint(product)
    return product


class ProductsZappos(object):

    @staticmethod
    def from_html(url, html):

        starttime = time.time()

        products = []

        soup = BeautifulSoup(html)
        meta = HTMLMetadata.do_html_metadata(soup)
        sp = SchemaOrg.get_schema_product(html)
        og = OG.get_og(soup)
        custom = get_custom(soup)

        sp = sp[0] if sp else {}

        signals = {
            'meta':meta,
            'sp':  SchemaOrg.to_json(sp),
            'og':  og,
            'custom': custom,
        }
        pprint(signals)

        prodid = custom.get('prodid') or None

        # is there one or more product on the page?
        if prodid:
            p = ProductZappos(
                prodid=prodid,
                canonical_url=url,
                brand=u(custom.get('brand')) or None,
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
                descr=u(nth(sp.get(u'description'), 0)
                        or og.get('description')
                        or meta.get('description') or None),
                sale_price=custom.get('sale_price') or None,
                price=u(custom.get('price')
                       or og.get('price:amount') or None),
                currency=custom.get('currency') or og.get('price:currency') or None,
                size=custom.get('size') or None,
                sizes=custom.get('sizes') or None,
                color=u(custom.get('color')) or None,
                colors=custom.get('colors') or None,
                img_url=u(custom.get('img_url')
                            or og.get('image')
                            or nth(sp.get('image'), 0) or None),
                img_urls=custom.get('img_urls') or None,
            )
            products.append(p)

        realproducts = [p.to_product() for p in products]

        page = ProductMapResultPage(
                    merchant_slug='zappos',
                    url=url,
                    size=len(html),
                    proctime = time.time() - starttime,
                    signals=signals)

        return ProductMapResult(page=page,
                                products=realproducts)


if __name__ == '__main__':

    import gzip

    url = 'http://www.zappos.com/converse-chuck-taylor-all-star-core-ox-black'
    filepath = 'test/www.zappos.com-converse-chuck-taylor-all-star-core-ox-black.gz'

    # test no-op
    #filepath = 'test/www.dermstore.com-product_Lipstick_31136.htm.gz'

    with gzip.open(filepath) as f:
        html = unicode(f.read(), 'utf8')

    products = ProductsZappos.from_html(url, html)
    print products
