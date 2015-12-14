#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set ts=4 et:

from flask import Flask, render_template, redirect, request
import time

from collections import Counter
from spider_frontend import spider_dynamo as spider
from spider_backend.domain import domain_to_canonical
from product_mapper import product2db
from bs4 import BeautifulSoup
import urllib
from urlparse import urljoin
from yurl import URL


app = Flask(__name__)

@app.route('/')
def index():
    return do_query(q=request.args.get('q'))

def do_query(q=None):
    t = time.time()
    return render_template('query.html',
                           q=q or '',
                           t=round(time.time()-t, 1))

def url_to_product(url):
    host = URL(url).host
    resp = spider.url_fetch(url, referer=url)
    url2, (code, headers, body, canonical_url, mimetype) = resp
    if code < 0 or code >= 400 or 'html' not in mimetype or not body:
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
                    and u.scheme in ('http','https'))]
    
    # in product2db.Host2Map
    cnt_url = Counter(best)
    print best
    sorted_urls = sorted(cnt_url.iteritems(), key=lambda x: (x[0][0], x[1]), reverse=True)
    print sorted_urls
    if not sorted_urls:
        return None
    best_url = sorted_urls[0]
    print 'best_url', best_url
    return best_url[0]

# http://0.0.0.0:9998/search/by/url?url=http://www.elle.com/fashion/trend-reports/g27402/biggest-fashion-trends-2015/?slide=1

@app.route('/search/by/url/')
def search_by_url():
    url = request.args.get('q')
    host = URL(url).host
    if host in product2db.Host2Map:
        # a host we know; assume it may be in our product db already!
        search_by_url = url
    else:
        # treat as third-party url that we don't know; fetch a product out of it
        search_by_url = url_to_product(url)
    '''
    go_to = '/'
    if search_by_url:
        go_to += '?q=' + search_by_url
    return redirect(go_to)
    '''
    return do_query(q=search_by_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0',
            port=9998,
            debug=True)

