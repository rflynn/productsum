# vim: set ts=4 et:

import codecs
from collections import defaultdict
from pprint import pprint, pformat
import re
import string


def flatten(l):
    return [item for sublist in l for item in sublist]

def do_tokenize(s):
    assert isinstance(s, unicode)
    sprep = s.strip().lower()
    if not sprep:
        return []
    return re.findall(ur'(\d+|\w+|\S)', sprep, re.UNICODE)

def tokenize(s):
    assert isinstance(s, unicode)
    return [t for t in do_tokenize(s)
                if t not in string.punctuation or t in u"&'+$"]

def tags_load(filepath, tag):
    with codecs.open(filepath, encoding='utf-8') as f:
        return [(tag, tokenize(line)) for line in f if line]

def reverse_index(l):
    index = defaultdict(list)
    for tag, tokens in l:
        index[tokens[0]].append((tag, tokens))
    return index

def build_tag_reverse_index():
    tags = [tags_load('./data/tag.%s.csv' % tag, tag)
                for tag in ['adj',
                            'brand',
                            'color',
                            'material',
                            'ngram2',
                            'pattern',
                            'product',
                            'quantity',
                            'size']]
    return reverse_index(flatten(tags))

# decide how well a [(tag, [token,...]),...] has performed
# all tokens in the search appear in perm; if unmatched then tag is None
# we have to be careful not to include too many business rules here (hopefully);
# instead, reward a match that covers more tokens with fewer tags, includes multiple tags, etc.
def score_match_perm(perm):
    tags = set(tag for tag, _ in perm)
    # favor longer successful matches
    num = sum(int(tag is not None) + len(tokens)
                for tag, tokens in perm)
    # favor more varied tags
    num += len(tags)
    return float(num) / max(1, len(perm))

def match_tree_flatten(mt, state=None, done=None):
    if state is None:
        state = []
        done = []
    for tag, child in mt:
        if child:
            match_tree_flatten(child, state + [tag], done)
        else:
            done.append(state + [tag])
    return done

def match_tree2(qtoks, ri):
    return [
        ((tag,p),
         match_tree2(qtoks[len(p):], ri)
                 if qtoks > p else None)
             for tag, p in ri.get(qtoks[0], [])
                 if qtoks[:len(p)] == p] + \
         [((None, qtoks[:1]), # account for no match
             match_tree2(qtoks[1:], ri)
                if len(qtoks) > 1 else None)]

def match_best(q, ri):
    if not q:
        return []
    #print repr(q)
    assert isinstance(q, unicode)
    #qtoks = tokenize(q[:80]) # FIXME: chop for performance
    qtoks = tokenize(q)
    #print qtoks
    '''
    for token in qtoks:
        print '%-12s %s' % (token, ri.get(token))
    '''
    mt = match_tree2(qtoks, ri)
    #pprint(mt)
    permutations = match_tree_flatten(mt)
    #print '%d permutations: %s' % (len(permutations), permutations)
    #print len(permutations)
    scoredperm = [(score_match_perm(perm), perm) for perm in permutations]
    #pprint(sorted(scoredperm, reverse=True)[:3], width=240)
    bestscore, bestperm = max(scoredperm) if scoredperm else (None, None)
    return bestperm

def tag_query(qstr, reverseIndex):
    tokens = tokenize(qstr)
    #print 'tokens:', tokens
    #tokids, tokens_tagged = tokenize_search(db, q)
    bestperm = match_best(qstr, reverseIndex)
    return bestperm

def run_tests(ri):
    tests = [
        u'Ike Behar Check Dress Shirt, Brown/Blue',
        u'RED VALENTINO flower print sheer shirt',
        u'VINTAGE by Jessica Liebeskind Leather Hobo Messenger Bag',
        u'Alexander McQueen Leopard-Print Pony Hair Envelope Clutch Bag',
        u'Deborah Lippmann Luxurious Nail Color - Whip It (0.5 fl oz.)',
        u'Cashmere Cleanse Facial Brush Head',
        u'Clarisonic Luxe Cashmere Cleanse Facial Brush Head Clarisonic 1 Pc Brush Head Facial Brush Head Women',
        u'Christian Louboutin Cataclou Studded Red Sole Demi-Wedge Sandal, Black/Dark Gunmetal',
        u'Christian Louboutin Cataclou Studded Suede Red Sole Wedge Sandal, Capucine/Gold',
    ]
    for t in tests:
        tq = tag_query(t, ri)
        #print 'bestperm:', pformat(tq, width=200)
        print tq

if __name__ == '__main__':

    ri = build_tag_reverse_index()
    run_tests(ri)

    #import sys
    #for line in sys.stdin:
    #    print tag_query(unicode(line, 'utf8'), ri)

