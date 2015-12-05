# ex: set ts=4 et:

from BeautifulSoup import BeautifulSoup
import random
import requests
import time
import traceback
from urlparse import urljoin
from yurl import URL

from spider_backend import db, s3wrap, page_links


Agents = [
    # googlebot
    'Googlebot/2.1 (+http://www.googlebot.com/bot.html)',
    # chrome
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.71 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
    # firefox
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1',
    'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0',
    # ie
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 7.0; InfoPath.3; .NET CLR 3.1.40767; Trident/6.0; en-IN)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/5.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/4.0; InfoPath.2; SV1; .NET CLR 2.0.50727; WOW64)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)',
    'Mozilla/4.0 (Compatible; MSIE 8.0; Windows NT 5.2; Trident/6.0)',
    # safari
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.13+ (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/534.55.3 (KHTML, like Gecko) Version/5.1.3 Safari/534.53.10',
]

def ua():
    return random.choice(Agents)

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

def url_fetch(url):
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
                            'Referer': 'https://www.google.com/',
                            'User-Agent': ua(),
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

def should_save_body(mimetype, bodylen):
    if bodylen > 1024*1024:
        return False
    if mimetype not in ('text/html',):
        return False
    return True


def do_extract_urls(link_id, url, body):
    links = page_links.from_url_results(url, body)
    print 'processing', len(links), 'links:', sorted(links)[:3], '...'
    for l in links:
        try:
            db.insert_url(link_id, URL(l).validate())
        except:
            print 'do_extract_urls...'
            traceback.print_exc()


def save_url_results(link_id, url, ts, results):
    httpcode, headers, body, canonical_url, mimetype = results
    print link_id, url, ts#, results

    olen = None
    clen = None
    sha256 = None

    # fallback to original if a better one isn't found
    canonical_url = canonical_url or url

    if body:
        olen = len(body)
        if should_save_body(mimetype, olen):
            compressed_body = compress_body(body)
            clen = len(compressed_body)
            path, sha256 = s3wrap.write_string_to_s3('productsum-spider',
                                                     compressed_body)
            do_extract_urls(link_id, canonical_url, body)
    db.link_update_results(link_id, httpcode, olen, clen,
                           sha256, canonical_url, mimetype)


def spider_one_link(site_id):
    try:
        nex = db.url_fetch_next(site_id)
        if nex:
            link_id, url = nex
            print link_id, url
            if link_id:
                url, results = url_fetch(url)
                save_url_results(link_id, url, time.time(), results)
    except Exception as e:
        traceback.print_exc()
        db.reconnect()


def spider_all_the_links(site_id):
    keepgoing = True
    try:
        while keepgoing:
            spider_one_link(site_id)
            time.sleep(5 + abs(int(random.gauss(1, 3))))
    except KeyboardInterrupt:
        print 'KeyboardInterrupt...'
        keepgoing = False


def run(site_id):
    db.init()
    spider_all_the_links(site_id)
    db.shutdown()


if __name__ == '__main__':
    import sys
    site_id = 1005
    if len(sys.argv) > 1:
        site_id = sys.argv[1]
    print 'site_id:', site_id
    run(site_id)

