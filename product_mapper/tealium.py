# ex: set ts=4 et:

import json
from pprint import pprint
import re
import traceback

'''
ref: http://tealium.com/blog/standard/what-is-universal-tag-part-4/
ref: http://tealium.com/blog/standard/best-practices-implementing-data-layer/
'''

class Tealium(object):

    @staticmethod
    def get_utag_data(soup):
        utag_text = [s.text for s in soup.findAll('script')
                        if 'utag_data' in s.text]
        j = {}
        if utag_text:
            m = re.search('utag_data\s*=\s*({[^;]*})', utag_text[0], re.DOTALL)
            if m:
                try:
                    objstr = m.groups(0)[0]
                    j = json.loads(objstr)
                except Exception as e:
                    print 'tealium', e

        return j


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
