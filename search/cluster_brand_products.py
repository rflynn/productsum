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

'''
select up.id, bt.brand_to, up.merchant_slug, up.name, up.category, up.available_colors, up.available_sizes from url_product up join brand_translate bt on bt.brand_from = up.brand where bt.brand_to = 'NARS' order by up.name;

\copy (select up.name, up.color, up.size, up.available_colors, up.available_sizes from url_product up join brand_translate bt on bt.brand_from = up.brand where bt.brand_to = 'NARS' order by up.name) to '/tmp/name-narscosmetics-variants.csv' csv;
'''

'''
 1109255 | NARS     | narscosmetics   | Audacious Lipstick - Geraldine                                               | Makeup                             | {Angela,Anita,Anna,Annabella,Audrey,Barbara,Bette,Brigitte,Carmen,Catherine,Charlotte,Claudia,Deborah,Dominique,Fanny,Geraldine,Grace,Greta,Ingrid,Jane,Janet,Jeanne,Julie,Juliette,Kelly,Lana,Leslie,Liv,Marisa,Marlene,Michiyo,Natalie,Olivia,Raquel,Rita,Sandra,Silvia,Vanessa,Vera,Vivien}

 1109102 | NARS     | narscosmetics   | Blush - Nico                                                                 | Makeup                             | {"413 BLKR",Almerla,Amour,Angelika,"Deep Throat",Desire,"Dolce Vita","Exhibit A",Gaiety,Gilda,Gina,LibertÉ,Lovejoy,Luster,Madly,"Mata Hari",Nico,Oasis,Orgasm,Outlaw,Reckless,Seduction,"Sex Appeal",Sin,"Super Orgasm","Taj Mahal",Taos,Torrid,Tribulation,Unlawful,Zen}

Core Product - underlying, universal item (e.g. "lipstick")
Brand Product - brand's product around core product (e.g. "Audacious Lipstick")
Product Variant - flavor/color variant of Brand Product (e.g. "Audacious Lipstick - Geraldine")

the record we start with may have:
    a specified variant:
    a set of possible variants:

NARS "#40 Eye Shadow Brush"
BrandProduct(NARS, BrandProduct(#40 Eye Shadow, CoreProduct(Brush)))

FooBrand 'A Novel Romance' Fluidline Eye Pencil
BrandProduct(FooBrand, BrandProduct("'A Novel Romance'", 

"All Day Luminous Powder Foundation Broad Spectrum SPF 24 - Siberia"
(((All Day) (Luminous (Powder (Foundation)))) (Broad Spectrum) (SPF 24) - (Siberia))"
   --- ---   --------  ------  ----------      ----- --------   --- --     -------
   -------   --------  ------  ----------      --------------   ------     -------
    ngram      adj      spec     core              ngram         ngram      token
                          +-------+                adj/attr      attr      variant
                +-------------+
      +----------------+
               +--------------------------------------+
                                 +---------------------------------+
'''

from collections import defaultdict, Counter
import itertools
import math
import Levenshtein
import networkx as nx
import numpy as np
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


def ngram_legit(ng):
    # should we count this ngram?
    # legit if:
    #   only 1 long
    #   > 1 long, and begins and ends with non-punctuation
    return (len(ng) == 1 or
        (re.search(r'^\w', ng[0]) and re.search(r'^\w', ng[-1])))

def flatten(l):
    return [item for sublist in l for item in sublist]

def listcontains(l, sublist):
    slen = len(sublist)
    return any(l[i:i+slen] == sublist
                for i in range(len(l) - slen + 1))

assert listcontains([1], [1]) is True
assert listcontains([1,2], [1]) is True
assert listcontains([1, 2], [2]) is True
assert listcontains([1, 2], [3]) is False
assert listcontains([1, 2], [1, 2]) is True
assert listcontains([1, 2, 3], [2, 3]) is True

def distance(toks1, toks2):
    s1 = set(toks1)
    s2 = set(toks2)
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    optdiff = len(s2) - len(s1)
    #print 'optdiff:', optdiff
    overlap = s1 & s2
    un = s1 | s2
    dist = len(s2) - len(overlap)
    #print 'dist:', dist
    return dist

assert distance([], []) == 0
assert distance([], ['a']) == 1
assert distance(['a'], []) == 1
assert distance(['a','b'], ['b','a']) == 0
assert distance(['a','b'], ['a']) == 1
assert distance(['a','b'], ['a','c']) == 1


def group(somelist, func):
    match = []
    nomatch = []
    for x in somelist:
        if func(x):
            match.append(x)
        else:
            nomatch.append(x)
    return match, nomatch

# some gonzo string matching bullshit
# use hierarchical clustering instead
def maxoverlap(stringlist, tokset):
    maxlen = max(len(tokset[s]) for s in stringlist)
    minlen = 3
    so = []
    while True:
        print 'minlen:', minlen
        cnts = Counter(flatten(flatten(map(tuple, nngram(tokset[s], n) or []) for s in stringlist)
                    for n in xrange(minlen, maxlen+1)))
        if not cnts:
            if minlen == 1:
                return None, None, stringlist
            else:
                minlen -= 1
                continue
        c = {k: v * len(k) for k, v in cnts.iteritems() if v > 1}
        so = sorted(c.iteritems(), key=lambda x: (x[1], len(x[0]), x[0]), reverse=True)
        if len(so) > 1:
            break
        else:
            minlen -= 1
    best, bestscore = so[0]
    # if an entry doesn't contain the ngram with the most overlap, kick it out of the group
    match, nomatch = group(stringlist, lambda x: listcontains(tokset[x], list(best)))
    return best, match, nomatch


