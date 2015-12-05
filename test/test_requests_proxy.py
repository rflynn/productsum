
import requests
from pprint import pprint


resp = requests.get('http://www.google.com/',
            timeout=3,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36',
            },
            proxies={
                'http': '104.131.215.237:8888',
                'https': '104.131.215.237:8888',
            },
            verify=False)
print resp.status_code
pprint(resp.headers)
print resp.text[:1024]

