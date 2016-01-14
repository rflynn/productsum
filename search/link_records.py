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

NOTE: a number of the "sizes" in narscosmetics are actually colors/variants


TODO:

"tearjerker eye set"
    3+ matches for this...
"#41 diffusing brush" == "diffusing brush #41"


\copy (select up.name, up.color, up.size, up.available_colors, up.available_sizes from url_product up join brand_translate bt on bt.brand_from = up.brand where bt.brand_to = 'NARS' order by up.name) to '/tmp/name-narscosmetics-variants.csv' csv;

\copy (select up.name, up.color, up.size, up.available_colors, up.available_sizes from url_product up join brand_translate bt on bt.brand_from = up.brand where bt.brand_to = 'M·A·C' order by up.name) to '/tmp/name-mac-variants.csv' csv;

'''


from collections import defaultdict, Counter
import itertools
from pprint import pprint, pformat
import networkx as nx
import re
import unicodecsv as csv
import unicodedata

import Levenshtein

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

def is_suffix(l1, l2):
    return l1[-len(l2):] == l2

def is_subseq(l1, l2):
    # python makes simple list operations very difficult to be performant
    l1 = list(l1)
    l2 = list(l2)
    return any(l1[i:i+len(l2)] == l2 for i in xrange(len(l1)))

def to_ascii(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')

def levenshtein(a, b):
    return Levenshtein.distance(a, b)


class ProductMatcher(object):

    def __init__(self, name, name_tokens, variants_tokens):
        self.name = name
        self.name_tokens = name_tokens
        self.variants_tokens = set(map(tuple, variants_tokens))

    def __repr__(self):
        return ('ProductMatcher(%s, %s)' % (
            u' '.join(self.name_tokens),
            '(%s)' % (','.join(' '.join(vt) for vt in sorted(self.variants_tokens))))).encode('utf8')

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other):
        return (self.name_tokens == other.name_tokens
                and self.variants_tokens == other.variants_tokens)

    def is_superset(self, other):
        return (self.name_tokens == other.name_tokens
                and self.variants_tokens > other.variants_tokens)

    def overlap(self, pr):
        assert isinstance(pr, ProductRecord)
        # calculate how much overlap there is
        maxtoks = len(pr.name_tokens) + len(pr.color_tokens or [])
        overlap = 0
        if is_subseq(pr.name_tokens, self.name_tokens):
            overlap += len(self.name_tokens)
            if pr.color_tokens:
                if tuple(pr.color_tokens) in self.variants_tokens:
                    overlap += len(pr.color_tokens)
            overlap += max([len(vt) for vt in self.variants_tokens
                                if is_subseq(pr.name_tokens, vt)] or [0])
        return float(overlap) / maxtoks

    @classmethod
    def definitive_set(cls, matchers):
        # given a set of matchers, condense based on equality/subset/superset logic into a minimal set
        ret = sorted(set(matchers), cmp=lambda x,y: x.is_superset(y))
        ret1 = set()
        for x in ret:
            if not any(r.is_superset(x) for r in ret):
                ret1.add(x)
        return ret1

pm1 = ProductMatcher('name', ['name'], ['x'])
pm2 = ProductMatcher('name', ['name'], ['x', 'y']) # superset of pm1
assert pm2.is_superset(pm1) is True
assert ProductMatcher.definitive_set([pm2, pm1]) == set([pm2])


class ProductRecord(object):
    def __init__(self, brand=None, name=None,
                       color=None, colors=None,
                       size=None, sizes=None):
        assert name is not None
        self.brand = brand
        self.name = name
        self.name_tokens = tokenize_words(name)
        self.color = color
        if self.color:
            self.color_tokens = tokenize_words(self.color)
        else:
            self.color_tokens = None
        self.colors = colors
        if self.colors:
            self.colors_tokens = sorted(tokenize_words(c) for c in self.colors)
        else:
            self.colors_tokens = None
        self.size = size
        self.sizes = sizes

        self.matcher = None
        self.calc_matcher()

    def __repr__(self):
        return ('ProductRecord(%s)' % (self.name,)).encode('utf8')

    def get_ascii_name(self):
        return unicodedata.normalize('NFKD', self.name).encode('ascii', 'ignore')

    def calc_matcher(self):
        if self.name_tokens:
            #if self.color_tokens and self.colors_tokens:
            #    self.matcher = ProductMatcher(self.name, self.name_tokens, self.colors_tokens)
            if self.color_tokens and not self.colors_tokens:
                self.matcher = ProductMatcher(self.name, self.name_tokens, self.color_tokens)
            elif self.colors_tokens:
                for ct in self.colors_tokens:
                    if is_suffix(self.name_tokens, ct): # FIXME: use max suffix... and then forget suffix...
                        self.matcher = ProductMatcher(self.name, self.name_tokens[:-len(ct)], self.colors_tokens)
                        return
                #print 'no matcher for ', self.name_tokens, ':::', self.colors_tokens
                self.matcher = ProductMatcher(self.name, self.name_tokens, self.colors_tokens)
                

def an_actual_size(s):
    return s and s.lower() not in {'', 'one size', 'onesize', 'no size', 'nosize'}

def actual_sizes(a):
    return [x for x in a if an_actual_size(x)] if a else None

# networkx.write_dot doesn't actually work
def actually_write_dot(G, filepath):
    #print G.__class__
    #print type(G)
    with open(filepath, 'wb') as f:
        f.write('''
