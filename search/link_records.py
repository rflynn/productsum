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


TODO:

"tearjerker eye set"
    3+ matches for this...
"#41 diffusing brush" == "diffusing brush #41"

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


records = {}
matchers = {}

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

if __name__ == '__main__':

    import sys

    with open('name-narscosmetics-variants.csv', 'rb') as f:
        rd = csv.reader(f)
        for row in rd:
            #print row
            name, color, size, colors, sizes = row
            c = parse_psql_array(colors)
            #print ('%s, %s, %s' % (name, size, c)).encode('utf8')
            #print tokenize_words(name)
            r = ProductRecord(brand='NARS', name=name, colors=c)
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

    unmatched2 = []

    for x in unmatched:
        d, y = min((levenshtein(x.name, u.name), u) for u in unmatched if u != x)
        if float(d) / min(len(x.name), len(y.name)) <= 0.5:
            print d, x, y
            G.add_edge(x.get_ascii_name(),
                       y.get_ascii_name(),
                       penwidth=str(float(d) / len(x.name) * 2),
                       color='green')
        else:
            unmatched2.append(x)

    for u in unmatched2:
        G.add_edge(u.get_ascii_name(),
                   u.get_ascii_name(),
                   penwidth=1,
                   color='gray')


    '''
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
    '''

    # graph via graphviz
    print 'nars.dot...'
    nx.write_dot(G, 'nars.dot')
    cmd = 'fdp -Tpng -Goutputorder=edgesfirst -o nars.png nars.dot 2>&1'
    cmd = 'neato -Tpng -Goutputorder=edgesfirst -o nars.png nars.dot 2>&1'
    print cmd
    import os
    os.system(cmd)

