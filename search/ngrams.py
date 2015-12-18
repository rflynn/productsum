# ex: set ts=4 et:
# -*- coding: utf-8 -*-

from collections import Counter
from pprint import pprint
import re

import tag_name


def nngram(ngram, n):
    if len(ngram) < n:
        return None
    return [ngram[i:i+n] for i in xrange(len(ngram) - n + 1)]

assert nngram([1], 2) is None
assert nngram([1], 1) == [[1]]
assert nngram([1,2,3], 1) == [[1],[2],[3]]
assert nngram([1,2,3], 2) == [[1,2],[2,3]]

if __name__ == '__main__':

    import sys

    n = 2
    if len(sys.argv) > 1:
        n = int(sys.argv[1])

    lines = [unicode(line, 'utf8') for line in sys.stdin]
    ngrams = [nngram(tag_name.tokenize(l), n) for l in lines]
    nng = tag_name.flatten(ng for ng in ngrams if ng)
    cnt = Counter(map(tuple, nng))

    for ng, c in sorted(cnt.items(), key=lambda x: x[1], reverse=True):
        print u' '.join(ng).encode('utf8')

