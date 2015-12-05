# ex: set ts=4 et:

'''
a productsum wrapper around opengraph
'''

import opengraph
from collections import defaultdict

class OG(object):

    # TODO: refactor out
    @staticmethod
    def get_og(html):
        ogp = opengraph.OpenGraph(html=html)
        d = dict(ogp)
        return d
