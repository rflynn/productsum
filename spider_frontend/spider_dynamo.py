# vim: set ts=4 et:

from BeautifulSoup import BeautifulSoup
from datetime import datetime
from orderedset import OrderedSet
import random
import re
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from time import sleep
import traceback
from urlparse import urljoin
from yurl import URL

from spider_backend import db_dynamo as db, s3wrap, page_links
from spider_frontend import ua, browser_selenium


requests.packages.urllib3.disable_warnings(InsecureRequestWarning) # annoying


_Seeds = {
    #'http://www.abercrombie.com/shop/us': {'ok':{'/shop/us/'}},
    'http://www.6pm.com/': {
        'skip': {
            '/bin/',
            '/multiview/',
            '/product/review/add/',
            '/cart',
            '/login',
            '/logout',
            '/register',
            '/account',
        },
    },
    'http://couture.zappos.com/': {},
    'https://shop.harpersbazaar.com/': {},
    'http://shop.mango.com/US': {
        'runjs': {},
        'ok': {
            '/catalog',
            '/US/',
        },
        'skip': {
            '/US/*/help',
            '/US/account',
            '/US/login',
            '/US/signup',
        },
    },
    'http://shop.nordstrom.com/': {},
    'http://us.christianlouboutin.com/us_en/': {'ok':{'/us_en/'}},
    'http://us.louisvuitton.com/eng-us/homepage': {'ok':{'/eng-us/'}},
    'http://us.topshop.com/en': {'ok':{'/en/'}},
    'http://www.alexandermcqueen.com/': {
        'skip': {
            # custom
            '/account/',
            '/checkout/',
            '/chooseyourcountry.asp',
            '/cms/',
            '/sitemap.asp',
            '/us/mcq',
            # robots.txt
            '/scripts/',
            '/teaser.asp*',
        },
    },
    'http://www.barneys.com/': {'skip':{'/on/'}},
    'http://www.bathandbodyworks.com/': {
        'skip': {
            '*jsessionid=',
            '/cart/',
            '/checkout/',
            '/emailFriend/',
            '/gcoreg/',
            '/helpdesk/',
            '/include/',
            '/largeImage/',
            '/prodEmailHandler/',
        }
    },
    'http://www.beauty.com/': {
        'skip': {
            '/4213/edh',
            '/500.htm',
            '/affiliate/content.asp',
            '/cart.asp',
            '/checkout/',
            '/checkout/default.asp',
            '/la/account/',
            '/la/order/',
            '/list.asp',
            '/LookAheadSuggestions.aspx',
            '/onorder.asp',
            '/popups/largerphoto/default.asp',
            '/pricing.asp',
            '/products/email_product.asp',
            '/products/writereview.asp',
            '/shoppingbag.asp',
            '/templates/events/circular.asp',
            '/templates/evgrndept/default.asp',
            '/templates/HIPAA/info.asp',
            '/templates/stdcat/default.asp',
            '/templates/stdplist/default.asp',
            '/user/',
        }
    },
    'http://www.beautybar.com/': {
        'needs-cookies': {},
        'skip': {
            '*%7C',
            '*%7c',
            '/about-us',
            '/buy/',
            '/helpcenter/',
            '/legal',
            '/login*',
            '/myaccount',
            '/shoppingcart',
        },
    },
    'http://www.beautylish.com/': {
        'skip': {
            '/about/',
            '/article/',
            '/articles/',
            '/bag/',
            '/f/',
            '/help/',
            '/jobs/',
            '/photos/',
            '/press/',
            '/review/',
            '/talk/',
            '/videos/',
        }
    },
    'http://www.belk.com/': {
        'skip': {
            # custom
            # robots.txt
            '/AST/Boutiques/',
            '/AST/Featured/Promo_Details/Ratings_and_Reviews.jsp',
            '/AST/Main/Belk_Primary/Sale_and_Clearance/',
            '/AST/Main/Wedding_Primary/',
            '/AST/Misc/Belk_Stores/Global_Navigation/',
            '/AST/Misc/Belk_Stores/My_Account/',
            '/AST/Misc/Belk_Stores/Shop_by_Brand.jsp',
            '/AST/Misc/Gift_Recommendations/',
            '/bridalregistry/bridal_search_results.jsp',
            '/myaccount/',
            '/ratingsandreviews',
            '/search/',
        },
    },
    'http://www.bergdorfgoodman.com/': {
        'skip': {
            '/account/',
            '/assistance/',
        }
    },
    'https://www.birchbox.com/': {
        'skip': {
            # all custom, their robots.txt is wide open
            '/about/',
            '/mobile/',
            '/stores/',
            '*/checkout/',
            '*/feedback/', # ignore extensive reviews
            '/subscribe/',
        }
    },
    'http://www.bluefly.com/': {
        'skip': {
            #'/*exclusives.fly',
            #'/browse/bfly/', #Google getting 500s
            #'/designers/list/', #Google getting 500s
            #'/newarrivals/', #Google getting 500s
            '/*/null', # Bad
            '/*/search.fly', # Bad Url
            '/*;jsessionid=*',
            '/*CROSS-SELL/', #color cross sells
            '/*CROSS_SELL/', #baynote cross sells
            '/*FEATURED_ITEMS/', #featured
            '/*SEARCH/',  #PDP from search results
            '/*jsessionid=*',
            '/Nrk-all/Nrr-all/Nrt-',
            '/Ntt-',
            '/addFavoriteProduct.jsp', # Bad
            '/browse/f_quick_buy.jsp',
            '/browse/pdpQuickAdd.jsp',
            '/browse/quickLogin.jsp',
            '/cart/',
            '/checkmyfly.jsp',
            '/favorites.jsp', # Bad Url
            '/invite/',
            '/media/templates/html/popups/',
            '/media/templates/html/sizecharts/',
            '/myaccount/',
            '/myfly/',
            '/pages/',
            '/removeFavoriteProduct.jsp', # Bad
            '/sl/',
        },
    },
    'http://www.bluemercury.com/': {
        'skip': {
            # custom
            '/CAREERS/',
            '/Marla/ProductSubmissions.htm',
            '/MemberLogin.aspx',
            '/Ordering-and-Payment',
            '/Returns-and-Exchanges',
            '/Shipping-Information',
            '/about.aspx',
            '/cart.aspx',
            '/contact.aspx',
            '/createAccount.aspx',
            '/policies.aspx',
            '/quick-view.aspx',
            '/wishlist-main.aspx',
            # robots.txt
            '/Samples',
            '/TrendingReports',
            '/backadmin',
            '/gwps/',
            '/productExports',
            '/samples/',
            '/testimonials',
        },
    },
    'http://www.brownsfashion.com/': {},
    'http://www.chanel.com/en_US/': {
        'ok': {
            '/en_US/',
        },
        'skip': {
            '/en_US/commerce',
            '/en_US/contact',
            '/en_US/faq',
            '/en_US/policies',
            '/en_US/storelocator',
        },
    },
    'http://www.clinique.com/': {
        'crawl-delay': 15,
        'skip': {
            # custom
            '/account/',
            '/checkout/',
            '/customer-care/',
            '/customer_service/',
            '/giftcards/',
            '/videos/',

            # robots.txt
            '/includes/',
            '/misc/',
            '/modules/',
            '/profiles/',
            '/scripts/',
            '/themes/',
            # Files
            '/CHANGELOG.txt',
            '/cron.php',
            '/INSTALL.mysql.txt',
            '/INSTALL.pgsql.txt',
            '/INSTALL.sqlite.txt',
            '/install.php',
            '/INSTALL.txt',
            '/LICENSE.txt',
            '/MAINTAINERS.txt',
            '/update.php',
            '/UPGRADE.txt',
            '/xmlrpc.php',
            # Paths (clean URLs)
            '/admin/',
            '/comment/reply/',
            '/filter/tips/',
            '/node/add/',
            '/search/',
            '/user/register/',
            '/user/password/',
            '/user/login/',
            '/user/logout/',
            '/account/',
            '/checkout/',
            '/templates/',
            '/includes/',
            # Paths (no clean URLs)
            '/?q=admin/',
            '/?q=comment/reply/',
            '/?q=filter/tips/',
            '/?q=node/add/',
            '/?q=search/',
            '/?q=user/password/',
            '/?q=user/register/',
            '/?q=user/login/',
            '/?q=user/logout/',
            '/shared/',
            '*.xml',
        },
    },
    'http://www.cvs.com/': {
        #'ok': {
        #    '/',
        #    '/shop/beauty/',
        #    '/shop/personal-care/',
        #    '/shop/skin-care/',
        #},
        'skip': {
            # custom
            '/help/',
            '*;jsessionid=',
            '/minuteclinic/',
            '*/clinics/',
            '/store-locator/',
            # robots.txt
            '/account/',
            '/bizontent/navarro/',
            '/checkout/',
            '/clinic-locator/cliniclocator-city.jsp?stateId=*',
            '/content/multidose',
            '/minuteclinic/clinic-locator/view-list.jsp?_requestid=*',
            '/minuteclinic/clinics/*/as$',
            '/minuteclinic/clinics/*/ib$',
            '/minuteclinic/search.jsp?q=*',
            '/mobile/',
            '/mobilelanding/',
            '/photo/cardspdp?category=*',
            '/photo/empty-shopping-cart',
            '/photo/error*',
            '/photo/library/',
            '/photo/offerdetails',
            '/photo/product-details?category=*',
            '/search/',
            '/shop/popups',
            '/store-locator/details-directions/*',
            '/stores/add-favorite-popup.jsp',
        },
    },
    'http://www.cusp.com/': {},
    'http://www.dermstore.com/': {
        'skip': {
            '*/account/*',
            '*/ajax/*',
            '*/cart/*',
            '*/cart/flip.php*',
            '*/content/*',
            '*/giftcard/*',
            '*/helpers/*',
            '*/list.php?*',
            '*/list_*-*.htm',
            '*/list_*clearance.htm',
            '*/list_*more*.htm',
            '*/list_*review.htm',
            '*/list_*shoppers.htm',
            '*/long_*',
            '*/prod_finder_widget.php*',
            '*/question_list*',
            '*/search_facetted.php?*',
            '*/searchsite.php?*',
            '/*source=igodigital*',
            '/reviews/',
        },
    },
    'http://www.dillards.com/': {
        'runjs': {},
        'skip': {
            '/c/',
            '/credit-services/',
            '/html/',
            '/shop/en/dillards/faqs-notices-policies-us',
            '/webapp/wcs/stores/servlet/OrderItemDisplay', # cart
            '/webapp/wcs/stores/servlet/LogonForm',
        },
    },
    'http://www.drugstore.com': {
        'skip': {
            # my app-specific, might change in the future
            '/household-food-and-pets/',
            '/medicine-and-health/',
            '/walgreens-pharmacy/',
            '/personal-care/',
            '/your-list/', # requires login
            # their robots.txt
            '/4213/edh',
            '/500.htm',
            '/affiliate/content.asp',
            '/cart.asp',
            '/checkout/',
            '/checkout/default.asp',
            '/la/account/',
            '/la/order/',
            '/list.asp',
            '/LookAheadSuggestions.aspx',
            '/onorder.asp',
            '/popups/largerphoto/default.asp',
            '/pricing.asp',
            '/products/email_product.asp',
            '/products/writereview.asp',
            '/reorders/',
            '/shoppingbag.asp',
            '/templates/events/circular.asp',
            '/templates/evgrndept/default.asp',
            '/templates/HIPAA/info.asp',
            '/templates/stdcat/default.asp',
            '/templates/stdplist/default.asp',
            '/user/',
        }
    },
    'http://www.dsw.com/': {
        'skip': {
            '/Boot-Shop-',
            '/Boots',
            '/boots/',
            '/dsw_shoes/',
            '/emi/',
            '/sandals/',
            '/shoe/joseph+abboud+collection+robert+oxford',
            '/wl/',
        }
    },
    'http://www.farfetch.com/': {
        'skip': {
            '/Account/',
            '/Custom/flash/',
            '/FFTEST/',
            '/fftest/',
            '/forum/',
            '/tag/',
            '/useraccount.aspx',
        },
    },
    'http://www.footcandyshoes.com/': {},
    'http://www.fwrd.com/': {
        'skip': {
            '/blog/',
            '/fw/',
            '/fwd/',
            '/r/',
            '/Unsubscribe.jsp',
        }
    },
    'http://www.gilt.com/': {},
    'http://www.gojane.com/': {},
    'http://www.harrods.com/': {
        'skip': {
            # custom
            '/contact-us/',
            '/content/',
            '/gift-cards/',
            '/instore-designers',
            '/login',
            '/register',
            '/user/',
            '/visiting-the-store',
            # robots.txt
            '/App_Browsers/',
            '/App_Code/',
            '/App_Data/',
            '/App_GlobalResources/',
            '/App_LocalResources/',
            '/CSS/',
            '/Cart.aspx',
            '/Controls/',
            '/Email/',
            '/Flash/',
            '/GlobalPages/',
            '/HarrodsStore/GlobalPages/',
            '/HarrodsStore/Weddings/Default.aspx',
            '/HarrodsStore/globalpages/Restaurants.aspx',
            '/Images/',
            '/JavaScript/',
            '/Layouts/',
            '/Minify/',
            '/Profile/',
            '/Public/',
            '/SiteError.htm',
            '/UIServices/',
            '/User/',
            '/User/getARewardsCard.aspx',
            '/Weddings/Services/Services.aspx?Id=AAC9EBDE-68B7-48d4-9B21-EF32D0F107B4',
            '/akamai/',
            '/bin/',
            '/browser_test.htm',
            '/globalpages/contentpage.aspx?id=bf12b1ef-2533-4460-a989-c13f26cb7bbc',
            '/new_css/',
            '/new_images/',
            '/pipelines/',
            '/shoppingbag/',
            '/templates/',
            '/version.aspx',
        },
    },
    'http://www.jcpenney.com/': {
        'skip': {
            # custom
            '/dotcom/jsp/cart/',
            '/jsp/browse/',
            '/jsp/checkout/',
            '/jsp/customerservice/',
            '/Customers/',:
            # robots.txt
            '/products/',
            '/jsp/search',
            '/jsp/browse/pp/print/',
            '/jsp/profile/',
        },
    },
    'https://www.jcrew.com/': {
        'runjs': {},
        'skip': {
            # custom
            '/aboutus/',
            '/account/',
            '/checkout2/',
            '/flatpages/',
            '/footer/',
            '/footie/',
            '/help/',
            '/intl/',
            '/signin/',
            '/wishlist',
            # robots.txt
            '/AST/filterAsst/',
            '/account/',
            '/api/',
            '/c/',
            '/checkout/',
            '/clienterror/',
            '/data/',
            '/embed/',
            '/feature-page/',
            '/help/include/inc_storelocator_right.jsp',
            '/index2.jsp',
            '/login/',
            '/p/',
            '/r/',
            '/register/',
            '/s/',
            '/size-charts/',
            '/sizecharts-module/',
            '/static/',
            '/v/',
            '/web-tracking/',
        },
    },
    'http://www.josephstores.com/': {},
    'http://us.jimmychoo.com/': {
        'needs-cookies': {},
        'ok': {
            '/en/',
            '/on/',
        },
        'skip': {
            '/*/Account-*',
            '/*/Cart-*',
            '/*/add-wishlist',
            '/*/customer-services/',
            '/*/store-locator/',
        },
    },
    'https://www.katespade.com/': {
        'skip': {
            # custom
            '/customer-care/',
            '/gift-cards-1/',
            '/gwp/',
            '/katespade-about-us/',
            '/katespade-careers',
            '/katespade-customer-service-shipping/',
            '/katespade-customer-service-privacy-security/',
            '/shopping-bag',
            '/stores',
            # robots.txt
            '*/Employee-BrandCloset/*',
            '*/Employee-EStockRoom/*',
            '*/CSSuite-Home/*',
            '*/Account-Show/*',
            '*/Account-StartRegister/*',
            '*/Wishlist-Show/*',
            '*/COShippingMultiple-StartShipments/*',
            '*/Cart-Show/*',
            '*/demandware.store/*',
        },
    },
    'http://www.lancome-usa.com/': {
        'skip': {
            # custom
            '/on/demandware.store/Sites-lancome_us-Site/default/Stores-Find',
            '/on/demandware.store/Sites-lancome_us-Site/default/CustomerService-ContactUsRealDialog',
            '*Wishlist-Add',
            # robots.txt
            '/on/demandware.store/Sites-lancome_us-Site/default/Account-Show',
            '/on/demandware.store/Sites-lancome_us-Site/default/Cart-Show',
        },
    },
    'http://www.ln-cc.com/': {
        'skip': {
            # custom
            '/*Cart-Show',
            '/*storelocator',
            '/*/feed/',
            # robots.txt
            '/*CountryGateway-SwitchLocale*',
            '/*prefn1*',
            '/*prefv1*',
            '/*SendToFriend-Start?pid*',
            '/*SendToFriend-Start?source*',
            '/*send-to-friend?pid*',
            '/*send-to-friend?source*',
            '/*Search-Show?q*',
            '/*risultati-ricerca?q*',
            '/*resulats-recherche?q*',
            '/*resultados-busqueda?q*',
            '/*suchergebnisse?q*',
            '/*search-results?q*',
            '/*Product-Variation?*',
            '/*srule=*',
        },
    },
    'http://www.lordandtaylor.com/': {
        'skip': {
            '/common/',
            '/eng/',
            '/extra/',
            '/fre/',
            '/frontEndComponents/',
            '/maint',
            '/sharedPages/',
            '/webapp/wcs/stores/servlet/AjaxCatalogSearchResultView',
            '/webapp/wcs/stores/servlet/AjaxChanelCatalogSearchResultView',
            '/webapp/wcs/stores/servlet/AjaxOrderItemDisplayView',
            '/webapp/wcs/stores/servlet/SearchDisplay',
            '/webapp/wcs/stores/servlet/logonform',
            '/webapp/wcs/stores/servlet/ProductDisplay',
            '/webapp/wcs/stores/servlet/QuickInfoDetailsView',
            '/webapp/wcs/stores/servlet/NavSearchDisplay',
            '/webapp/wcs/stores/servlet/OrderShippingBillingView',
            '/webapp/wcs/stores/servlet/en/thebay',
            '/webapp/wcs/stores/servlet/fr/thebay',
        }
    },
    'http://www.luisaviaroma.com/': {
        'runjs': {},
    },
    'http://madisonlosangeles.com/': {},
    'http://www.matchesfashion.com/': {
        'skip': {
            # custom
            '/us/settings*',
            # robots.txt
            '*/addtowaitlist/*',
            '*/sendfriend/*',
            '*?q=*',
            '*?signup*',
            '*?text=*',
            '*filter=*',
            '*orderby=*',
            '*pagesize=*',
            '/account/*',
            '/affiliate/',
            '/barcode/',
            '/bin/',
            '/checkout/',
            '/employee/',
            '/preview/',
            '/search*',
            '/settings*',
            '/shopping-bag*',
            '/system/',
        }
    },
    'http://www.maybelline.com': {
        'skip': {
            # custom
            '/Makeup-Videos/',
            '/shopping-bags.aspx',
            # robots.txt
            '/Layers/',
            '/Maybelline/',
            '/MaybellineV2/',
            '/user/',
            '/members/',
        },
    },
    'http://www.michaelkors.com/': {
        'runjs': {},
        'skip': {
            # custom
            '/browse/common/',
            '/checkout/',
            '/stores/',
            # robots.txt
            '/myaccount/',
        },
    },
    'http://www.mytheresa.com/': {
        'skip': {
            # endless filter combinations...
            '*?*designer=*%7C',
            '*?*size_harmonized=*%7C',
            '*?*main_colors=*%7C',
            '*?*color_pattern=*%7C',
            '*/customer/',
            '/de-de/',
            '*/giftcard/',
            '*/mzcatalog/',
            '*/mywishlist/',
        },
    },
    'http://www.nastygal.com/': {
        'skip': {
            # custom
            '/account/',
            '/careers',
            '/crushes',
            '/customer-care/',
            '/gift-card/',
            '/localization',
            '/privacy-policy/',
            '/orders/',
            '/stores/',
            '/terms-of-use/',
            '/tote',
            # robots.txt
            '/Expletive-Ring-Set',
            '/localization',
            '/account/',
            '/orders',
            '/closet',
            '/tote',
            '/checkout',
            '/waitlist/',
            '/search?',
        },
    },
    'http://www.neimanmarcus.com/': {
        'skip': {
            '/account/',
            '/assistance/',
            '/checkout/',
            '/service/',
            '/stores/',
        }
    },
    'http://www.net-a-porter.com/': {
        'skip': {
            '/*viewall',
            '/*sortBy',
            '/*image_view',
            '/*designerFilter',
            '/*colourFilter',
            '/*sizeFilter',
            '/Shop/Featured-Products/',
            '/Shop/Lost/',
            '/Shop/Search/',
            '/am/pssizechart.nap',
        },
    },
    'http://www.nyxcosmetics.com/': {
        'skip': {
            '/careers.html',
            '/customer-service-privacy-policy.html',
            '/faqs.html',
            '/events.html',
            '/on/demandware.store/',
            '/shipping-returns.html',
            '/termsandconditions.html',
        },
    },
    'http://www.ralphlauren.com/': {
        'runjs': {},
        'skip': {
            # custom
            '/helpdesk/',
            # robots.txt
            '/cart/',
            '/cartHandler/',
            '/checkout/',
            '/coreg/',
            '/employee/',
            '/include/',
            '/product/index.jsp?productId=2894542',
            '/product/index.jsp?productId=3560608',
            '/search/',
        },
    },
    'http://www.revolveclothing.com/': {
        'skip': {
            '/r/ajax/crawlerDiscovery.jsp',
        },
    },
    'https://shop.riteaid.com/': {
        'skip': {
            # custom
            '/info/',
            # ignore everything but beauty and...
            '/baby-kids-mom/',
            '/diet-fitness/',
            '/electronics-office/',
            '/household/',
            '/medicine-health/',
            '/sexual-health/',
            '/vitamins-supplements/',
        },
    },
    'http://www.saksfifthavenue.com/': {
        # ref: http://www.saksfifthavenue.com/main/ProductDetail.jsp?PRODUCT<>prd_id=845524446904973
        #'favor': lambda url: bool(re.match('/main/ProductDetail.jsp[?]PRODUCT<>prd_id=\d+$', url.path)),
        'skip': {
            '/account/',
            '/main/bridal_landing.jsp',
            '/NoJavaScript.jsp',
            '/search/',
            '/stores/',
            '/trendcaster',
        }
    },
    'http://www.selfridges.com/US/en/': {
        'ok': {
            '/US/en/',
        },
        'skip': {
            # custom
            '/*CountrySelection',
            '/*MyAccount',
            '/*WishList',
            '/*OrderCalculate',
            '/*gift-card',
            # robots.txt
            '/webapp/wcs/stores/servlet/OrderItemAdd',
            '/webapp/wcs/stores/servlet/OrderItemDisplay',
            '/webapp/wcs/stores/servlet/OrderCalculate',
            '/webapp/wcs/stores/servlet/QuickOrderCmd',
            '/webapp/wcs/stores/servlet/InterestItemDisplay',
            '/webapp/wcs/stores/servlet/ProductDisplayLargeImageView',
            '/webapp/wcs/stores/servlet/FittingRoomApplicationView',
            '/webapp/wcs/stores/servlet/LogonForm',
            '*/content/brand-guidlines*',
            '*/wcsstore/Selfridges/upload/html5/brand-guidelines-email.html',
        },
    },
    'http://www.sephora.com/': {
        'runjs': {},
        'skip': {
            # custom
            '*_image',
            '/about/',
            '/customerService/',
            '/rewards',
            '/sephoratv/',
            '/stores/',
            # robots.txt
            '/basket/',
            '/checkout/',
            '/error/',
            '/lovelist/',
            '/profile/MyAccount/',
            '/profile/login/',
            '/profile/orders/',
            '/profile/purchaseHistory/',
            '/profile/popup/',
            '/profile/logout/',
            '/profile/forgotpassword/',
            '/profile/myBeautyBag/',
            '/profile/accountHistory/',
            '/profile/common/',
            '/profile/orderConfirmation/',
            '/profile/registration/',
            '/shopping-list/',
        }
    },
    'http://www.shiseido.com/': {
        'skip': {
            # custom
            '/Customer-Service/',
            '/on/demandware.store/Sites-Shiseido_US-Site/en_US/PowerReviews-WriteReviewPage',
            '/Privacy/',
            '/store-locator/',
            '/Site-Selector/',
            # robots.txt
            '/*prefn1',
            '/PowerReviews-WriteReviewPage/',
        },
    },
    'http://www.shoescribe.com/us/women': {'ok':{'/us/'}},
    'http://www.skinstore.com/': {
        'skip': {
            # custom
            '/myAccount/',
            '/serviceCenter/',
            # robots.txt
            '/Search/',
            '/acquisition/',
            '/admin/',
            '/assets/',
            '/checkout/',
            '/educationCenter/',
            '/expressShopper/',
            '/fav/',
            '/myaccount/',
            '/orderStatus/',
            '/orderstatus/',
            '/productArchive/',
            '/productarchive/',
            '/search/',
            '/servicecenter/askus.aspx',
            '/servicecenter/requestinformation.aspx',
            '/servicecenter/sitefeedback.aspx',
            '/store/',
            '/storefront/',
            '/uploadedFiles/',
            '/uploadedImages/',
            '/widgets/',
            '/workarea/',
        },
    },
    'http://www.stuartweitzman.com/home/default.aspx': {
        'runjs': {},
        'skip': {
            # custom
            '/?ChangeCountry=',
            '/careers/',
            '/home',
            '/my-account/',
            '/shopping-bag',
            '/service/',
            # robots.txt
            '/admin/',
            '/ckeditor/',
            '/fckeditor/',
            '/search/',
            '/search_results/',
        },
    },
    'http://www.stylebop.com/': {
        'skip': {
            # ignore other languages
            '/de/',
            '/fr/',
            '/jp/',
            # from robots.txt
            '/admin/',
            '/admin2/',
            '/app/',
            '/backup/',
            '/batch/',
            '/book/',
            '/book_new/',
            '/bt-trp.php',
            '/bt-trp/',
            '/cgi-bin/',
            '/changeCountry.php',
            '/checkout.php',
            '/data_muc/',
            '/data_nyc/',
            '/export/',
            '/feedback.php',
            '/findologic/',
            '/flash/',
            '/go2item.php',
            '/intern/',
            '/intern/',
            '/intro.php',
            '/keybroker_redirect.php',
            '/language/',
            '/login.php',
            '/mobile/',
            '/monitoring/',
            '/my.php',
            '/my_exchange.php',
            '/my_retour.php',
            '/my_wishlist.php',
            '/newsletter/',
            '/password.php',
            '/phpMyAdmin-20110829/',
            '/phpMyAdmin-stylktut/',
            '/phpMyAdmin-stylktut1/',
            '/presentation/',
            '/press/',
            '/redaktion/',
            '/register.php',
            '/retour.php',
            '/search/',
            '/search_findologic.php',
            '/server.php',
            '/shopconfig/',
            '/statistik/',
            '/templates/',
            '/thankyou2.php',
            '/translate/',
            '/video/',
            '/waitForOrder.php',
            '/webshopneu/',
            '/wishlist.php',
        }
    },
    'http://www.target.com/': {
        'ok': { # custom
            '/',
            '/c/beauty/',
            '/c/*beauty',
            '/c/*health',
            '/c/*clothing',
            '/c/*shoes',
            '/p/',
            '/sb/*beauty',
            '/sb/*health',
            '/sb/*clothing',
            '/sb/*shoes',
        },
        'skip': { # robots.txt
            '/Allons_voter*',
            '/admin*',
            '/AjaxSearchNavigationView',
            '/SearchNavigationView',
            '/CallToActionModalView*',
            '/cgi-bin*',
            '/cgi-local*',
            '/Checkout',
            '/CheckoutEditItemsDisplayView',
            '/CheckoutOrderBillingView',
            '/CheckoutOrderShippingView',
            '/CheckoutSignInView',
            '/common*',
            '/coupons.',
            '/data*',
            '/database/philboard.mdb',
            '/dir_on_server/*',
            '/ExitCheckoutCmd',
            '/EmailCartView',
            '/EnlargedImageView*',
            '/ESPDisplayOptionsViewCmd',
            '/FetchProdRefreshContent',
            '*Fafid*',
            '/FiatsCmd',
            '/fiats*',
            '/file*',
            '*force-full-site=1',
            '/FreeGiftDisplayView*',
            '/GenericRegistryPortalView',
            '/GiftRegistrySearchViewCmd*',
            '/guestEmailNotificationView',
            '/GuestAsAnonymous',
            '/gp/*',
            '/HelpContent*',
            '/index.jhtml',
            '/legal-contact-us/*',
            '/igp*',
            '/list.id=1',
            '/login.php',
            '/LogonForm',
            '/OpenZoomLayer*',
            '/ManageOrder',
            '/ManageReturns',
            '/MediaDisplayView',
            '/moreinfo.cfm*',
            '/news*',
            '/np/*',
            '/OrderItemDisplay',
            '/OpenZoomLayer*',
            '/PhotoUpload',
            '/ProductComparisonCmd',
            '/ProductDetailsTabView*',
            '/PromotionDisplayView',
            '/PromotionDetailsDisplayView',
            '/qi/',
            '/ready_sit_read/index.jhtml',
            '/RegistryPortalCmd',
            '/ReportAbuse',
            '/s?searchTerm=*',
            '/script*',
            '/search.php',
            '/shop/*',
            '/shell.php',
            '/SingleShipmentOrderSummaryView',
            '/SOImapPriceDisplayView*',
            '/splitOrderItem',
            '/store-locator/search-results-print*',
            '/supertarget/index.jhtml',
            '/target_baby/*',
            '/target_group*',
            '/target.php',
            '/targetdirect_group/*',
            '/TargetListPortalView',
            '/TargetStoreLocatorCmd',
            '/tdir/p/kids-back-to-school/*',
            '/tsa/*',
            '/WriteComments',
            '/WriteReviews',
            '/winnt/*',
            '/webapp',
            '/advancedGiftRegistrySearchView',
            '/SpecificationDefinitionView',
            '/VariationSelectionView',
            '/vuln.php*',
            '/FeaturedShowMoreOverlay',
            '/mm/*',
            '/mm/',
            '/p/premium-registry*',
        },
    },
    'https://www.therealreal.com': {
        'skip': {
            # custom
            '/about',
            '/authenticity',
            '/business-sellers',
            '/careers',
            '/consignments',
            '/contactus',
            '/first_look_subscriptions',
            '/returns',
            '/shipping',
            '/team',
            '/terms',
            # robots.txt
            '/cart',
            '/checkouts',
            '/orders',
            '/countries',
            '/login',
            '/line_items',
            '/password_resets',
            '/states',
            '/user_sessions',
            '/users',
        },
    },
    'http://www.toryburch.com/': {
        'skip': {
            # custom
            '/about-us/',
            '/account',
            '/blog/',
            '/ca-supply-chain-disclosure/',
            '/content-privacy/',
            '/giftcards/',
            '/global/',
            '/on/',
            '/stores/',
            # robots.txt
            '/Login-Show/',
            '/Customer-EditProfile/',
            '/Customer-AddressBookList/',
            '/PaymentInstruments-List/',
            '/Order-Track/',
            '/Wishlist-Show/',
            '/E?mai?lFr?ien?d-S?tar?t/',
            '/Search-*?',
            '/Sites-ToryBurch_CF-Site/',
            '/hidden-category/',
        },
    },
    'http://www.thecorner.com/us': {'ok':{'/us/'}},
    'http://www.snapdeal.com/': {
        'ok': {
            '/products/perfumes-beauty-cosmetics',
            '/products/make-up-eyes',
            '/products/make-up-face',
            '/products/make-up-nails',
            '/products/make-up-removers',
            '/products/makeup-tools-accessories',
            '/products/makeup-kits',
            # avoid other top-level directories, but follow individual product links
            '/products/*/*',
        },
        'skip': {
            # avoid anything other than individual products from the top-levels we want...
            '/products/*/*?',
        },
    },
    'http://www.ulta.com/': {
        'skip': {
            '*_dynSessConf=',
            '/browse/inc/addToFavorites.jsp',
            '/browse/inc/productDetail_crossSell.jsp',
            '/careers-at-ulta/', # useless
            '/image-server/',
            '/ulta/a/Nails-ULTA-Collection/_/N-*?categoryId=cat350015&ciSelector=leaf/', # endless permutations of search results
            '/ulta/cart/',
            '/ulta/checkout/',
            '/ulta/common/productRecommendations.jsp',
            '/ulta/common/recommendedProduct.jsp',
            '/ulta/external/',
            '/ulta/integrations/',
            '/ulta/myaccount/addressbook.jsp',
            '/ulta/myaccount/learnmore_template.jsp',
            '/ulta/myaccount/login.jsp',
            '/ulta/myaccount/order.jsp',
            '/ulta/myaccount/pages/order_status_anonymous.jsp',
            '/ulta/myaccount/preferences.jsp',
            '/ulta/myaccount/register.jsp',
            '/ulta/myaccount/reset_password.jsp',
            '/ulta/myaccount/rewards.jsp',
            '/ulta/myaccount/rewards_template.jsp',
            '/ulta/myaccount/template.jsp',
            '/ulta/reminder/',
        }
    },
    'http://us.christianlouboutin.com/us_en/': {
        'ok': {
            '/us_en/',
        },
        'skip': {
            # custom
            '/us_en/checkout',
            '/us_en/contacts',
            '/us_en/customer',
            '/us_en/product-care',
            '/us_en/news',
            '/us_en/policy',
            '/us_en/storelocator',
            '/us_en/stopfake',
            '/us_en/terms-use',
            '/us_en/terms-sale',
            '/us_en/wishlist',
        },
    },
    'http://www.violetgrey.com/': {
        'skip': {
            '/account',
            '/cart',
            '/checkout',
            '/subscriptions',
            '/users',
        }
    },
    'http://www.walgreens.com/': {
        'runjs': {},
        'skip': {
            # custom
            '/balancerewards/',
            '/mktg/',
            # robots.txt
            '/common/',
            '/emailsignup/',
            '/includes/',
            '/iso/',
            '/library/checkdrug/',
            '/logout.jsp',
            '/marketing/emailsignup/',
            '/messaging/',
            '/overlays/',
            '/password/',
            '/pharmacy/',
            '/popups/',
            '/register/',
            '/reviews/',
            '/search/search_results.jsp?',
            '/send/',
            '/shoppinglist/',
            '/store/browse/overlays/',
            '/store/checkout/',
            '/store/sscart.jsp',
            '/storelocator/', # custom
            '/topic/', # custom
            '/webpickup/',
            '/youraccount/',
        }
    },
    'http://www.walmart.com/': {
        'ok': {
            '/',
            '/browse/Beauty/',
            '/c/brand/', # browse brands
            #'/c/kp/', # featured categories # XXX: too broad
            '/c/tp/', # top
            '/cp/Bath-Body/', # categories
            '/cp/Beauty/',
            '/cp/Fragrances/',
            '/cp/Hair-Care/',
            '/cp/Health/',
            '/cp/Makeup/',
            '/cp/Mens-Grooming/',
            '/cp/Shaving/',
            '/cp/Skin-Care/',
            '/ip/', # products
        },
        'skip': {
            # custom
            '/account/',
            '/store/',
            # robots.txt
            '/account/',
            '/api/review/',
            '/browse/invalid-category-id/',
            '/buyguide/',
            '/c/store/',
            '/cart2/',
            '/cdstore/',
            '/classrooms/',
            '/email_collect/',
            '/iphone/',
            '/prod/cp/',
            '/reviews/seller/',
            '/shopping_card/',
            '/shoppinglists/',
            '/solutions/',
            '/store/category/',
            '/store/popular_in_grade/',
        },
    },
    'http://www.yoox.com/us': {
        # ugh...
        # yoox.com/ redirects to /us/women, but /us/women has a canonical address of yoox.com/
        #'ok':{'/us/'},
        'skip': {
            '/al/','/dz/','/ad/','/ar/','/am/','/au/','/at/','/az/',
            '/bh/','/by/','/be/','/ba/','/bn/','/bg/', '/ca/','/cl/','/co/','/ci/', '/cy/','/cz/',
            '/dk/','/do/','/eg/','/ee/','/fi/','/fr/','/ge/','/de/','/gr/','/gt/',
            '/hk/','/hr/','/hu/','/is/','/in/','/id/','/ie/','/il/','/it/','/jp/','/jo/',
            '/kz/','/kw/','/kg/','/lv/','/lb/','/lr/','/li/','/lt/','/lu/',
            '/mo/','/mk/','/mg/','/my/','/mt/','/mx/','/md/','/fr/','/me/','/ma/',
            '/nl/','/nz/','/no/','/om/','/pa/','/py/','/pe/','/ph/','/pl/','/pt/',
            '/qa/','/ro/','/ru/','/it/','/sa/','/rs/','/sg/','/sk/','/si/',
            '/za/','/kr/','/es/','/sr/','/se/','/ch/','/sy/','/tw/','/tj/','/th/','/tn/','/tr/','/tm/',
            '/ua/','/ae/','/uk/','/uz/','/it/','/ve/','/vn/',
            # ?
            '/cms/',
        }
    },
    'http://www.zappos.com/': {
        'skip': {
            '/favorites.do',
            '/*.jpg', # wtf
        }
    },
    'http://www1.bloomingdales.com/': {
        'skip': {
            '/bag/',
            '/customerservice/fandf/',
            '/customerservice/international.jsp',
            '/internationalContext/index.ognc',
            '/myinfo/',
            '/search/',
            '/service/order/',
            '/service/policies/',
            '/shop/registry/wedding/search',
            '/shop/search',
            '/shop/wedding-registry/product',
            '/signin/',
            '/timedevents/index.ognc',
        },
    },
    'http://www1.macys.com/': {
        'skip': {
            '*Natuzzi*',
            '*Natuzzi*',
            '*natuzzi*',
            '*natuzzi*',
            '/bag/add*',
            '/catalog/product/zoom.jsp',
            '/cms/',
            '/compare',
            '/registry/wedding/compare',
            '/search',
            '/shop/registry/wedding/search',
            '/shop/search',
        },
        #'favor': lambda url: bool(re.match(r'/shop/product/.*?\?ID=\d+&CategoryID=\d+', url.path)),
    },
    'https://us.burberry.com/': {
        'runjs': {},
        'skip': {
            # custom
            '/burberry/myburberry/',
            '/checkout/',
            '/customer-service/',
            '/our-history/',
            '/store-locator/',
            # robots.txt
            '/*/?locale=*',
            '/*/?search=true*',
            '/*/?trail=*',
            '/book-of-gifts/gifts-for-children/*',
            '/book-of-gifts/gifts-for-her/*',
            '/book-of-gifts/gifts-for-him/*',
            '/book-of-gifts/gifts-for-the-home/*',
            '/geschenkkatalog/geschenke-fur-ihn/*',
            '/geschenkkatalog/geschenke-fur-kinder/*',
            '/geschenkkatalog/geschenke-fur-sie/*',
            '/geschenkkatalog/geschenke-fur-zuhause/*',
            '/libro-de-los-regalos/regalos-para-/*',
            '/libro-de-los-regalos/regalos-para-el-hogar/*',
            '/libro-de-los-regalos/regalos-para-ella/*',
            '/libro-de-los-regalos/regalos-para-ni/*',
            '/libro-dei-regali/regali-per-i-bambini/*',
            '/libro-dei-regali/regali-per-la-casa/*',
            '/libro-dei-regali/regali-per-lei/*',
            '/libro-dei-regali/regali-per-lui/*',
            '/livret-de-cadeaux/cadeaux-pour-elle/*',
            '/livret-de-cadeaux/cadeaux-pour-la-maison/*',
            '/livret-de-cadeaux/cadeaux-pour-les-enfants/*',
            '/livret-de-cadeaux/cadeaux-pour-lui/*',
            '/livro-de-presentes/presentes-infantis/*',
            '/livro-de-presentes/presentes-para-ela/*',
            '/livro-de-presentes/presentes-para-ele/*',
            '/livro-de-presentes/presentes-para-o-lar/*',
            '/search/*',
            '/store/burberry/views/email/email.jsp*',
        },
    },
    'https://www.italist.com/en': {
        'ok': {
            '/en/',
        },
        'skip': {
            '/en/login',
        },
    },
    'https://www.modaoperandi.com/': {
        'skip': {
            '/about'
            '/careers'
            '/contact'
            '/app'
            '/terms'
            '/affiiates'
            '/signin'
            '/shopping-bag'
        },
    },
    'https://www.shopbop.com/': {
        'skip': {
            '/actions/',
            '/checkout/',
            '/customerservice/',
            '/gp/help/',
            '/myaccount/',
            '/wishlist/',
        }
    },
    'https://www.ssense.com/': {
        'ok': {
            '/',
            '/en-us/',
        },
        'skip': {
            '/fr-fr/'
            '*fr-fr', # why doesn't fr-fr work?!?!?!?
            '/en-ca/',
            # robots.txt
            '*/addproductstoshoppingbag/',
            '*/popup',
            '/*?isAjax=*',
            '/account/',
            '/checkout',
            '/cms/preview/',
            '/compte/',
            '/editorial/queryProduct/',
            '/export/',
            '/feeds/',
            '/hq/',
            '/newsletters/',
            '/nl/',
            '/paiement',
            '/panier',
            '/pma/',
            '/shopping-bag',
        },
    },
    'https://www.theoutnet.com/': {
        'ok': {
            '/en-US/'
        },
        'skip': {
            '/*Filter',
            '/*Search',
            '/*keywords',
            '/*pn=',
            '/*sortBy',
            '/*viewall',
            '/*weekendpage',
        },
    },
    'https://www.tradesy.com/': {
        # seems legit...
    },
    'http://us.rimmellondon.com/': {
        'ok': {
            '/products/',
        },
        'skip': {
            # robots.txt
            '/includes/',
            '/misc/',
            '/modules/',
            '/profiles/',
            '/scripts/',
            '/themes/',
            '/CHANGELOG.txt',
            '/cron.php',
            '/INSTALL.mysql.txt',
            '/INSTALL.pgsql.txt',
            '/INSTALL.sqlite.txt',
            '/install.php',
            '/INSTALL.txt',
            '/LICENSE.txt',
            '/MAINTAINERS.txt',
            '/update.php',
            '/UPGRADE.txt',
            '/xmlrpc.php',
            # clean URLs
            '/admin/',
            '/comment/reply/',
            '/filter/tips/',
            '/node/add/',
            '/search/',
            '/user/register/',
            '/user/password/',
            '/user/login/',
            '/user/logout/',
            # no clean URLs
            '/?q=admin/',
            '/?q=comment/reply/',
            '/?q=filter/tips/',
            '/?q=node/add/',
            '/?q=search/',
            '/?q=user/password/',
            '/?q=user/register/',
            '/?q=user/login/',
            '/?q=user/logout/',
        },
    },
    'http://www.urbanoutfitters.com/': {
        'crawl-delay': 60,
        'skip': {
            # custom
            '/urban/help/',
            '/urban/stores/',
            '/urban/on/',
            # robots.txt
            '/urban/catalog/category.jsp?id=UOWW',
            '/urban/arc/',
            '/urban/checkout/',
            '/urban/content/ApartmentEntertain.html',
            '/urban/content/ApartmentFurnish.html',
            '/urban/content/browsepage_content.html',
            '/urban/content/Home.html',
            '/urban/content/MensAccessories.html',
            '/urban/content/MensApparel.html',
            '/urban/content/MensShoes.html',
            '/urban/content/splashspring_summer.html',
            '/urban/content/WomensAccessories.html',
            '/urban/content/WomensApparel.html',
            '/urban/content/WomensShoes.html',
            '/urban/catalog/category_content_cached.jsp',
            '/urban/coremetrics/',
            '/urban/emails/',
            '/urban/html/damsel_sizechart.html',
            '/urban/html/faq.html',
            '/urban/html/Features.html',
            '/urban/html/gift_cards.html',
            '/urban/html/mail_list_info.html',
            '/urban/html/MailOrderForm.html',
            '/urban/html/mens_brands.html',
            '/urban/html/OrderingAndPayment.html',
            '/urban/html/pop_creditCardInfo.html',
            '/urban/html/pop_daytime_phone.html',
            '/urban/html/popup_giftoptions.html',
            '/urban/html/popup_paymentoptions.html',
            '/urban/html/popup_returnsexchanges.html',
            '/urban/html/popup_shippinginfo.html',
            '/urban/html/popup_sizechart.html',
            '/urban/html/privacy_security.html',
            '/urban/html/ReturnsAndExchanges.html',
            '/urban/html/sale.html',
            '/urban/html/ShippingInformation.html',
            '/urban/html/sizechart_damsel.html',
            '/urban/html/SpecialInformation.html',
            '/urban/html/splash.html',
            '/urban/html/TermsOfUse.html',
            '/urban/html/viewgateway.html',
            '/urban/html/WACC.html',
            '/urban/html/wacc.html',
            '/urban/html/womens_brands.html',
            '/urban/popups/',
            '/urban/signup/',
            '/urban/ui/',
            '/urban/user/',
            '/uk/checkout.jsp',
            '/fr/checkout.jsp',
            '/de/checkout.jsp',
            '/uk/user/*',
            '/fr/user/*',
            '/de/user/*',
            '/*/pos/',
        },
    },
    'https://www.victoriassecret.com/': {},
    'http://www.ysl.com/us': {
        'ok': {
            '/',
            '/us/',
        },
        'skip': {
            # custom
            '/corporate/',
            '/us/Account/',
            '/us/AddressDrivenCheckout/Cart',
            '/us/Help/',
            # robots.txt
            '/yTos/',
            '/teaser.asp*',
        },
    },
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
        if not canonical_url:
            tag = soup.find('meta', itemprop='url', content=True)
            if tag:
                canonical_url = tag.get('content')
        if canonical_url:
            canonical_url = urljoin(url, canonical_url)
    except Exception as e:
        print e
    return canonical_url

'''
TODO: consider:
<link rel="alternate" href="http://www.stylebop.com" hreflang="x-default" >
'''

def get_language(headers, body):
    '''
    Content-Language: en
    Content-Language: mi, en
    <html lang="en_US">
    <html prefix="og: http://ogp.me/ns#" xmlns="http://www.apple.com/itms/" lang="en">
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" >
    <meta name="language" content="fr">
    '''
    lang = None
    return lang

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

def url_fetch(url, referer=None, settings=None):
    settings = settings or {}
    headers = None
    code = -1 # unspecified error
    mimetype = None
    body = None
    canonical_url = None
    try:
        # TODO: limit size...
        # ref: http://stackoverflow.com/questions/23514256/http-request-with-timeout-maximum-size-and-connection-pooling
        with requests.Session() as s:
            # maintain state (cookies, etc) for lifetime of the request
            # some sites set cookies and redirect and check them
            r = s.get(url,
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
        body = r.text # by default use static body...
        if 'runjs' in settings and code == 200 and 'html' in mimetype:
            # if configured, and looks like success, fetch body with
            # headless browser so we execute javascript
            try:
                body = browser_selenium.url_fetch(url, timeout=30)
            except:
                traceback.print_exc()
                code = -1
                body = None
            if body is None:
                if code == 200:
                    code = -1
            sleep(settings.get('crawl-delay') or 5) # make sure we don't request too fast...
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
        gzip_file.write(python_sucks(body).encode('utf8'))
    return stringio.getvalue()
    # TODO: consider one-liner
    #return body.encode('utf8').encode('zlib_encode')


def should_save_body(url, canonical_url, httpcode, mimetype, bodylen):
    if url != canonical_url:
        print "don't save, url != canonical_url"
        return False
    if httpcode < 0 or httpcode >= 400:
        print "don't save, httpcode = %s" % httpcode
        return False
    if bodylen > 1024*1024:
        print "don't save, bodylen > 1M (%s)" % bodylen
        return False
    if mimetype not in ('text/html',
                        'application/xhtml+xml',
                        'text/x-server-parsed-html'):
        print "don't save, mimetype = %s" % mimetype
        return False
    print "save body"
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
    try_fixing_error = httpcode_should_retry(item.get('code')) and age > 3 * days
    if try_fixing_error:
        print 'try_fixing_error now=%s updated=%s (%s) code=%s' % (
            now,
            item.get('updated'), now - item.get('updated') if item.get('updated') else None,
            item.get('code'))
    # last fetch succeeded, but it's getting stale
    is_stale = age > 28 * days
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

def get_links(url, referer=None, settings=None):
    print 'get_links %s' % url
    links = []
    item = db.get_url(url)
    canon = url
    if not item or should_fetch_again(item):
        if not item:
            print 'new %s' % url
        else:
            db.invalidate_cache(url)
            print 'updating %s' % url
        url, results = url_fetch(url, referer=referer, settings=settings)

        # WTF?!?!?!? i have to do this here and i don't know why...
        (code, headers, body, canonical_url, mimetype) = results
        if canonical_url and canonical_url != url:
            print u'canonical_url', canonical_url
            canon = canonical_url
            #links.append(python_sucks(canonical_url))

        links.extend(map(python_sucks, save_url_results(url, results)))
        sleep(5 + abs(int(random.gauss(1, 3)))) # sleep somewhere from 5 to about 21 seconds
    elif item:
        if python_sucks(item.get('url_canon')) != url:
            links.append(python_sucks(item['url_canon']))
        if item.get('links'):
            links.extend(map(python_sucks, item['links']))
    return canon, links


def prefix_matches(path, prefix):
    if prefix == '/':
        return path in ('', '/')
    if '*' in prefix:
        pattern = prefix
        pattern = pattern.replace('+', '[+]')
        pattern = pattern.replace('?', '[?]')
        pattern = pattern.replace('*', '.*?')
        return bool(re.search(pattern, path))
    return (
        path.startswith(prefix)
        or (prefix[-1] == '/' and path == prefix[:-1]) # "/en/" ~= "/en"
    )

assert prefix_matches('/', '/')
assert prefix_matches('', '/')
assert not prefix_matches('/a', '/')
assert prefix_matches('/foo/bar?baz', '/*bar')
assert prefix_matches('/fr-fr/femmes', '/fr-fr/')
assert prefix_matches('/en-de/accessories.html?designer=3852%7C3887', '*?designer=*%7C')

def ok_to_spider(url, fqdn, settings):
    if len(url) > 2048:
        return False
    u = URL(url)
    if u.host.lower() != fqdn:
        # stay on the same fqdn
        return False
    if settings:
        # enforce path prefix whitelist/blacklist
        if 'skip' in settings:
            if any(prefix_matches(u.path + u.query, s) for s in settings['skip']):
                print 'skip', url, settings['skip']
                return False
        if 'ok' in settings:
            if not any(prefix_matches(u.path + u.query, s) for s in settings['ok']):
                print 'not ok', url, settings['ok']
                return False
    if '://www.ssense.com/fr-fr/' in url:
        # FIXME: i don't understand why the simple rule of blocking /fr-fr/ does not work for ssense...
        return False
    return True

def traverse(url, fqdn): # breadth-first traversal
    print 'traverse(%s, %s)' % (url, fqdn)
    # python's unicode support is horrible
    # best spider url to test this with is yoox; they have a bunch of crazy unicode urls
    settings = _Seeds[url]
    # fetch seed url w/o checking whitelist/blacklist
    _canon, urls_ = get_links(python_sucks(url), referer=url, settings=settings)
    urls = OrderedSet([_canon] + urls_)
    while urls:
        next_url = page_links.canonicalize_url(urls.pop(0))
        if ok_to_spider(next_url, fqdn, settings):
            canon, links = get_links(next_url, referer=url, settings=settings)
            while links:
                assert isinstance(links[0], unicode)
                l = page_links.canonicalize_url(links.pop(0))
                if l != next_url and l not in urls and ok_to_spider(l, fqdn, settings):
                    canon, _links = get_links(l, referer=next_url, settings=settings) # ignore results...
                    # prioritize following up w/ canon first
                    if ok_to_spider(canon, fqdn, settings):
                        if canon != l:
                            print 'fetching canon', python_sucks(canon)
                            get_links(python_sucks(canon), referer=l, settings=settings)
                        urls.add(canon)

# TODO: have us try all seeds at all times; schedule each one...
def run(url):
    db.init()
    keepgoing = True
    try:
        while keepgoing:
            if not url:
                url = random.choice(_Seeds.keys())
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

