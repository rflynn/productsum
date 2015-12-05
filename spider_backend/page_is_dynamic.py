# ex: set ts=4 et:

'''
static detection of definitive dynamic javascript pages
'''

from BeautifulSoup import BeautifulSoup


def page_has_angularjs(soup):
    # ref: https://angularjs.org/
    # NOTE: this is not 100% definitive, as it is *possible* to use angular without ng-*
    return soup.find(lambda tag: any(k.startswith('ng-')
                            for k, _ in tag.attrs)) is not None
    #return bool(soup.find(True, {'ng-app': True}))


def page_has_reactjs(soup):
    # ref: https://facebook.github.io/react/
    # impossible to determine definitively statically... so return None instead of False
    return (soup.find(lambda tag: any(k == 'data-reactid'
                        for k, _ in tag.attrs)) is not None) or None

def page_has_handlebars(soup):
    # client-side templating library
    # ref: http://handlebarsjs.com/
    return soup.find(
        'script',
            {'type': lambda t: t in ('text/x-handlebars',
                                     'text/x-handlebars-template')}
        ) is not None

