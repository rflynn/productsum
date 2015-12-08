# ex: set ts=4 et:
# -*- coding: utf-8 -*-

'''
map a document archived from revolveclothing.com to zero or more products
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
from util import flatten, nth, xstrip, normstring, xint, xboolstr, maybe_join, dehtmlify


class ProductFwrd(object):
    def __init__(self, prodid=None, canonical_url=None,
                 stocklevel=None, instock=None,
                 price=None, sale_price=None, currency=None,
                 brand=None, category=None, bread_crumb=None,
                 name=None, title=None, descr=None,
                 features=None, size=None, sizes=None,
                 color=None, colors=None,
                 img_url=None, img_urls=None):

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
        assert color is None or isinstance(color, basestring)
        assert colors is None or isinstance(colors, list)
        assert img_url is None or isinstance(img_url, basestring)
        assert img_urls is None or isinstance(img_urls, list)

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
        self.color = color
        self.colors = colors
        self.img_url = img_url
        self.img_urls = img_urls

    def __repr__(self):
        return '''ProductFwrd(
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
    color.........%s
    colors........%s
    img_url.......%s
    img_urls......%s
)''' % (self.prodid, self.canonical_url,
       self.instock, self.stocklevel,
       self.price, self.sale_price, self.currency,
       self.brand, self.category, self.bread_crumb,
       self.name, self.title, self.descr,
       self.features, self.size, self.sizes,
       self.color, self.colors,
       self.img_url, self.img_urls)

    def to_product(self):

        return Product(
            merchant_slug='fwrd',
            url_canonical=self.canonical_url,
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
            available_colors=self.colors,
            size=self.size,
            available_sizes=self.sizes,
            img_url=self.img_url,
            img_urls=self.img_urls
        )


class ProductsFwrd(object):

    @staticmethod
    def from_html(url, html):

        starttime = time.time()

        soup = BeautifulSoup(html)
        meta = HTMLMetadata.do_html_metadata(soup)
        og = OG.get_og(soup)
        sp = SchemaOrg.get_schema_product(html)
        custom = ProductsFwrd.get_custom(soup)

        # FIXME: this is stupid...
        # FIXME: actually, this is broken for fwrd.com; they list multiple product variations on a page...
        sp = sp[0] if sp else {}

        signals = {
            'meta': meta,
            'og':   og,
            'sp':   SchemaOrg.to_json(sp),
            'custom': custom,
        }
        #pprint(signals)

        products = []

        prodid = (custom.get('prodid')
                    or nth(sp.get('sku'), 0) or None)

        # is there one or more product on the page?
        if prodid:

            offerprop = {}
            try:
                offerprop = nth(sp.get('offers'), 0)['properties']
            except:
                pass

            p = ProductFwrd(
                prodid=prodid,
                canonical_url=(custom.get('url_canonical')
                        or og.get('url') or url),
                stocklevel=custom.get('stock_level'),
                instock=(custom.get('in_stock')
                        or nth(offerprop.get('availability'), 0) == 'In Stock'
                        or og.get('availability') in ('instock',)),
                price=(custom.get('price')
                        or nth(offerprop.get('price'), 0)
                        or og.get('price:amount') or None),
                sale_price=(custom.get('sale_price')
                        or nth(offerprop.get('price'), 0) or None),
                currency=(nth(offerprop.get('priceCurrency'), 0)
                        or None),
                brand=(nth(sp.get(u'brand'), 0)
                        or og.get('brand')
                        or custom.get('brand') or None),
                category=custom.get('category'),
                bread_crumb=custom.get('bread_crumb') or None,
                name=(nth(sp.get('name'), 0)
                        or custom.get('name')
                        or og.get('title')
                        or meta.get('title') or None),
                title=(og.get('title')
                        or meta.get('title') or None),
                descr=(maybe_join(' ', sp.get('description'))
                        or custom.get('descr')
                        or og.get('description')
                        or meta.get('description') or None),
                features=custom.get('features') or None,
                size=custom.get('size') or None,
                sizes=custom.get('sizes') or None,
                color=custom.get('color') or None,
                colors=custom.get('colors') or None,
                img_url=custom.get('img_url') or og.get('image') or None,
                img_urls=custom.get('img_urls') or None
            )
            products.append(p)

        realproducts = [p.to_product() for p in products]

        page = ProductMapResultPage(
                 merchant_slug='fwrd',
                 url=url,
                 size=len(html),
                 proctime = time.time() - starttime,
                 signals=signals)

        return ProductMapResult(page=page,
                                products=realproducts)


    @staticmethod
    def get_custom(soup):

        # url
        url_canonical = None
        tag = soup.find('link', rel='canonical', href=True)
        if tag:
            url_canonical = tag.get('href')
        if not url_canonical:
            tag = soup.find('meta', itemprop='url', content=True)
            if tag:
                url_canonical = tag.get('content')

        brand = None
        name = None
        price = None
        sale_price = None
        descr = None
        features = None
        bread_crumb = None
        category = None
        prodid = None
        in_stock = None
        stock_level = None
        size = None
        sizes = None
        color = None
        colors = None
        img_url = None
        img_urls = None

        '''
        <span id="find-your-size" class="size_fit" style="display: "
                data-is-visible="true"><a href="#"
                id="cant-find-size-link"
                data-code="RODA-UO3"
                data-sectionurl="Direct Hit"
                data-sessionid="null"
                data-dept="Womens"
                data-show-special-order="false"
                data-show-back-in-stock="true"
                >Can't Find Your Size</a></span>
        '''
        tag = soup.find(attrs={'data-code': True})
        #print 'prodid:', tag
        if tag:
            prodid = tag.get('data-code')

        '''
    <div class="product_info">
        <h1 class="designer_brand">
            <a href="/brand-rodarte/7b4e84/?pdpsrc=brandname">
                Rodarte
            </a>
        </h1>
        <h2 class="product_name">Radarte Poly-Blend Sweatshirt</h2>
        <div class="price_box sale">
            <span class="price">$154</span>
            <span class="discount_price">$77</span>
        </div>
        <!-- regular price style -->
        <!-- <p class="product_price">$685</p> -->
        <div class="color_dd">
            <label>Color</label>
            <select id="color-select">
                <option value="Heather Grey" data-dp-url= "/product-radarte-polyblend-sweatshirt/RODA-UO3/?d=Womens&pdpsrc=selectcolor">Heather Grey</option>

                <option value="Black Heather" data-dp-url= "/product-radarte-polyblend-sweatshirt/RODA-UO5/?d=Womens&pdpsrc=selectcolor">Black Heather</option>

                <option value="Red" data-dp-url= "/product-radarte-polyblend-sweatshirt/RODA-UO2/?d=Womens&pdpsrc=selectcolor">Red</option>

        </select>

    </div><!-- color_dd -->
        '''

        prod_info = soup.find('div', {'class': 'product_info'})
        #print 'prod_info:', prod_info
        if prod_info:
            tag = prod_info.find('h1', {'class': 'designer_brand'})
            #print 'tag:', tag
            if tag:
                brand = normstring(tag.text)

            tag = prod_info.find('h2', {'class': 'product_name'})
            #print 'tag:', tag
            if tag:
                name = normstring(tag.text)

            tag = prod_info.find('span', {'class': 'price'})
            if tag:
                price = normstring(tag.get_text())
            tag = prod_info.find('span', {'class': 'discount_price'})
            if tag:
                sale_price = normstring(tag.get_text())

            tag = prod_info.find('select', id='color-select')
            if tag:
                colors = [normstring(opt.get('value'))
                            for opt in tag.findAll('option', value=True)
                                if opt.get('value')]

            '''
        <div id="details" class="product_detail" style="display:none">
            <ul>
                <li>50% poly 38% cotton 12% rayon</li>
                <li>Made in Dominican Republic</li>
                <li>Our Style No. RODA-UO3</li>
                <li>Manufacturer Style No. F657</li>
            </ul>
            '''
            tag = prod_info.find('div', {'class': 'product_detail'})
            if tag:
                features = [normstring(li.get_text()) for li in tag.findAll('li') if li]

        '''
            <label>Size</label>
            <select id="size-select">
                <option value="">Select Size</option>

                <option value="35"
                                data-is-preorder="false"
                                data-is-one-left="false"
                                data-is-oos="true"
                        data-is-on-sale="false"
                                data-preorder-date="null">
                                35

                                 (Sold Out)

                </option>

                <option value="35.5"
                                data-is-preorder="true"
                                data-is-one-left="false"
                                data-is-oos="false"
                        data-is-on-sale="false"
                                data-preorder-date="Apr 09">
                                35.5

                </option>
        '''
        try:
            tag = soup.find('select', id='size-select')
            if tag:
                tags = tag.findAll('option', value=lambda v: bool(v))
                if tags:
                    sizes = [t.get('value') for t in tags if t.get('value')]
                    oos = [xboolstr(t.get('data-is-oos')) for t in tags]
                    if in_stock is None:
                        # use data-is-oos as indicator...
                        if False in oos: # definitive value...
                            in_stock = True
                    if in_stock is not False:
                        # infer approximate stock level...
                        def approx_quantity(tag):
                            if xboolstr(tag.get('data-is-oos')) is True:
                                return 0
                            if xboolstr(tag.get('data-is-preorder')) is True:
                                return 0
                            if xboolstr(tag.get('data-is-one-left')) is True:
                                return 1
                            return 2 # logical inference...
                        quantity = [approx_quantity(t) for t in tags
                                        if t.get('value')]
                        #print 'quantity:', quantity
                        if quantity:
                            stock_level = sum(quantity)

        except Exception as e:
            traceback.print_exc()
            pass

        '''
        <div class="cycle-slideshow cycle-paused" style="position: relative; overflow: hidden;"
                data-cycle-fx="scrollHorz"
                data-cycle-swipe="true"
                data-cycle-slides=".product-detail-image-zoom"
                data-cycle-timeout="0"
                data-cycle-carousel-fluid="true"
                data-cycle-carousel-visible="1"
                data-cycle-speed="200"
                data-cycle-prev="#prev"
                data-cycle-next="#next"
                data-cycle-pager=".cycle-pager"
                data-cycle-log="false">

            <div class="product-detail-image-zoom">
                <img alt="Image 1 of Rodarte Radarte Poly-Blend Sweatshirt in Heather Grey" src="https://is4.revolveassets.com/images/p/fw/z/RODA-UO3W_V1.jpg" data-zoom-image="https://is4.revolveassets.com/images/p/fw/z/RODA-UO3W_V1.jpg" class="product-detail-image" />
            </div>

            <div class="product-detail-image-zoom">
                <img alt="Image 2 of Rodarte Radarte Poly-Blend Sweatshirt in Heather Grey" src="https://is4.revolveassets.com/images/p/fw/z/RODA-UO3W_V2.jpg" data-zoom-image="https://is4.revolveassets.com/images/p/fw/z/RODA-UO3W_V2.jpg" class="product-detail-image" />
            </div>
            ...
        </div>
        '''
        tag = soup.find('div', attrs={'class': 'cycle-slideshow'})
        if tag:
            img_urls = [img.get('src')
                            for img in tag.findAll('img', src=True)
                                if img.get('src')] or None
            if img_urls:
                img_url = img_urls[0]

        '''
        <div itemscope itemtype="http://data-vocabulary.org/Breadcrumb"><a href="/"><span itemprop="title">Women</span></a></div> / <div itemprop="child" itemscope="" itemtype="http://data-vocabulary.org/Breadcrumb"><span itemprop="title">Radarte Poly-Blend Sweatshirt</span></div>
        '''
        # NOTE: they fucked this up; one breadcrumb item per?
        tags = soup.findAll(attrs={'itemtype': 'http://data-vocabulary.org/Breadcrumb'})
        if tags:
            bread_crumb = [normstring(t.get_text()) for t in tags] or None

        data = {
            'url_canonical': url_canonical,
            'prodid': prodid,
            'bread_crumb': bread_crumb,
            'category': category or None,
            'brand': brand or None,
            'price': price or None,
            'sale_price': sale_price or None,
            'stock_level': stock_level,
            'in_stock': in_stock,
            'name': name,
            'title': None,
            'descr': descr,
            'features': features,
            'size': size,
            'sizes': sizes,
            'color': color,
            'colors': colors,
            'img_url': img_url,
            'img_urls': img_urls,
        }
        return data


if __name__ == '__main__':

    import gzip

    # test no-op
    filepath = 'test/www.dermstore.com-product_Lipstick_31136.htm.gz'

    url = 'http://www.fwrd.com/product-aquazzura-wild-thing-suede-heels-in-lipstick/AAZZ-WZ85/?d=Womens&srcType=plpaltimage&list=plp-list-2'
    filepath = 'test/www.fwrd.com-product-aquazzura-wild-thing-suede-heels-in-lipstick-AAZZ-WZ85-d-Womens.gz'
    url = 'http://www.fwrd.com/product-rodarte-radarte-polyblend-sweatshirt-in-heather-grey/RODA-UO3/?d=Womens&srcType=plpaltimage&list=plp-list-3'
    filepath = 'test/www.fwrd.com-product-rodarte-radarte-polyblend-sweatshirt-in-heather-grey-RODA-UO3-d-Womens.gz'

    with gzip.open(filepath) as f:
        html = f.read()

    products = ProductsFwrd.from_html(url, html)
    print products
