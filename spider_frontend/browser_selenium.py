# ex: set ts=4 et:

from contextlib import contextmanager
from pyvirtualdisplay import Display
import os
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.webdriver.support.ui import WebDriverWait
import time

# functions.waitForAngular
# ref: https://github.com/angular/protractor/blob/c94f678cfbe142dcb88ef13610d850d60b5e1ccc/lib/clientsidescripts.js

def has_angular(browser):
    # Boolean(document.querySelector('[ng-app]'))
    try:
        print 'has_angular?'
        wait = WebDriverWait(browser, 2, poll_frequency=1)
        wait.until(lambda browser: browser.execute_script('return typeof window.angular !== "undefined"'))
        return True
    except TimeoutException:
        return False

def wait_for_angular(browser, seconds=5):
    if not has_angular(browser):
        print 'no angular...'
        return
    print 'waiting for angular...'
    browser.execute_script('''
angular.element(document).ready(function () {
    document.getElementsByTagName('body')[0].setAttribute('data-productsum-angular', 'loaded');
    console.log('angular document ready');
});''')
    try:
        wait = WebDriverWait(browser, seconds)
        wait.until(EC.presence_of_element_located((By.XPATH, '//body[@data-productsum-angular="loaded"]')))
    except TimeoutException:
        print 'Loading took too much time!'
        raise
    #browser.implicitly_wait(1)

_VirtDisplay = None
_Browser = None

def get_display():
    global _VirtDisplay
    if not _VirtDisplay:
        _VirtDisplay = Display(visible=0, size=(1024, 768))
        _VirtDisplay.start()
    return _VirtDisplay

def get_browser_firefox_invisible():
    # works on ubuntu! yay!
    display = get_display()
    browser = webdriver.Firefox()
    return browser

_Chrome_Cachedir = '/tmp/chromecache/'
_Chrome_Cachesize = str(64*1024*1024)

def get_chrome_options():
    try:
        os.mkdir(_Chrome_Cachedir)
    except Exception as e:
        print e
    # ref: http://stackoverflow.com/questions/15165593/set-chrome-prefs-with-python-binding-for-selenium-in-chromedriver
    # ref: http://peter.sh/experiments/chromium-command-line-switches/
    options = webdriver.ChromeOptions()
    #options.add_argument('--allow-running-insecure-content')
    #options.add_argument('--disable-web-security')

    # persist/share disk cache across runs and instances to reduce downloads/speed things up
    options.add_argument('--disk-cache-dir=' + _Chrome_Cachedir)
    options.add_argument('--disk-cache-size=' + _Chrome_Cachesize)

    #options.add_argument('--no-referrers')
    #options.add_argument('--window-size=1003,719')
    #options.add_argument('--proxy-server=localhost:8118')
    #options.add_argument("'chrome.prefs': {'profile.managed_default_content_settings.images': 2}")
    return options

def get_browser_chrome():
    display = get_display()
    # runs on ubuntu but doesn't work...
    #display = Display(visible=0, size=(1024, 768))
    #display.start()
    chromedriver = '/usr/lib/chromium-browser/chromedriver'
    os.environ['webdriver.chrome.driver'] = chromedriver
    options = get_chrome_options()
    browser = webdriver.Chrome(chromedriver,
                               chrome_options=options)
    return browser

def get_browser():
    global _Browser
    print 'get_browser...'
    if not _Browser:
        #_Browser = get_browser_firefox_invisible()
        _Browser = get_browser_chrome()
    return _Browser

def kill_browser():
    global _Browser
    try:
        _Browser.quit()
    except Exception as e:
        print e
    _Browser = None

def init():
    print 'browser_selection.init start...'
    x = get_display()
    print 'browser_selection.init done'
    return x

def shutdown():
    print 'browser_selection.shutdown start...'
    try:
        _Browser.quit()
    except:
        pass
    try:
        _VirtDisplay.stop()
    except:
        pass
    try:
        _VirtDisplay.popen.kill() # prevent zombie
    except:
        pass
    print 'browser_selection.shutdown done'


'''
# runs on ubuntu but doesn't work...
display = Display(visible=0, size=(1024, 768))
display.start()
chromedriver = '/usr/lib/chromium-browser/chromedriver'
os.environ['webdriver.chrome.driver'] = chromedriver
browser = webdriver.Chrome(chromedriver)
'''

# amazing-concealer-flawless-face-kit

'''
# does not work on ubuntu...
display = Display(visible=0, size=(1024, 768))
display.start()
os.environ['PATH'] += ':/usr/lib/chromium-browser'
browser = webdriver.Chrome()
'''

'''
# works on ubuntu... but doesn't load angular right...
browser = webdriver.PhantomJS()
'''

# doesn't work...
#os.environ['SELENIUM_SERVER_JAR'] = './selenium-server-standalone-2.48.2.jar'
#browser = webdriver.Safari()

#browser.set_window_size(1024, 768)

@contextmanager
def wait_for_page_to_load(browser, timeout=30):
    old_page = browser.find_element_by_tag_name('html')
    yield
    print 'waiting for new page...'
    WebDriverWait(browser, timeout).until(staleness_of(old_page))
    wait_for_angular(browser)


def url_fetch(url, timeout=30):
    browser = get_browser()
    page_source = None
    try:
        browser.set_page_load_timeout(timeout)
        with wait_for_page_to_load(browser, timeout=timeout):
            print 'getting %s' % url.encode('utf8')
            browser.get(url)
            page_source = unicode(browser.page_source).encode('utf8')
    except Exception as e:
        print e
        kill_browser()
    return page_source


if __name__ == '__main__':
    t = time.time()
    try:
        init()
        page_source = url_fetch('http://www.sephora.com/foundation-kits-sets')
        print len(page_source)
        print (page_source or u'')[:1024]
        print time.time() - t

        page_source = url_fetch('http://www.sephora.com/nail-polish-nail-lacquer')
        print time.time() - t

    except Exception as e:
        print e
    finally:
        shutdown()
    print time.time() - t

    '''
#browser.execute_script('scroll(0, 9999);');
#browser.implicitly_wait(2)

#browser.find_element_by_id('search_form_input_homepage').send_keys('realpython')
#browser.find_element_by_id('search_button_homepage').click()

print browser.current_url
#links = browser.find_elements_by_class_name('a') # WRONG
#links = browser.find_element_by_css_selector('a[href]')
#links = browser.find_element_by_xpath('//a')#/@href')

# iterating DOM nodes in selenium is absurdly slow...
# do it in javascript instead...
#links = set(browser.execute_script('return Array.from(document.querySelectorAll("a[href]")).map(function(a){ return a.getAttribute("href"); })'))
# phantomjs needs something different...
links = set(browser.execute_script('return [].slice.call(document.querySelectorAll("a[href]")).map(function(a){ return a.getAttribute("href"); })'))
print len(links)
print sorted(links)

#contents = 
# browser.page_source

#print browser.get_log('browser')

    '''
