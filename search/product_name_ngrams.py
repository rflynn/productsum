# ex: set ts=4 et:
# -*- coding: utf-8 -*-

from collections import Counter
import nltk
from nltk.util import ngrams
from pprint import pprint
import re


def flatten(l):
    return [item for sublist in l for item in sublist]


if __name__ == '__main__':

    with open('/tmp/url_product_name.csv', 'rb') as f:
        names = [line for line in f]

    cleannames = [re.sub('[|()]', '', name) for name in names]

    tokens = [nltk.word_tokenize(name) for name in cleannames]

    n = 2
    ngrams = flatten([list(ngrams(toks, n)) for toks in tokens])

    cnt = Counter(ngrams)
    pprint(sorted(cnt.iteritems(), key=lambda x: x[1], reverse=True))

