# vim: set ts=4 et:
# -*- coding: utf-8 -*-

import codecs
from collections import defaultdict
import itertools
from pprint import pprint, pformat
import re
import string
from watchdog.observers import Observer
import traceback


def flatten(l):
    return [item for sublist in l for item in sublist]

def tokenize(s):
    assert isinstance(s, unicode)
    return re.findall(ur"(\d+(?:\.\d+)?|\w+|[&'+$/\"-])", s.lower(), re.UNICODE)

def tokenize_words(s):
    assert isinstance(s, unicode)
    return re.findall(ur"(\d+(?:\.\d+)?|\w+)", s.lower(), re.UNICODE)

class TokeParser(object):
    def __init__(self, tag):
         self.tag = tag
    def consume(self, toks):
        return 0

class ReverseIndex(TokeParser):
    def __init__(self, tag, filepath):
        self.tag = tag
        self.index = defaultdict(list)
        with codecs.open(filepath, encoding='utf-8') as f:
            for line in f:
                if line:
                    toks = tokenize(line)
                    if toks:
                        if toks not in self.index[toks[0]]:
                            self.index[toks[0]].append(toks)
    def consume(self, qtoks):
        match = []
        for toks in self.index.get(qtoks[0]) or []:
            if toks == qtoks[:len(toks)]:
                if len(toks) > len(match):
                    match = toks
        return len(match)

class PriceParser(TokeParser):
    def __init__(self):
        self.tag = 'price'
    def consume(self, qtoks):
        if qtoks[0] in (u'$', u'€', u'£', u'¥') and len(qtoks) > 1:
            try:
                if re.match(r'^(?:\d{1,6}|(?:\d{1,3},)?\d{3})(?:\.\d{2})?$', qtoks[1]):
                    return 2
            except:
                pass
        return 0

class QuotedParser(TokeParser):
    def __init__(self):
        self.tag = 'quoted'
    def consume(self, qtoks):
        try:
            if qtoks[0] in (u"'", u'"') and len(qtoks) > 2:
                if qtoks[1] == 's': # FIXME: ugh
                    return 0
                try:
                    nextquote = qtoks.index(qtoks[0], 1)
                except ValueError:
                    return 0
                return nextquote + 1
        except Exception as e:
            traceback.print_exc()
        return 0

def is_int(x):
    try:
        x = int(x)
        return True
    except ValueError:
        return False

def is_float(x):
    try:
        x = float(x)
        return True
    except ValueError:
        return False

def is_number(x):
    return is_int(x) or is_float(x)

def consume_fraction(toks):
    if len(toks) < 3:
        return 0
    if is_int(toks[0]) and toks[1] == '/' and is_int(toks[2]):
        return 3
    return 0

class SizeParser(TokeParser):
    '''
size:
"size" "newborn"
"size" number
int fract? ("inches" | "inch" | '"')
int? fract "qt"
int? "-"? fract ("carat" | "ct") ("tw" | "t" "w")?
number "ml"
number "g"
number "mm"
number "liter"
number ("inches" | "inch" | '"')
number ("ounce" | "oz")
number ("gallons" | "gallon")
number ("fl" "oz" | "floz")
    '''
    def __init__(self):
        self.tag = 'size'
    def consume(self, qtoks):
        try:
            if qtoks[0] == 'size' and len(qtoks) > 1:
                if qtoks[1] == 'newborn':
                    return 2
                if is_number(qtoks[1]):
                    return 2
            elif is_int(qtoks[0]):
                start = 0
                if len(qtoks) > 3 and qtoks[1] == '-':
                    start = 2
                fr = consume_fraction(qtoks[start:])
                if fr:
                    # int fract ...
                    cnt = start + fr
                    if qtoks[cnt] in {'inches','inch','"'}:
                        return cnt+1
                    elif qtoks[cnt] == 'qt':
                        return cnt+1
                    elif qtoks[cnt] in ('carat', 'ct'):
                        cnt += 1
                        if qtoks[cnt] == 'tw':
                            return cnt + 1
                        elif qtoks[cnt] == 't' and qtoks[cnt+1] == 'w':
                            return cnt + 2
                        return cnt
            if is_number(qtoks[0]) and len(qtoks) > 1:
                if qtoks[1] == 'ml':
                    return 2
                elif qtoks[1] == 'g':
                    return 2
                elif qtoks[1] == 'mm':
                    return 2
                elif qtoks[1] == 'liter':
                    return 2
                elif qtoks[1] in {'inches', 'inch', '"'}:
                    return 2
                elif qtoks[1] in {'ounce', 'oz'}:
                    return 2
                elif qtoks[1] in {'gallons', 'gallon'}:
                    return 2
                elif qtoks[1] in {'qt', 'quart'}:
                    return 2
                elif qtoks[1] == 'floz':
                    return 2
                elif qtoks[1] in {'fl', 'fluid'} and len(qtoks) > 2 and qtoks[2] == 'oz':
                    return 3
        except Exception as e:
            traceback.print_exc()
        return 0

