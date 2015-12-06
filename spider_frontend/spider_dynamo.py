# ex: set ts=4 et:

from BeautifulSoup import BeautifulSoup
from datetime import datetime
import random
import requests
from time import sleep
import traceback
from urlparse import urljoin
from yurl import URL

from spider_backend import db_dynamo as db, s3wrap, page_links
from spider_frontend import ua


_Seeds = {
    #'http://www.abercrombie.com/shop/us',
    'http://couture.zappos.com/',
    'http://shop.mango.com/US',
    'http://shop.nordstrom.com/',
    'http://us.christianlouboutin.com/us_en/',
    'http://us.louisvuitton.com/eng-us/homepage',
    'http://us.topshop.com/en',
    'http://www.barneys.com/',
    'http://www.bergdorfgoodman.com/',
    'http://www.bloomingdales.com/',
    'http://www.bluefly.com/',
    'http://www.brownsfashion.com/',
    'http://www.chanel.com/en_US/',
    'http://www.cusp.com/',
    'http://www.dermstore.com/',
    'http://www.dsw.com/',
    'http://www.farfetch.com/',
    'http://www.footcandyshoes.com/',
    'http://www.fwrd.com/',
    'http://www.gilt.com/',
    'http://www.gojane.com/',
    'http://www.harrods.com/',
    'http://www.josephstores.com/',
    'http://www.lordandtaylor.com/',
    'http://www.luisaviaroma.com/',
    'http://madisonlosangeles.com/',
    'http://www.matchesfashion.com/us/',
    'http://www.michaelkors.com/',
    'http://www.mytheresa.com/',
    'http://www.nastygal.com/',
    'http://www.neimanmarcus.com/',
    'http://www.net-a-porter.com/',
    'http://www.revolveclothing.com/',
    'http://www.saksfifthavenue.com/',
    'http://www.sephora.com/',
    'http://www.stuartweitzman.com/',
    'http://www.stylebop.com/',
    'http://www.toryburch.com/',
    'http://www.thecorner.com/us',
    'http://www.violetgrey.com/',
    'http://www.yoox.com/us/women',
    'http://www.zappos.com/',
    'http://www1.bloomingdales.com/',
    'http://www1.macys.com/',
    'https://us.burberry.com/',
    'https://www.italist.com/en',
    'https://www.modaoperandi.com/',
    'https://www.shopbop.com/',
    'https://www.ssense.com/',
    'https://www.theoutnet.com/en-US/',
    'https://www.tradesy.com/',
    'https://www.victoriassecret.com/',
}


def parse_canonical_url(body, url):
    canonical_url = None
    try:
        soup = BeautifulSoup(body)
        c = soup.find('link', rel='canonical')
        if c:
            canonical_url = c.get('href')
        else:
            og_url = soup.find('meta', property='og:url')
            if og_url:
                canonical_url = og_url.get('content')
                if canonical_url:
                    # god fucking dammit sephora
                    if 'www.sephora.com$/' in canonical_url:
                        canonical_url = canonical_url.replace('$/', '/')
        if canonical_url:
            canonical_url = urljoin(url, canonical_url)
    except Exception as e:
        print e
    return canonical_url

def get_mimetype(headers):
    # TODO: use a lib or smthn
    if not headers:
        return None
    mimetype = headers.get('Content-Type')
    if not mimetype:
        return None
    mimetype = mimetype.strip().lower()
    if ';' in mimetype:
        mimetype = mimetype.split(';')[0].strip()
    return mimetype or None

assert get_mimetype({}) is None
assert get_mimetype({'Content-Type': 'text/html'}) == 'text/html'
assert get_mimetype({'Content-Type': 'text/html;charset=UTF-8'}) == 'text/html'

def url_fetch(url, referer=None):
    headers = None
    code = -1 # unspecified error
    mimetype = None
    body = None
    canonical_url = None
    try:
        # TODO: limit size...
        # ref: http://stackoverflow.com/questions/23514256/http-request-with-timeout-maximum-size-and-connection-pooling
        r = requests.get(url,
                         allow_redirects=True,
                         headers={
                            'Accept': 'text/html',
                            'Accept-Encoding': 'gzip, deflate',
                            'Accept-Language': 'en-US,en;q=0.8',
                            'Connection': 'keep-alive',  # lies...
                            'DNT': '1',
                            'Referer': python_sucks(referer or url).encode('utf8'), # cannot handle unicode
                            'User-Agent': ua.ua(),
                         },
                         # proxies={},  # maybe someday...
                         timeout=5,
                         verify=False)  # ignore SSL certs, oh well
        code = r.status_code
        headers = sorted([(k, v) for k, v in r.headers.iteritems()])
        mimetype = get_mimetype(r.headers)
        body = r.text
        canonical_url = parse_canonical_url(body, url)
    except requests.exceptions.MissingSchema:
        code = -2
    except requests.exceptions.ConnectionError:
        code = -3
    except requests.exceptions.Timeout:
        code = -4
    except requests.exceptions.TooManyRedirects:
        code = -5
    except requests.exceptions.HTTPError:
        code = -6
    except Exception as e:
        raise
        pass
    return url, (code, headers, body, canonical_url, mimetype)


