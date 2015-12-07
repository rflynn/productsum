# ex: set ts=4 et:

from BeautifulSoup import BeautifulSoup
from pprint import pprint


class HTMLMetadata(object):
    @staticmethod
    def do_html_metadata(soup):
        html = soup.find('html')
        lang = None
        if html:
            lang = html.get('lang') or html.get('xml:lang')
        charset = soup.find('meta', charset=True)
        if charset:
            charset = charset.get('charset')
        title = soup.find('title')
        if title:
            title = title.text
        keywords = soup.find('meta', {'name': 'keywords'})
        if keywords:
            keywords = dict(keywords.attrs).get('content')
        description = soup.find('meta', {'name': 'description'})
        if description:
            description = dict(description.attrs).get('content')
        attrs = {
            'lang': lang,
            'charset': charset,
            'title': title,
            'keywords': keywords,
            'description': description
        }
        #pprint(attrs)
        return attrs

