# vim: set ts=4 et:
# -*- coding: utf-8 -*-

import codecs
from collections import defaultdict
import itertools
from pprint import pprint, pformat
import re
import string
from watchdog.observers import Observer


def flatten(l):
    return [item for sublist in l for item in sublist]

def tokenize(s):
    assert isinstance(s, unicode)
    return re.findall(ur"(\d+(?:\.\d+)?|\w+|[&'+$/\"-])", s.lower(), re.UNICODE)

def tokenize_words(s):
    assert isinstance(s, unicode)
    return re.findall(ur"(\d+(?:\.\d+)?|\w+)", s.lower(), re.UNICODE)

def tags_load(filepath, tag):
    try:
        with codecs.open(filepath, encoding='utf-8') as f:
            return [(tag, tokenize(line)) for line in f if line]
    except Exception as e:
        print e
        raise

def reverse_index(l):
    index = defaultdict(list)
    for tag, tokens in l:
        if (tag, tokens) not in index[tokens[0]]:
            index[tokens[0]].append((tag, tokens))
    return index

def build_tag_reverse_index():
    tags = [tags_load('./data/tag.%s.csv' % tag, tag)
                for tag in ['brand',
                            'color',
                            'demographic',
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
    # favor brand appearing first, ugh
    if perm:
        num += perm[0][0] == 'brand'
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

def match_list(qtoks, ri):
    return [(tok, [(tag, toks)
                        for tag, toks in ri.get(tok, [])
                            if toks == qtoks[i:i+len(toks)]] or [(None, [tok])])
                for i, tok in enumerate(qtoks or [])]

def match_list_iter(ml, idx=0):
    if len(ml) > idx:
        tok, matches = ml[idx]
        for tag, toks in matches:
            yield [(tag, toks)] + list(match_list_iter(ml, idx + len(toks)))

def match_list_iter2(ml):
    for p in itertools.product(*[matches for tok, matches in ml]):
        a = []
        i = 0
        while i < len(p):
            a.append(p[i])
            i += len(p[i][1])
        yield a

def match_best(q, ri):
    if not q:
        return []
    #print repr(q)
    assert isinstance(q, unicode)
    #qtoks = tokenize(q[:80]) # FIXME: chop for performance
    qtoks = tokenize(q)
    if not qtoks:
        return []

    ml = match_list(qtoks, ri)
    #print 'match list: %s' % (pformat(ml, width=200))
    mli = match_list_iter2(ml)
    #print 'match_list_iter: %s' % (pformat(mli, width=200),)

    '''
    mt = match_tree2(qtoks, ri)
    #print 'match tree: %s' % (pformat(mt, width=200))
    permutations = match_tree_flatten(mt)
    print '%d permutations: %s' % (len(permutations), pformat(permutations, width=200))
    print len(permutations)
    '''

    permutations = mli

    scoredperm = [(score_match_perm(perm), perm) for perm in permutations]
    #pprint(sorted(scoredperm, reverse=True)[:3], width=240)
    bestscore, bestperm = max(scoredperm) if scoredperm else (None, None)
    return bestperm

ri = None

def get_reverse_index(force=False):
    global ri
    if (not ri) or force:
        print 'building reverse index (force=%s)...' % force
        ri = build_tag_reverse_index()
    return ri

def tag_query(qstr):
    price = None
    m = re.search(ur'(([$€£¥])\s?(\d+(?:\.\d+)?))$', qstr, re.UNICODE)
    if m:
        raw, sign, amount = m.groups()
        price = ('price', [sign + amount])
        qstr = qstr[:-len(raw)].rstrip()
    tokens = tokenize(qstr)
    #print 'tokens:', tokens
    ri = get_reverse_index()
    bestperm = match_best(qstr, ri)
    bestperm = list(bestperm)
    if price:
        bestperm.append(price)
    return bestperm


def to_original_case(tq, qstr):
    '''
    re-convert lowercase'd tokens back to their original case
    '''
    lqstr = qstr.lower()
    tq2 = []
    idx = 0
    for tag, toks in tq:
        toks2 = []
        for tok in toks:
            #print 'lsqtr=%s tok=%s idx=%s' % (lqstr, tok, idx)
            i2 = lqstr.index(tok, idx)
            t2 = qstr[i2:i2+len(tok)]
            toks2.append(t2)
            idx = i2 + len(tok)
        tq2.append((tag, toks2))
    return tq2

assert to_original_case([], u'') == []
try:
    assert to_original_case([('tag', [u'a'])], u'') == []
    raise Exception('expected failure')
except:
    pass
assert to_original_case([('tag', [u'a'])], u'A') == [('tag', [u'A'])]
assert to_original_case([('tag', [u'b'])], u'AB') == [('tag', [u'B'])]


def to_original_substrings(tq, qstr):
    lqstr = qstr.lower()
    tq2 = []
    idx = 0
    for tag, toks in tq:
        t2 = []
        for tok in toks:
            i2 = lqstr.index(tok, idx)
            t2.append(i2)
            idx = i2 + len(tok)
        tq2.append((tag, [qstr[t2[0]:t2[-1]+len(toks[-1])]]))
    return tq2

assert to_original_substrings([('tag', [u'a', u'b'])], u'A B') == [('tag', [u'A B'])]


# watch our tag files, and if they change, re-load the reverse index

observer = None

class Handler(object):
    def dispatch(self, event):
        if event.event_type in ('created', 'modified'):
            if not event.is_directory:
                if event.src_path.endswith('.csv'):
                    print 'reloading index... (%s)' % event.src_path
                    get_reverse_index(True)
    def on_created(self, event):
        pass
    def on_modified(self, event):
        pass
    def on_moved(self, event):
        pass
    def on_deleted(self, event):
        pass

def init():
    # initial ri
    get_reverse_index()
    global observer
    observer = Observer()
    observer.schedule(Handler(), './data/', recursive=True)
    observer.start()

def shutdown():
    observer.stop()
    observer.join()

def run_tests():
    ri = get_reverse_index()
    tests = [
        u'RED VALENTINO flower print sheer shirt',
        u'Ike Behar Check Dress Shirt, Brown/Blue',
        u'VINTAGE by Jessica Liebeskind Leather Hobo Messenger Bag',
        u'Alexander McQueen Leopard-Print Pony Hair Envelope Clutch Bag',
        u'Deborah Lippmann Luxurious Nail Color - Whip It (0.5 fl oz.)',
        u'Cashmere Cleanse Facial Brush Head',
        u'Clarisonic Luxe Cashmere Cleanse Facial Brush Head Clarisonic 1 Pc Brush Head Facial Brush Head Women',
        u'Christian Louboutin Cataclou Studded Red Sole Demi-Wedge Sandal, Black/Dark Gunmetal',
        u'Christian Louboutin Cataclou Studded Suede Red Sole Wedge Sandal, Capucine/Gold',
        u'BLACK BROWN 1826 Classic-Fit Dress Shirt',
        u'Le Creuset 2 1/4 Qt. Saucier Pan - Soleil',
        u'Flight 001 Cateye Sunglasses Eye Mask',
        u'Laura Mercier Tinted Moisturizer SPF20 - Mocha, 40ml',
        u'Lucien Piccard Carina Rose Tone Stainless Steel Rose Tone Dial', # it's a watch, but doesn't say so
        u'SAM EDELMAN Nixon Heel in Black',
        u'Christian Louboutin Tucskick GIittered Red Sole Pump, White/Gold', # typo "GIittered"
        u'SHISEIDO Extra-Smooth Sun Protection Cream SPF 38/2 oz. $32',
        u'LOUISE ET CIE Gold-Plated Glass Pearl Stud Earrings',
        u'SWAROVSKI Solitaire Swarovski Crystal Stud Earrings $69', # when 2 instances of brand appear, we should favor the prefix
        u'Glam-To-Go Cheek, Eye & Lip Travel Case', # ampersand...
        u'LA MER CRÈME DE LA MER', # brand "LA MER" appears twice, favor first...
        u'T-shirt à imprimé "Undecorated" bleu marine',
        u'-',
        u'Smoothing and Relaxing Eye Patches x 7',
        u'FOUNTAIN The Hair Molecule - 8 oz',
        u'Anne Klein Gold-Tone Pink Leather Charger Bracelet',
        u'Wet n Wild Megalast Lip Color in Sugar Plum Fairy',
        u'2-Piece Plaid Pajama Set',
        u'Black Label Open-Front Cashmere Cardigan, Long-Sleeve Cashmere Sweater & Mid-Rise Matchstick Jeans',
        # XXX: FIXME: TOO SLOW....
        u'Le Vian Green Tourmaline (7/8 ct. t.w.), Peridot (7/8 ct. t.w.), Lemon Quartz (7/8 ct. t.w.) and Chocolate (1/3 ct. t.w.) and White Diamond (1/10 ct. t.w.) Ring in 14k Gold',
    ]
    for t in tests:
        print t.encode('utf8')
        tq = tag_query(t)
        #print 'bestperm:', pformat(tq, width=200)
        pprint(tq, width=200)

if __name__ == '__main__':

    import sys
    from pprint import pprint
    from collections import Counter

    if sys.argv and sys.argv[1:] == ['test']:
        run_tests()
        sys.exit(0)

    nones = Counter()

    for line in sys.stdin:
        #if len(line) > 80:
        #    print "TOO LONG WE'RE SLOW", line.strip()
        #    continue
        print line.strip()
        tq = tag_query(unicode(line, 'utf8'))
        pprint(tq, width=500)
        print
        for t, x in itertools.groupby(tq, lambda x: x[0] is None):
            if t:
                x = [x[0] for _, x in x]
                if re.search(r'\w+', x[0], re.UNICODE) and re.search(r'\w+', x[-1], re.UNICODE):
                    nones[tuple(x)] += 1

        unmatched_ngrams = sorted([(n, x) for x, n in dict(nones).iteritems() if n > 1], reverse=False)
        pprint(unmatched_ngrams, width=100)
