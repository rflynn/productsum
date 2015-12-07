# ex: set ts=4:
# -*- coding: utf-8 -*-

from BeautifulSoup import BeautifulSoup
import re


def nth(maybelist, index, val=None):
    try:
        return maybelist[index]
    except:
        return val

def xstrip(s):
    return s.strip() if s is not None else None

def normstring(s):
    return xstrip(re.sub('\s+', ' ', s)) if s is not None else None

def dehtmlify(s):
    if not s: return s
    soup = BeautifulSoup(s, convertEntities=BeautifulSoup.HTML_ENTITIES)
    return u''.join(t.text if hasattr(t, 'text') else t
                for t in soup.contents)

def maybe_join(joinwith, joinme):
    if joinme is None:
        return None
    if isinstance(joinme, list):
        return joinwith.join(joinme)
    return joinme

def xboolstr(x):
    if x is None:
        return x
    x = x.strip().lower()
    if x == 'false':
        return False
    elif x == 'true':
        return True
    return None

def xint(x):
    if x is None:
        return None
    try:
        return int(xstrip(x))
    except:
        return None

def balanced(s, updown=None):
    updown = updown or (lambda c: 1 if c == '{' else -1 if c == '}' else 0)
    pos = [(i, updown(c)) for i, c in enumerate(s) if updown(c) != 0]
    cnt = 0
    p = 0
    for p, adj in pos:
        cnt += adj
        if cnt <= 0:
            break
    if cnt != 0:
        p = -1
    return p

if __name__ == '__main__':
    assert dehtmlify(None) is None
    assert dehtmlify('') == ''
    assert dehtmlify('<p>') == ''
    assert dehtmlify('<p></p>') == ''
    assert dehtmlify('<p>text</p>') == 'text'
    assert dehtmlify(u'UGG<sup>®</sup> Australia') == u'UGG® Australia' # FIXME
    assert dehtmlify('<p>te<sup>x</sup>t</p>') == 'text'
    assert dehtmlify('<p>te<sup><sup>x</sup></sup>t</p>') == 'text'
    assert dehtmlify('a &amp; b') == 'a & b'

