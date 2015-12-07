# ex: set ts=4:

from BeautifulSoup import BeautifulSoup, SoupStrainer
import re
from urlparse import urljoin
from yurl import URL


def url_abs(soup, page_url, base_url, url):
    return urljoin(base_url or page_url, url)


def a_to_url(soup, page_url, base_url, a):
    assert page_url or base_url
    if not a:
        return None
    href = a.get('href')
    if not href:
        return None
    href = href.strip()
    if href.startswith('#'):
        return None # anchor only, fuck it...
    u = url_abs(soup, page_url, base_url, href)
    # whitelist the stuff we care about...
    if u.startswith('http:') or u.startswith('https:'):
        return u
    # ...everything else is shit
    #print 'discarding %s' % (u,)
    return None


def url_looks_like_angular_nonsense(url):
    return bool(re.search('{{.*}}', url))

assert url_looks_like_angular_nonsense('http://www.sephora.com/{{sku.productSearchUrl}}') == True


def canonicalize_url(url):
    '''
    www.fwrd.com contains:
    <base href="http://www.fwrd.com:80/fw/" />
    '''
    u = URL(url)
    # strip default ports
    if u.scheme == 'http' and u.port == '80':
        u = u.replace(port='')
    elif u.scheme == 'https' and u.port == '443':
        u = u.replace(port='')
    # strip non-hashbang anchors
    if u.fragment and not u.fragment.startswith('!'):
        u = u.replace(fragment='')
    return str(u)

assert canonicalize_url('http://www.fwrd.com:80/fw/') == 'http://www.fwrd.com/fw/'
assert canonicalize_url('http://foo.com/#anchor_stripped') == 'http://foo.com/'
assert canonicalize_url('http://foo.com/#!hashbang_preserved') == 'http://foo.com/#!hashbang_preserved'

_NonHTMLExts = {
    '.avi',
    '.bmp',
    '.css',
    '.flv',
    '.doc',
    '.docx',
    '.exe',
    '.gif',
    '.ico',
    '.jpeg',
    '.jpg',
    '.js',
    '.m4a',
    '.mp3',
    '.mp4',
    '.mpg',
    '.otf',
    '.pdf',
    '.png',
    '.ppt',
    '.swf',
    '.tif',
    '.tiff',
    '.ttf',
    '.txt',
    '.wav',
    '.xls',
    '.xlsx',
    '.xml',
    '.zip',
}

def might_be_html(url):
    # FIXME: it would be better to either HEAD the files
    # and go by mimetype, or to async download and check then,
    # but this is a crappy shortcut to avoiding as much garbage as possible :-/
    low = url.lower()
    return not any(low.endswith(ext) for ext in _NonHTMLExts)

def from_url_results(url, body):
    '''
    links = {tag.get('href') for tag in BeautifulSoup(body,
                                    parseOnlyThese=SoupStrainer('a'))}
    '''
    soup = BeautifulSoup(body)
    base = soup.find('base')  # soup base lol
    base_url = canonicalize_url(base.get('href', url) if base else url)
    links = {a_to_url(soup, url, base_url, a)
                for a in soup.findAll('a', href=True)}
    return [l for l in links
                if l and len(l) < 2048 and might_be_html(l)]


assert from_url_results('http://foo.com/', u'') == []
assert from_url_results('http://foo.com/', u'<html><body><a href="a"></a>') == [u'http://foo.com/a']
assert from_url_results('http://foo.com/',
                        u'<html><base href="http://bar.com/"></base><body><a href="/a"></a>') == [u'http://bar.com/a']
assert from_url_results('http://foo.com/',
                        u'<html><body><a href="a"></a><a href="b"></a>') == [u'http://foo.com/a', u'http://foo.com/b']
assert from_url_results('http://x.com/', u'<html><body><a href="mailto:"></a>') == []
assert from_url_results('http://x.com/', u'<html><body><a href="//y.com/"></a>') == [u'http://y.com/']