class QuantityParser(TokeParser):
    '''
quantity:
"x" int
int "x"
int "ea"
int ("pc" | "piece")
int "-"? ("count" | "ct")
"set" "of" int
("one"|"two"|"three"|"four"|"five"|"six"|"seven"|"eight"|"nine"|"ten"|"eleven"|"twelve") ("piece" | "pack" | "pk")
"assorted"? int "-"? "pack"
    '''
    def __init__(self):
        self.tag = 'quantity'
    def consume(self, qtoks):
        try:
            if qtoks[0] == 'x' and is_int(qtoks[1]):
                return 2
            elif is_int(qtoks[0]) and len(qtoks) > 1:
                if qtoks[1] == 'x':
                    return 2
                elif qtoks[1] == 'ea':
                    return 2
                elif qtoks[1] in {'piece', 'pieces', 'pc'}:
                    return 2
                elif qtoks[1] in {'count', 'ct'}:
                    return 2
                elif qtoks[1] == '-' and len(qtoks) > 2 and qtoks[2] in ('count', 'ct'):
                    return 3
            elif qtoks[0] == 'set' and len(qtoks) > 2 and qtoks[1] == 'of' and is_int(qtoks[2]):
                return 3
            elif len(qtoks) > 2 and qtoks[1] == '-' and qtoks[2] == 'pack':
                return 3
            elif len(qtoks) > 1 and qtoks[1] == 'pack':
                return 2
            elif qtoks[0] in {'single', 'dual', 'triple', 'quad', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve'} and len(qtoks) > 1 and qtoks[1] in {'piece', 'pack', 'pk'}:
                return 2
            elif qtoks[0] == 'assorted' and len(qtoks) > 1 and is_int(qtoks[1]):
                if len(qtoks) > 3 and qtoks[2] == '-' and qtoks[3] == 'pack':
                    return 4
                elif len(qtoks) > 2 and qtoks[2] == 'pack':
                    return 3
        except Exception as e:
            traceback.print_exc()
        return 0


class Parser(object):

    def __init__(self):
        self.parsers = []
        self._build_tag_reverse_index()
        self.add_parser(PriceParser())
        self.add_parser(QuotedParser())
        self.add_parser(QuantityParser())
        self.add_parser(SizeParser())

    def add_parser(self, parser):
        self.parsers.append(parser)

    def _build_tag_reverse_index(self):
        for tag in ['brand',
                    'color',
                    'demographic',
                    'material',
                    'ngram2',
                    'pattern',
                    'product',
                    #'quantity',
                    #'size'
                    ]:
            ri = ReverseIndex(tag, './data/tag.%s.csv' % tag)
            self.add_parser(ri)

    def match_list(self, qtoks):
        matches = []
        for i, tok in enumerate(qtoks or []):
            tokmatches = []
            tokl = qtoks[i:]
            for p in self.parsers:
                consumed = p.consume(tokl)
                if consumed > 0:
                    tokmatches.append((p.tag, tokl[:consumed]))
            if not tokmatches:
                tokmatches = [(None, [tok])]
            matches.append((tok, tokmatches))
        return matches

class BrandObj(object):
    def __init__(self):
        pass

class PriceObj(object):
    def __init__(self):
        pass

class ProductObj(object):
    def __init__(self):
        pass

class SeparatorObj(object):
    def __init__(self):
        pass

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

def match_list_iter2(ml):
    for p in itertools.product(*[matches for tok, matches in ml]):
        a = []
        i = 0
        while i < len(p):
            a.append(p[i])
            i += len(p[i][1])
        yield a

P = Parser()

def regen_parser():
    global P
    P = Parser()

def match_best(q):
    if not q:
        return []
    #print repr(q)
    assert isinstance(q, unicode)
    qtoks = tokenize(q)
    if not qtoks:
        return []

    #ml = match_list(qtoks, ri)
    ml = P.match_list(qtoks)

    #print 'match list: %s' % (pformat(ml, width=200))
    permutations = match_list_iter2(ml)
    #print 'match_list_iter: %s' % (pformat(mli, width=200),)

    scoredperm = [(score_match_perm(perm), perm) for perm in permutations]
    #pprint(sorted(scoredperm, reverse=True)[:3], width=240)
    bestscore, bestperm = max(scoredperm) if scoredperm else (None, None)
    return bestperm

def tag_query(qstr):
    tokens = tokenize(qstr)
    #print 'tokens:', tokens
    bestperm = match_best(qstr)
    bestperm = list(bestperm)
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
                    regen_parser()
    def on_created(self, event):
        pass
    def on_modified(self, event):
        pass
    def on_moved(self, event):
        pass
    def on_deleted(self, event):
        pass

def init():
    global observer
    observer = Observer()
    observer.schedule(Handler(), './data/', recursive=True)
    observer.start()

def shutdown():
    observer.stop()
    observer.join()

def run_tests():
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
        u"'A Novel Romance' Fluidline Eye Pencil",
        u"$25.99 lol",
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
