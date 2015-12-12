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


# ref: http://help.wanelo.com/customer/portal/articles/1527843-how-can-i-use-meta-tags-to-keep-store-product-info-accurate-
def get_meta_wanelo(soup):
    '''
<!-- wanelo product tag start-->
<meta property="wanelo:product:name" content="Stuart Weitzman Nudist Heel in Black Patent" />
<meta property="wanelo:product:price" content="398.00">
<meta property="wanelo:product:price:currency" content="USD" />
<meta property="wanelo:product:availability" content="InStock" />
<meta property="wanelo:product:url" content="http://www.revolveclothing.com/stuart-weitzman-nudist-heel-in-black-patent/dp/STUA-WZ111/?d=Womens" />
<!-- wanelo product tag end -->
    '''
    wa = {m['property'][7:]: m['content'].encode('utf8')
            for m in soup.findAll('meta', content=True,
                                property=re.compile('^wanelo:'))}
    return wa

class ProductRevolveClothing(object):
    VERSION = 0
    def __init__(self, prodid=None, canonical_url=None,
                 stocklevel=None, instock=None,
                 price=None, sale_price=None, currency=None,
                 brand=None, category=None, bread_crumb=None,
                 name=None, title=None, descr=None,
                 features=None, size=None, sizes=None,
                 color=None, colors=None,
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
        assert color is None or isinstance(color, basestring)
        assert colors is None or isinstance(colors, list)
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
        self.color = color
        self.colors = colors
        self.img_url = img_url

        # fixups
        if self.price:
            self.price = re.sub('\s+', '', self.price)

    def __repr__(self):
        return '''ProductRevolveClothing(
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
)''' % (self.prodid, self.canonical_url,
       self.instock, self.stocklevel,
       self.price, self.sale_price, self.currency,
       self.brand, self.category, self.bread_crumb, 
       self.name, self.title, self.descr,
       self.features, self.size, self.sizes,
       self.color, self.colors,
       self.img_url)

    def to_product(self):

        return Product(
            merchant_slug='revolveclothing',
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
            img_urls=[self.img_url] if self.img_url else None
        )


class ProductsRevolveClothing(object):

    VERSION = 0

    @classmethod
    def from_html(cls, url, html):

        starttime = time.time()

        soup = BeautifulSoup(html)
        meta = HTMLMetadata.do_html_metadata(soup)
        og = OG.get_og(soup)
        sp = SchemaOrg.get_schema_product(html)
        wa = get_meta_wanelo(soup)
        custom = cls.get_custom(soup, og)

        sp = sp[0] if sp else {}

        signals = {
            'meta': meta,
            'og':   og,
            'sp':   SchemaOrg.to_json(sp),
            'wa':   wa,
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

            p = ProductRevolveClothing(
                prodid=prodid,
                canonical_url=(custom.get('url_canonical')
                        or wa.get('product:url')
                        or og.get('url') or url),
                stocklevel=custom.get('stock_level'),
                instock=(custom.get('in_stock')
                        or wa.get('product:availability') == 'InStock'
                        or og.get('availability') in ('instock',)),
                price=(nth(offerprop.get('price'), 0)
                        or wa.get('product:price')
                        or custom.get('price')
                        or og.get('price:amount') or None),
                sale_price=custom.get('sale_price') or None,
                currency=(nth(offerprop.get('priceCurrency'), 0)
                        or wa.get('product:price:currency')
                        or None),
                brand=(nth(sp.get(u'brand'), 0)
                        or og.get('brand')
                        or custom.get('brand') or None),
                category=custom.get('category'),
                bread_crumb=custom.get('bread_crumb') or None,
                name=(nth(sp.get('name'), 0)
                        or wa.get('product:name')
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
                img_url=og.get('image') or None,
            )
            products.append(p)

        realproducts = [p.to_product() for p in products]

        page = ProductMapResultPage(
                 version=cls.VERSION,
                 merchant_slug='revolveclothing',
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
        '''
        <div class="product-details__content js-tabs__content js-tabs__content-active product-details__description">
            <ul class="product-details__list u-margin-l--none">
                <li>Patent leather upper with leather sole<br></li><li>Heel measures approx 4.5" H</li><li>Buckle closure</li><li>This item is not available for international export</li><li>Revolve Style No. STUA-WZ111</li><li>Manufacturer Style No. NUDIST</li>
            </ul>
        </div>
        '''
        tag = soup.find('ul', {'class': 'product-details__list'})
        if tag:
            features = [normstring(t.text)
                            for t in tag.findAll('li')]

        bread_crumb = None
        # TODO:
        '''
<div itemscope itemtype="http://data-vocabulary.org/Breadcrumb"><a href="/"><span itemprop="title">Women</span></a></div> / <div itemprop="child" itemscope="" itemtype="http://data-vocabulary.org/Breadcrumb"><span itemprop="title">Nudist Heel</span></div>
        '''

        brand = None
        category = None
        prodid = None
        in_stock = None
        stock_level = None

        '''
          <h2 class="product-titles__brand u-margin-a--none" property="brand">
              <a href='/stuart-weitzman/br/a9b29d/?srcType=dp_des2'>
                  Stuart Weitzman
              </a>
          </h2>
        '''
        tag = soup.find('h2', property='brand')
        if tag and hasattr(tag, 'text'):
            brand = normstring(tag.text)

        '''
        <input type="hidden" id="productCode" name="productCode" value="STUA-WZ111">
        '''
        tag = soup.find('input', type='hidden', id='productCode', value=True)
        if tag:
            prodid = normstring(tag['value'])
        
        '''
pushAddProductToGA('Stuart Weitzman Nudist Heel in Black Patent', 'STUA-WZ111', '398.00', 'Stuart Weitzman', 'Heels', 'Black Patent', 'USD', '1');
        '''

        '''
        <a href="javascript:void(0)"
            class="cantfindsize"
            id="find-size"
            data-show-popup="full"
            data-is-all-preorder="false"
            data-all-size="6,6.5,7,7.5,8,8.5,9,9.5,10"
            data-oos-size="6,6.5,7,7.5,8,8.5,9,10"
            data-code="STUA-WZ111"
            data-sectionurl="Direct Hit"
            data-sessionid="null"
            >
        '''
        size = None
        sizes = None
        try:
            tag = soup.find('a', id='find-size')
            if tag:
                all_sizes = tag.get('data-all-size')
                if all_sizes:
                    sizes = all_sizes.split(',') or None

                oos_sizes = tag.get('data-oos-size')
                if oos_sizes is not None:
                    oos_sizes = xstrip(oos_sizes)
                    if oos_sizes == '':
                        oos = []
                    else:
                        oos = oos_sizes.split(',')
                    in_stock = all_sizes != oos
                if not prodid:
                    code = tag.get('data-code')
                    if code:
                        prodid = xstrip(code)
        except Exception as e:
            traceback.print_exc()
            pass

        color = None
        colors = None
        def get_color(s):
            m = re.search("changeColorText\('([^']+)'\)", s)
            if m:
                return m.groups(0)[0]
        tags = soup.findAll('div', id=re.compile('^outercolor[0-9]+$'))
        colors = sorted(set(
                    [c for c in
                        flatten([[get_color(t.get('onmouseover')),
                                  get_color(t.get('onmouseout'))]
                            for t in tags]) if c])) or None
        # current color is color switch tag that doesn't do anything, because it's already set!
        setcolor = [t for t in tags if not t.get('onmouseover')]
        color = get_color(setcolor[0].get('onmouseout')) or None if setcolor else None

        data = {
            'url_canonical': url_canonical,
            'prodid': prodid,
            'bread_crumb': bread_crumb,
            'category': category or None,
            'brand': brand,
            'price': price or None,
            'sale_price': None,
            'img_url': None,
            'stock_level': stock_level or None,
            'in_stock': in_stock,
            'name': name,
            'title': None,
            'descr': descr,
            'features': features,
            'size': size,
            'sizes': sizes,
            'color': color,
            'colors': colors,
        }
        return data


if __name__ == '__main__':

    import gzip

    url = 'http://www.revolveclothing.com/stuart-weitzman-nudist-heel-in-black-patent/dp/STUA-WZ111/?d=Womens'
    # test no-op
    #filepath = 'test/www.dermstore.com-product_Lipstick_31136.htm.gz'

    filepath = 'test/www.revolveclothing.com-stuart-weitzman-nudist-heel-in-black-patent-dp-STUA-WZ111.gz'

    with gzip.open(filepath) as f:
        html = f.read()

    products = ProductsRevolveClothing.from_html(url, html)
    print products
