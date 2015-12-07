# ex: set ts=4 et:

'''
a productsum wrapper around opengraph
'''

from collections import defaultdict
import re


class OG(object):

    @staticmethod
    def get_og(soup):
        og = {m['property'][3:]: m['content'].encode('utf8')
                for m in soup.findAll('meta', content=True,
                                    property=re.compile('^og:'))}
        return og
