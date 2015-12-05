# ex: set ts=4 et:

from BeautifulSoup import BeautifulSoup
import execjs # json not good enough here...
import gzip
import json
from pprint import pprint
import re

from htmlmetadata import HTMLMetadata
from og import OG
from schemaorg import SchemaOrg
from tealium import Tealium
from util import nth, xstrip


if __name__ == '__main__':
    import sys
    testfile = 'www.luisviaroma.com-index-SeasonId-63I-CollectionId-D0Z-ItemId-6-VendorColorId-U1BJQ0U1.gz'
    filepath = sys.argv[1] if len(sys.argv) > 1 else testfile
    products = []
    with gzip.open(filepath) as f:
        html = f.read()

    sp = SchemaOrg.get_schema_product(html)
    og = OG.get_og(html)
    soup = BeautifulSoup(html)
    meta = HTMLMetadata.do_html_metadata(soup)
    utag = Tealium.get_utag_data(soup)

    pprint(sp)
    pprint(og)
    pprint(meta)
    pprint(utag)

    raise NotImplementedError()

    #products = ProductsBluefly.from_html('http://bluefly.example/', html)
    #pprint(products)

