# ex: set ts=4:
# -*- coding: utf-8 -*-

from yurl import URL
import re


def url_to_domain(url):
    return URL(url).host.lower() or None

assert url_to_domain(u'http://') is None
assert url_to_domain(u'http://x.com/') == u'x.com'
assert url_to_domain(u'http://X.COM/') == u'x.com'
assert url_to_domain(u'http://x.com:80/') == u'x.com'
assert url_to_domain(u'http://x.co.uk/') == u'x.co.uk'


def looks_like_an_ip(domain):
    return looks_like_ipv4(domain)


def looks_like_ipv4(domain):
    return bool(re.match('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', domain))

assert looks_like_ipv4('0.0.0.0') == True
assert looks_like_ipv4('127.0.0.1') == True
assert looks_like_ipv4('foo.bar.baz.quux') == False
assert looks_like_ipv4('foo1.bar.baz.quux') == False
assert looks_like_ipv4('1.2.3.com') == False


def looks_like_ipv6(domain):
    return bool(re.match('^\[[0-9a-fA-F:]{1,32}\]$', domain))


def is_second_level_domain(s):
    return s in ('co', 'com')


def domain_to_canonical_uk(domain):
    m = re.search('([^.]+\.(?:co|org|me|ltd|plc|net|sch|ac|gov|mod|nhs|police)\.uk)$', domain)
    if m:
        return m.groups(0)[0]
    return domain


def domain_to_canonical_au(domain):
    m = re.search('([^.]+\.(?:asn|com|net|id|org|edu|gov|csiro|act|nsw|nt|qld|sa|tas|vic|wa)\.au)$', domain)
    if m:
        return m.groups(0)[0]
    return domain


def domain_to_canonical_jp(domain):
    m = re.search('([^.]+\.(?:ac|ad|co|ed|go|gr|lg|ne|or)\.jp)$', domain)
    if m:
        return m.groups(0)[0]
    return domain


def domain_to_canonical(domain):
    if not domain:
        return None
    if looks_like_an_ip(domain):
        return domain
    domain = domain.lower()
    domain = domain.lstrip('.').rstrip('.') # strip dots...
    domain = re.sub('[.]+', '.', domain, flags=re.UNICODE) # normalize dots
    if domain.endswith('.uk'):
        return domain_to_canonical_uk(domain)
    elif domain.endswith('.au'):
        return domain_to_canonical_au(domain)
    elif domain.endswith('.jp'):
        return domain_to_canonical_jp(domain)
    parts = domain.split('.')
    keep_last = 2  # e.g. 'foo.com'
    if len(parts) > 2 and is_second_level_domain(parts[-2]):
        # e.g. 'foo.co.uk'
        keep_last = 3
    dom = '.'.join(parts[-keep_last::])
    # trim leading/trailing garbage
    sanitized = re.sub('^[^a-z0-9]+|[^a-z0-9]+$', '', dom, flags=re.UNICODE)
    return sanitized

assert domain_to_canonical(None) == None
assert domain_to_canonical(u'') == None
assert domain_to_canonical(u'localhost') == u'localhost'
assert domain_to_canonical(u'127.0.0.1') == u'127.0.0.1'
assert domain_to_canonical(u'www.x.com') == u'x.com'
assert domain_to_canonical(u'WWW.X.COM') == u'x.com'
assert domain_to_canonical(u'www.x.co') == u'x.co'
assert domain_to_canonical(u'x.co.uk') == u'x.co.uk'
assert domain_to_canonical(u'www.x.co.uk') == u'x.co.uk'
assert domain_to_canonical(u'www.x.co.co') == u'x.co.co'
assert domain_to_canonical(u'www.facebook.com') == u'facebook.com'
assert domain_to_canonical(u'123.foobar.com') == u'foobar.com'
# fucked up stuff in real world...
assert domain_to_canonical(u'123.foobar.com$') == u'foobar.com'
assert domain_to_canonical(u'123.foobar.com.') == u'foobar.com'
assert domain_to_canonical(u'.foo.com') == u'foo.com'
assert domain_to_canonical(u'foo..com') == u'foo.com'
assert domain_to_canonical(u'amazon.com.mx') == u'amazon.com.mx'
assert domain_to_canonical(u'www.amazon.com.mx') == u'amazon.com.mx'

