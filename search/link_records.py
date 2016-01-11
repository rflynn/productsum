# vim: set ts=4 et:
# -*- coding: utf-8 -*-

'''
How to group products

1. Extract obvious attributes from name to fields, normalize name
    size
    color
    other variants
2. tokenize
3. sort
4. group based on prefix matches?

unclear:
* how to accomodate colors/variants?
* prices as hints
* stuff that doesn't sort right/different orders
'''


from collections import defaultdict, Counter
from pprint import pprint
import networkx as nx
import re
import unicodecsv as csv
import unicodedata

from tag_name import tokenize_words


def parse_psql_array(s):
    def dequote(s):
        if s.startswith('"') and s.endswith('"'):
            s = s[1:-1]
        return s.replace('""', '"')
    if not s: return None
    if s == u'{}': return []
    return [dequote(s) for s in
                re.findall(r'("(?:""|[^"]+)*"|[^,]+)',
                    s[1:-1], re.UNICODE)]
assert parse_psql_array(u'{}') == []
assert parse_psql_array(u'{"",a,"b c","d""e",""""}') == [u'', u'a', u'b c', u'd"e', u'"']

def list_prefix_overlap(l1, l2):
    i = 0
    llen = min(len(l1), len(l2))
    while i < llen:
        if l1[i] != l2[i]:
            break
        i += 1
    return i
assert list_prefix_overlap([], []) == 0
assert list_prefix_overlap([1], []) == 0
assert list_prefix_overlap([], [1]) == 0
assert list_prefix_overlap([2], [1]) == 0
assert list_prefix_overlap([1], [1]) == 1
assert list_prefix_overlap([1,2], [1]) == 1
assert list_prefix_overlap([1,2], [1,3]) == 1
assert list_prefix_overlap([1,2], [1,2]) == 2

records = {}

class ProductRecord(object):
    def __init__(self, brand=None, name=None,
                       color=None, colors=None,
                       size=None, sizes=None):
        assert name is not None
        self.brand = brand
        self.name = name
        self.name_tokens = tokenize_words(name)
        self.color = color
        self.colors = colors
        self.size = size
        self.sizes = sizes

    def __repr__(self):
        return ('ProductRecord(%s)' % (self.name,)).encode('utf8')

    def closest_prefixes(self, records):
        if self.name_tokens:
            closest = defaultdict(list)
            for r in records:
                if r.name != self.name and r.name_tokens:
                    closest[list_prefix_overlap(self.name_tokens, r.name_tokens)].append(r)
            if closest:
                bestscore = max(closest.keys())
                return int(bestscore), closest[bestscore]
        return 0, []

    def get_ascii_name(self):
        return unicodedata.normalize('NFKD', self.name).encode('ascii', 'ignore')

if __name__ == '__main__':

    with open('name-narscosmetics-variants.csv', 'rb') as f:
        rd = csv.reader(f)
        for row in rd:
            #print row
            name, color, size, colors, sizes = row
            c = parse_psql_array(colors)
            #print ('%s, %s, %s' % (name, size, '')).encode('utf8')
            #print tokenize_words(name)
            records[name] = ProductRecord(brand='NARS', name=name, colors=c)

    #pprint(records)
    #pprint(records[u'All Day Luminous Powder Foundation Broad Spectrum SPF 24 - Siberia'].closest_prefixes(records.values()))
    #pprint(records[u'All Day Luminous Powder Foundation'].closest_prefixes(records.values()))

    G = nx.Graph()
    prefixes = Counter()
    for k, r in records.iteritems():
        score, closest = r.closest_prefixes(records.values())
        if score and closest:
            prefixes[tuple(r.name_tokens[:score])] += 1
        if score > 1:
            for cl in closest:
                G.add_edge(r.get_ascii_name(), cl.get_ascii_name(), weight=score)

    for i, (k, cnt) in enumerate(sorted(prefixes.iteritems(), key=lambda x: x[1], reverse=True)):
        print ('%3d %3d %s' % (i, cnt, k)).encode('utf8')

    # graph via graphviz
    print 'nars.dot...'
    nx.write_dot(G, 'nars.dot')
    cmd = 'fdp -Tpng -Goutputorder=edgesfirst -o nars.png nars.dot 2>&1'
    print cmd
    import os
    os.system(cmd)