def levenshtein(a, b):
    return Levenshtein.distance(a, b)

assert levenshtein('', '') == 0
assert levenshtein('a', '') == 1
assert levenshtein('', 'a') == 1
assert levenshtein('a', 'a') == 0
assert levenshtein('ab', 'a') == 1
assert levenshtein('ab', 'ba') == 2
assert levenshtein('ab', 'xy') == 2


def tree_dump(t, indent=0, xlate=None):
    if t.get_left():
        tree_dump(t.get_left(), indent=indent+1, xlate=xlate)
    if not (t.get_left() and t.get_right()):
        print '%s%s' % (' ' * indent, xlate(t.get_id()) if xlate else t.get_id())
    if t.get_right():
        tree_dump(t.get_right(), indent=indent+1, xlate=xlate)

def cluster_that_shit(dist_matrix, xlate=None):
    # ref: http://brandonrose.org/clustering
    from scipy.cluster.hierarchy import ward
    # ref: https://joernhees.de/blog/2015/08/26/scipy-hierarchical-clustering-and-dendrogram-tutorial/
    from scipy.cluster.hierarchy import fcluster, to_tree
    linkage_matrix = ward(dist_matrix) #define the linkage_matrix using ward clustering pre-computed distances
    print linkage_matrix
    max_d = 5
    #clusters = fcluster(linkage_matrix, max_d, criterion='distance')
    clusters = fcluster(linkage_matrix, len(dist_matrix[0]), criterion='maxclust', R=5)
    print 'clusters:'
    print len(clusters)
    print clusters
    tree = to_tree(linkage_matrix)
    print 'tree:'
    print tree_dump(tree, xlate=xlate)


if __name__ == '__main__':

    import sys

    records = {unicode(line, 'utf8').strip(): i
                for i, line in enumerate(sys.stdin)}
    #pprint(records)

    # de-dupe record values
    nameset = {k: i for i, k in enumerate(set(records.keys()))}
    id2str = {v: k for k, v in nameset.iteritems()}
    #pprint(id2str)

    # tokenize each name
    # FIXME: strips all non-ascii strings...
    tokset = {s: tag_name.tokenize_words(s) for s in nameset.keys()}
    print 'len tokset:', len(tokset)
    #pprint(tokset, width=200)

    #sys.exit(0)

    # this sucks
    '''
    match = True
    nomatch = tokset.keys()
    while match and nomatch:
        best, match, nomatch = maxoverlap(nomatch, tokset)
        print best
        pprint(match, width=4, indent=4)

    pprint(sorted(nomatch))
    '''

    strings = [k for k, v in sorted(nameset.iteritems(), key=lambda x: x[1])]
    dist_matrix = [[0 for _ in xrange(len(strings))] for _ in xrange(len(strings))]
    for x, s in enumerate(strings):
        for y, t in enumerate(strings):
            if y >= x:
                break
            dist = levenshtein(s, t)
            dist_matrix[x][y] = dist
            dist_matrix[y][x] = dist
    #dist_matrix = [levenshtein(s, t) for s, t in itertools.combinations(strings, 2)]
    print len(dist_matrix)
    print len(dist_matrix[0])
    #print dist_matrix[0]
    #print dist_matrix
    #pprint(dist_matrix, width=1000)
    
    cluster_that_shit(dist_matrix, xlate=lambda x: '%s %s' % (x, id2str[x].encode('utf8') if x in id2str else None))

    print 'done'

    sys.exit(0)

    ntoks = len(nameset)
    dist = np.array([[float('inf')] * ntoks] * ntoks, dtype=float)

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
        for _, v in o2.iteritems():
            for x, y in itertools.combinations(v, 2):
                if x > y:
                    x, y = y, x
                edges[(x,y)] += n

    G = nx.Graph()

    G.add_weighted_edges_from(
        (x,y,w) for (x,y),w in edges.iteritems())

    print 'find_cliques:'
    for nodes in nx.find_cliques(G):
        pprint(nodes, width=10)
        print 'maxoverlap:'
        pprint(maxoverlap(nodes, tokset))

    sys.exit(0)

    def toascii(s):
        import unicodedata
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')

    # ascii-fy for display; networkx/graphviz doesn't handle utf8?!
    # round(float(distance(tokset[x], tokset[y])) / max(len(tokset[x]), len(tokset[y])), 2)
    #edges2 = {(toascii(x), toascii(y)): w
    edges2 = {(toascii(x), toascii(y)): max(len(tokset[x]), len(tokset[y])) - distance(tokset[x], tokset[y])
        for (x,y),w in edges.iteritems()}


    # G2 is ascii friendly because nx can't handle utf8 apparently

    G2 = nx.Graph()

    G2.add_weighted_edges_from(
        (x,y,w) for (x,y),w in edges2.iteritems())

    for (x, y), w in edges2.iteritems():
        G2[x][y]['label'] = w
        G2[x][y]['penwidth'] = str(w) #str(round((1.0 / max(1, w)) * 3, 1))

    print 'nx:'
    print dir(nx)
    #pprint(nx.enumerate_all_cliques(G))
    pprint(nx.number_of_cliques(G2))

    print 'G2:'
    print dir(G2)

    #G2 = nx.make_max_clique_graph(G)

    # graph via graphviz
    print 'cluster.dot...'
    nx.write_dot(G2, 'cluster.dot')
    cmd = 'fdp -Tpng -Goutputorder=edgesfirst -o cluster.png cluster.dot 2>&1'
    print cmd
    import os
    os.system(cmd)

    '''
    import matplotlib.pyplot as plt
    nx.draw(G)
    plt.show()
    '''