def compress_body(body):
    import gzip
    import StringIO
    stringio = StringIO.StringIO()
    with gzip.GzipFile(fileobj=stringio, mode='wb') as gzip_file:
        gzip_file.write(body.encode('utf8'))
    return stringio.getvalue()
    # TODO: consider one-liner
    #return body.encode('utf8').encode('zlib_encode')

def should_save_body(url, canonical_url, httpcode, mimetype, bodylen):
    if url != canonical_url:
        return False
    if httpcode < 0 or httpcode >= 400:
        return False
    if bodylen > 1024*1024:
        return False
    if mimetype not in ('text/html',
                        'application/xhtml+xml',
                        'text/x-server-parsed-html'):
        return False
    return True


def save_url_results(url, results):
    httpcode, headers, body, canonical_url, mimetype = results
    print url, httpcode #, results

    olen = None
    clen = None
    sha256 = None
    links = []

    # fallback to original if a better one isn't found
    canonical_url = canonical_url or url

    if body:
        olen = len(body)
        if should_save_body(url, canonical_url, httpcode, mimetype, olen):
            compressed_body = compress_body(body)
            clen = len(compressed_body)
            path, sha256 = s3wrap.write_string_to_s3('productsum-spider',
                                                     compressed_body)
            links = page_links.from_url_results(url, body)
            print '%d links: %s...' % (len(links), links[:3])
            if url in _Seeds:
                if not links:
                    print 'seed url %s has zero links?! (links: %s)' % (
                        url, links)
                    raise Exception(url)
    db.link_update_results(url, httpcode, olen, clen,
                           sha256, canonical_url, mimetype, links)
    return links

def httpcode_should_retry(code):
    return code is None or code < 0 or code >= 500

def should_fetch_again(item):
    now = db.utcnow()
    # last fetch failed, try it again sooner
    age = now - item.get('updated')
    hours = 60 * 60
    days = 24 * hours
    try_fixing_error = httpcode_should_retry(item.get('code')) and age > 4 * hours
    if try_fixing_error:
        print 'try_fixing_error now=%s updated=%s (%s) code=%s' % (
            now,
            item.get('updated'), now - item.get('updated') if item.get('updated') else None,
            item.get('code'))
    # last fetch succeeded, but it's getting stale
    is_stale = age > 14 * days
    if is_stale:
        print 'is_stale now=%s updated=%s (%s) code=%s' % (
            now,
            item.get('updated'), now - item.get('updated') if item.get('updated') else None,
            item.get('code'))
    return try_fixing_error or is_stale

def python_sucks(x):
    if x is None:
        return None
    if isinstance(x, unicode):
        return x
    if isinstance(x, str):
        return unicode(x, 'utf8')
    raise Exception(str(x))

def get_links(url, referer=None):
    print 'get_links %s' % url
    links = []
    item = db.get_url(url)
    if not item or should_fetch_again(item):
        if not item:
            print 'new %s' % url
        else:
            db.invalidate_cache(url)
            print 'updating %s' % url
        url, results = url_fetch(url, referer=referer)

        # WTF?!?!?!? i have to do this here and i don't know why...
        (code, headers, body, canonical_url, mimetype) = results
        if canonical_url and canonical_url != url:
            print u'canonical_url', canonical_url
            links.append(python_sucks(canonical_url))

        links.extend(map(python_sucks, save_url_results(url, results)))
        sleep(5 + abs(int(random.gauss(1, 3)))) # sleep somewhere from 5 to about 21 seconds
    elif item:
        if python_sucks(item.get('url_canon')) != url:
            links.append(python_sucks(item['url_canon']))
        if item.get('links'):
            links.extend(map(python_sucks, item['links']))
    return links

def ok_to_spider(url):
    return (
        'revolveclothing.com/r/ajax/crawlerDiscovery.jsp' not in url
    )

def traverse(url, fqdn): # breadth-first traversal
    # python's unicode support is horrible
    # best spider url to test this with is yoox; they have a bunch of crazy unicode urls
    urls = [python_sucks(url)]
    while urls:
        next_url = urls.pop(0)
        if ok_to_spider(url):
            links = get_links(next_url, referer=url)
            #random.shuffle(links)
            while links:
                assert links[0] is not None
                assert isinstance(links[0], unicode)
                l = links.pop(0)
                if l != next_url and URL(l).host.lower() == fqdn and l not in urls and ok_to_spider(l):
                    # stay in the same fdqn...
                    get_links(l, referer=next_url) # ignore results...
                    urls.append(l)

# TODO: have us try all seeds at all times; schedule each one...
def run(url):
    db.init()
    keepgoing = True
    try:
        while keepgoing:
            if not url:
                url = random.choice(list(_Seeds))
            fqdn = URL(url).host.lower()
            traverse(url, fqdn)
            sleep(30)
    except KeyboardInterrupt:
        print 'KeyboardInterrupt...'
        keepgoing = False
    db.shutdown()

if __name__ == '__main__':
    import sys
    url = None
    if len(sys.argv) > 1:
        url = sys.argv[1]
        assert url in _Seeds
    print 'url:', url
    run(url)

