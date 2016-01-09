# vim: set ts=4 et:
# -*- coding: utf-8 -*-

# Run me: cat name-narscosmetics.csv | python cluster_brand_products.py 2>&1

'''
given a set of $url_product.name strings that belong to a given $brand...
    figure out which ones are the same products
    cluster them together by similarity
'''

# ref: https://en.wikipedia.org/wiki/Longest_common_subsequence_problem
# ref: https://en.wikipedia.org/wiki/N-gram

from collections import defaultdict
import itertools
import math
import networkx as nx
from pprint import pprint
import re

import tag_name


def nngram(ngram, n):
    '''
    given a list of tokens, return list of set of token sequences of length n
    '''
    if len(ngram) < n:
        return None
    return [ngram[i:i+n] for i in xrange(len(ngram) - n + 1)]

assert nngram([1], 2) is None
assert nngram([1], 1) == [[1]]
assert nngram([1,2,3], 1) == [[1],[2],[3]]
assert nngram([1,2,3], 2) == [[1,2],[2,3]]

def ngram_count(strings, n=2):
    ngrams = [nngram(tag_name.tokenize(s), n) for s in strings]
    nng = tag_name.flatten(ng for ng in ngrams if ng)
    cnt = Counter(map(tuple, nng))
    return cnt


def ngram_legit(ng):
    # should we count this ngram?
    # legit if:
    #   only 1 long
    #   > 1 long, and begins and ends with non-punctuation
    return (len(ng) == 1 or
        (re.search(r'^\w', ng[0]) and re.search(r'^\w', ng[-1])))

def flatten(l):
    return [item for sublist in l for item in sublist]


if __name__ == '__main__':

    import sys

    records = {i+1: unicode(line, 'utf8').strip()
                for i, line in enumerate(sys.stdin)}
    #pprint(records)

    # de-dupe record values
    nameset = {k: i for i, k in enumerate(set(records.values()))}

    # tokenize each name
    # FIXME: strips all non-ascii strings...
    tokset = {s: tag_name.tokenize(s) for s in nameset.keys()
        if all(ord(c) < 128 for c in s) }
    #pprint(toks)

    G = nx.Graph()
    edges = defaultdict(int)

    # calculate overlap of ngrams per string entry
    for n in range(10, 2, -1):
        print n
        o = defaultdict(list)
        for s, toks in tokset.iteritems():
            for nn in nngram(toks, n) or []:
                if ngram_legit(nn):
                    o[tuple(nn)].append(s)
        # filter entries with no overlap
        o2 = {k: v for k, v in o.iteritems()
                if len(v) > 1}
        #print 'values:'
        #pprint(o2.values())
        #edges = flatten(itertools.combinations(v, 2) for v in o2.values())
        for _, v in o2.iteritems():
            for x, y in itertools.combinations(v, 2):
                if x > y:
                    x, y = y, x
                edges[(x,y)] += n
        #pprint(edges)
        # sort by most overlap
        #o2sort = sorted(o2.iteritems(), key=lambda x: (len(x[1]), x[0]), reverse=True)
        #pprint(o2sort, width=200)

    #G.add_edges_from(edges)
    G.add_weighted_edges_from(
        (x,y,w) for (x,y),w in edges.iteritems())

    for (x, y), w in edges.iteritems():
        G[x][y]['label'] = w
        G[x][y]['penwidth'] = str(round(math.log(w), 1))

    print 'cluster.dot...'
    nx.write_dot(G, 'cluster.dot')
    import os
    print 'cluster.png...'
    os.system('fdp -Tpng -Goutputorder=edgesfirst -o cluster.png cluster.dot')

    '''
    import matplotlib.pyplot as plt
    nx.draw(G)
    plt.show()
    '''

