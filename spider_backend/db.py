# ex: set ts=4 et:

from collections import defaultdict
import pickle
import psycopg2
import psycopg2.extensions
from yurl import URL
from domain import domain_to_canonical
import traceback


dbhost = 'productsum-urlmetadata.ccon1imhl6ui.us-east-1.rds.amazonaws.com'
dbname = 'urlmetadata'
dbuser = 'root'
dbpass = '8VtsDPYHkcSQJ9'

# echo 8VtsDPYHkcSQJ9 | psql -h productsum-urlmetadata.ccon1imhl6ui.us-east-1.rds.amazonaws.com -p 5432 -U root -W urlmetadata
# SELECT EXTRACT(EPOCH FROM TIMESTAMP WITH TIME ZONE '2001-02-16 20:38:40.12-08');

# ref: http://initd.org/psycopg/docs/usage.html#unicode-handling
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

conn = None

def reconnect():
    print 'reconnect...'
    global conn
    try:
        if conn:
            conn.close()
            conn = None
        conn = psycopg2.connect("host='%s' user='%s' password='%s' dbname='%s'" % (
            (dbhost, dbuser, dbpass, dbname)))
        conn.set_client_encoding('utf8')
        print conn
    except Exception as e:
        conn = None
        print e
        raise e

reconnect()


def urlcache_init():
    print 'urlcache_init...'
    return defaultdict(dict)
    '''
    try:
        with open('./cache/url/urlcache.pickle', 'rb') as f:
            return pickle.load(f)
    except:
        return defaultdict(dict)
    '''

URLCache = None

def urlcache_get(urlobj):
    #print 'urlcache_get(%s)' % (urlobj,)
    return URLCache[urlobj.host].get(str(urlobj))

def urlcache_set(urlobj, link_id):
    print 'urlcache_set(%s, %s)' % (urlobj, link_id)
    global URLCache
    URLCache[urlobj.host][str(urlobj)] = link_id

def urlcache_save():
    pass
    '''
    print 'urlcache_save...'
    with open('./cache/url/urlcache.pickle', 'wb') as f:
        pickle.dump(URLCache, f)
    '''

def init():
    global URLCache
    URLCache = urlcache_init()

def shutdown():
    urlcache_save()


def url_fetch_next(site_id):
    try:
        cur = conn.cursor()
        cur.execute('''
select link_id, link_next
from link_fetch_next_site(%s);
''',
            (site_id,))
        conn.commit() # WTF needed for update within user defined function...
        row = cur.fetchone()
        print row
        link_id, url = row
        cur.close()
        return link_id, url
    except:
        traceback.print_exc()
        raise


def get_url_id(u):
    link_id = urlcache_get(u)
    if link_id:
        return link_id
    cur = conn.cursor()
    cur.execute('''
select id
from link
where host_id = (select id from host where name=%s)
and url_scheme = %s
and url_path = %s
and url_query = %s
''', (u.host, u.scheme, u.path, u.query or u''))
    row = cur.fetchone()
    if row:
        link_id, = cur.fetchone()
    cur.close()
    urlcache_set(u, link_id)
    return link_id


# TODO: move this shit to stored procedures


DomainCache = {}

def get_domain_id(host):
    domain = domain_to_canonical(host)
    if domain in DomainCache:
        return DomainCache[domain]
    cur = conn.cursor()
    cur.execute('select id from domain where name=%s', (domain,))
    row = cur.fetchone()
    if row:
        domain_id, = row
    else:
        cur.execute('insert into domain (name) values (%s)', (domain,))
        conn.commit()
        cur.execute('select lastval()')
        domain_id, = cur.fetchone()
    cur.close()
    if domain_id:
        DomainCache[domain] = domain_id
    return domain_id

HostCache = {}

def get_host_id(host):
    if host in HostCache:
        return HostCache[host]
    cur = conn.cursor()
    cur.execute('select id from host where name=%s', (host,))
    row = cur.fetchone()
    if row:
        host_id, = row
    else:
        domain_id = get_domain_id(host)
        cur.execute('insert into host (domain_id, name) values (%s, %s)',
            (domain_id, host))
        conn.commit()
        cur.execute('select lastval()')
        host_id, = cur.fetchone()
    cur.close()
    if host_id:
        HostCache[host] = host_id
    return host_id


def insert_url(orig_link_id, u):
    link_id = urlcache_get(u)
    if link_id:
        return link_id
    cur = conn.cursor()
    try:
        cur.execute('''
insert into link (
    datetime_created,
    site_id,
    host_id,
    url_scheme,
    url_userinfo,
    url_port,
    url_path,
    url_query,
    url_fragment
) values (
    now(),
    (select site_id from link where id=%(orig_link_id)s),
    %(host_id)s,
    %(scheme)s,
    %(userinfo)s,
    %(port)s,
    %(path)s,
    %(query)s,
    %(fragment)s
)
''',
        {
        'orig_link_id': orig_link_id,
        'host_id': get_host_id(u.host),
        # postgresql distinct doesn't work on NULLs...
        'scheme': u.scheme or u'',
        'userinfo': u.userinfo or u'',
        'port': u.port or u'',
        'path': u.path or u'',
        'query': u'?' + u.query if u.query else u'',
        'fragment': u'#' + u.fragment if u.fragment else u'',
        })
    except (psycopg2.DataError, psycopg2.IntegrityError):
        conn.rollback()
        return None
    conn.commit()
    cur.execute('select lastval()')
    link_id, = cur.fetchone()
    # link original link to the new one...
    cur.execute('update link set fetch_canonical_id = %s where id = %s', (link_id, orig_link_id,))
    conn.commit()
    cur.close()
    urlcache_set(u, link_id)
    return link_id


def get_canonical_url_id(link_id, canonical_url):
    if not canonical_url:
        return None
    # break url into parts
    u = URL(canonical_url)
    # check for existence
    # if not, create and return id...
    return None


def link_update_results(link_id, httpcode, olen, clen, sha256,
                        canonical_url, mimetype):
    canonical_url_id = get_canonical_url_id(link_id, canonical_url)
    cur = conn.cursor()
    cur.execute('''
update link
set
    datetime_enqueued = null,
    datetime_updated = now(),
    datetime_last_ok = case %s when 200 then now() else datetime_last_ok end,
    fetch_canonical_id = %s,
    fetch_code = %s,
    fetch_origbytes = %s,
    fetch_savebytes = %s,
    fetch_mimetype = %s,
    fetch_sha256 = %s
where id = %s
''', (httpcode,
      canonical_url_id,
      httpcode,
      olen,
      clen,
      mimetype,
      bytearray(sha256) if sha256 else None,
      link_id,))
    conn.commit() # WTF needed for update within user defined function...
    cur.close()