graph {
node[color=black,penwidth=0.25,fontname=arial,fontsize=9];
edge[len=1];
''')
        for e in G.edges_iter():
            u, v = e
            attrs = G.get_edge_data(u, v)
            writeattrs = (','.join('%s=%s' % (k, ('%.1f' % v) if isinstance(v, (int, float)) else '"%s"' % v)
                            for k, v in attrs.iteritems()))
            if u == v:
                f.write(('"%s" [%s]\n' % (u, writeattrs)).encode('utf8'))
            else:
                f.write(('"%s" -- "%s" [%s]\n' % (u, v, writeattrs)).encode('utf8'))
        f.write('}\n')

if __name__ == '__main__':

    import sys

    brand = 'narscosmetics'
    #brand = 'mac'

    if sys.argv and len(sys.argv) > 1:
        brand = sys.argv[1]

    print 'brand:', brand

    records = {}
    matchers = {}

    with open('name-%s-variants.csv' % brand, 'rb') as f:
        rd = csv.reader(f)
        for row in rd:
            #print row
            name, color, size, colors, sizes_str = row
            c = parse_psql_array(colors)
            sizes = actual_sizes(parse_psql_array(sizes_str))
            #if sizes:
            #    print ('%s, %s, %s' % (name, sizes, c)).encode('utf8')
            #print tokenize_words(name)
            r = ProductRecord(brand=brand, name=name, colors=c)
            m = r.matcher
            if m:
                matchers[m] = m
            records[name] = r

    #print 'records:', len(records)
    #print 'matchers:', len(matchers)

    matchers2 = defaultdict(list)
    for _, m in matchers.iteritems():
        matchers2[tuple(m.name_tokens)].append(m)

    #pprint(dict(matchers2))
    # condense multiple matches under the same name
    for k, v in matchers2.iteritems():
        matchers2[k] = ProductMatcher.definitive_set(v)

    # display results
    for k, v in matchers2.iteritems():
        print 'matchers2:', k, len(v)
        #if len(v) > 1:
        #    print pformat(v, indent=4, width=50)


    def do_match(r, matchers):
        m = {}
        for k, v in matchers.iteritems():
            for v2 in v:
                o = v2.overlap(r)
                if o > 0:
                    m[v2] = o
        return m


    #sys.exit(0)

    G = nx.DiGraph()

    unmatched = []

    for name, r in records.iteritems():
        #print r, 'matches', 
        matches = do_match(r, matchers2)
        if matches:
            for m, pct in matches.iteritems():
                G.add_edge(r.get_ascii_name(),
                           to_ascii(unicode(str(m), 'utf8'))[:128],
                           weight=pct,
                           penwidth=str(round(pct * 5, 1)),
                           color='blue')
        else:
            print 'no matches:', r
            unmatched.append(r)

    unmatched2 = set()

    # various desperate features to try and find some overlap where it clearly exists...
    for x in unmatched:
        #d, y = min((levenshtein(x.name, u.name), u) for u in unmatched if u != x)
        #if float(d) / min(len(x.name), len(y.name)) <= 0.5:
        matched = False
        for y in unmatched:
            if x != y:
                xnt = set(x.name_tokens)
                ynt = set(y.name_tokens)
                if set(x.name_tokens) == set(y.name_tokens):
                    # exact token match, order-independent
                    matched = True
                    d = min(len(x.name), len(y.name))
                    print 'exact match, order-independent', d, x, y
                    G.add_edge(x.get_ascii_name(),
                               y.get_ascii_name(),
                               penwidth=str(float(d) / len(x.name) * 2),
                               color='green')
                elif len(y.name_tokens) > 1 and set(x.name_tokens) > set(y.name_tokens):
                    matched = True
                    d = min(len(x.name), len(y.name))
                    print 'token superset', d, x, y
                    G.add_edge(x.get_ascii_name(),
                               y.get_ascii_name(),
                               penwidth=str(float(d) / len(x.name) * 2),
                               color='purple')
                elif min(len(xnt), len(ynt)) >= 2 and float(len(xnt & ynt)) / max(len(xnt), len(ynt)) >= 0.66:
                    matched = True
                    d = float(len(xnt & ynt)) / max(len(xnt), len(ynt))
                    print 'set overlap', d, x, y
                    G.add_edge(x.get_ascii_name(),
                               y.get_ascii_name(),
                               penwidth=str(float(d) / max(len(xnt), len(ynt)) * 3),
                               color='orange')
        if not matched:
            unmatched2.add(x)

    for u in unmatched2:
        G.add_edge(u.get_ascii_name(),
                   u.get_ascii_name(),
                   penwidth=1,
                   color='gray')


    # graph via graphviz
    print '%s.dot...' % brand
    #nx.write_dot(G, '%s.dot' % brand)
    actually_write_dot(G, brand + '.dot')

    #sys.exit(1)

    cmd = 'fdp -Tpng -Goutputorder=edgesfirst -o %s.png %s.dot 2>&1' % (brand, brand)
    cmd = 'neato -Tpng -Glabel="%s" -Glabelloc=t -Glabelfontsize=32 -Goutputorder=edgesfirst -o %s.png %s.dot 2>&1' % (brand, brand, brand)
    cmd = 'sfdp -Tpng -Glabel="%s" -Glabelloc=t -Glabelfontsize=32 -Goverlap=prism -Goutputorder=edgesfirst -o %s.png %s.dot 2>&1' % (brand, brand, brand)
    cmd = 'fdp -Tpng -Glabel="%s" -Glabelloc=t -Glabelfontsize=32 -o %s.png %s.dot 2>&1' % (brand, brand, brand)
    cmd = 'neato -Tpng -Glabel="%s" -Glabelloc=t -Glabelfontsize=32 -o %s.png %s.dot 2>&1' % (brand, brand, brand)
    cmd = 'sfdp -Tpng -Glabel="%s" -Glabelloc=t -Glabelfontsize=32 -o %s.png %s.dot 2>&1' % (brand, brand, brand)
    print cmd
    import os
    os.system(cmd)

