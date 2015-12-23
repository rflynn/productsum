#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set ts=4 et:

from flask import Flask, render_template, redirect, request, jsonify
import time

from collections import Counter
from spider_frontend import spider_dynamo as spider
from spider_backend.domain import domain_to_canonical
from product_mapper import product2db, unknown
from search import tag_name
from bs4 import BeautifulSoup
import urllib
from urlparse import urljoin
from yurl import URL


app = Flask(__name__)

@app.route('/')
def index():
    url = None
    q = request.args.get('q')
    if q and (q.startswith('http://') or q.startswith('https://')):
        url = q
        q = search_by_url(q)
    return do_query(q=q, url=url)


def search_by_url(url):
    host = URL(url).host
    if host in product2db.Host2Map:
        # a host we know; assume it may be in our product db already!
        search_by_url = url
    else:
        # treat as third-party url that we don't know; fetch a product out of it
        search_by_url = url_to_product(url)
    return search_by_url


def do_query(q=None, url=None):
    t = time.time()
    return render_template('query.html',
                           q=urllib.unquote(q or ''),
                           url=url or '',
                           t=round(time.time()-t, 1))

def url_to_product(url):
    host = URL(url).host
    resp = spider.url_fetch(url, referer=url)
    url2, (code, headers, body, canonical_url, mimetype) = resp
    if code < 0 or code >= 400 or 'html' not in mimetype or not body:
        print 'url2 failed', url2, code
        return None
    soup = BeautifulSoup(body)
    ahrefs = soup.findAll('a', href=True)
    links = [urljoin(url, a.get('href')) for a in ahrefs]
    third_parties = {
        'plus.google.com',
    }
    third_parties_canon = {
        'facebook.com',
        'instagram.com',
        'hearstmags.com', # argh...
        'pinterest.com',
        'twitter.com',
        'tumblr.com',
        'youtube.com',
        domain_to_canonical(host)
    }
    host2url = [(URL(l), l) for l in links]
    best = [l for u, l in host2url
                if (u.host != host
                    and u.host not in third_parties
                    and domain_to_canonical(u.host) not in third_parties_canon
                    and u.scheme in ('http','https')
                    and (not u.path.endswith('.jpg'))
                    and (u.path not in ('', '/')))]
    
    # in product2db.Host2Map
    cnt_url = Counter(best)
    print best
    sorted_urls = sorted(cnt_url.iteritems(), key=lambda x: (x[0][0], x[1]), reverse=True)
    print sorted_urls
    if not sorted_urls:
        print 'not sorted_urls'
        return None
    best_url = sorted_urls[0][0]
    print 'best_url', best_url

    # now fetch the best url, and try to parse a product out of it...

    resp = spider.url_fetch(best_url, referer=url)
    url3, (code, headers, html, canonical_url, mimetype) = resp
    print url3, code
    if code < 0 or code >= 400 or 'html' not in mimetype or not body:
        print 'failed', url3, code
        return None

    ret = best_url
    prods = unknown.ProductsUnknown.from_html(best_url, html, require_prodid=False)
    if prods:
        p = prods[0]
        ret = u''
        if p.brand:
            brand = p.brand
            if brand.startswith('www.') and brand.endswith('.com'):
                brand = brand[4:-4]
            ret = 'brand:(%s) ' % brand.encode('utf8')
        elif p.merchant_name:
            brand = p.merchant_name
            if brand.startswith('www.') and brand.endswith('.com'):
                brand = brand[4:-4]
            if brand == 'ralphlauren':
                brand = 'ralpha lauren'
            ret = 'brand:(%s) ' % brand.encode('utf8')
        if p.name:
            ret += p.name
        elif p.title:
            ret += p.title
        if p.price:
            ret += u' %s%s' % ('$', str(p.price).replace('$',''))
    return ret.strip()


@app.route('/parse')
def parse():
    import unicodedata
    q = request.args.get('q')
    if q.startswith('http://') or q.startswith('https://'):
        return jsonify(result={'q':[]})
    j = tag_name.tag_query(q)
    k = [(t, [unicodedata.normalize('NFKD', x).encode('ascii','ignore') for x in l]) for t, l in j]
    return jsonify(result={'q': j, 'normalized': k})

# http://0.0.0.0:9998/search/by/url?url=http://www.elle.com/fashion/trend-reports/g27402/biggest-fashion-trends-2015/?slide=1

if __name__ == '__main__':
    tag_name.init()
    app.run(host='0.0.0.0',
            port=9998,
            debug=True)
    tag_name.shutdown()
