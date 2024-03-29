
productsum.com

# Learning Tech
1. AWS Dynamo
2. AWS RDS - Postgresql
3. Postgresql Array and JSON data types
4. AWS SQS
5. AWS Lambda
6. AWS ElasticSearch Service
7. DigitalOcean
8. Docker?

## Interesting Terms

1. "dress shirt"
2. "top coat"
3. "black label"

## How To Do Stuff

```sh
mkdir src
cd src
sudo apt-get update -y
sudo apt-get install -y git

git clone https://github.com/rflynn/productsum.git

cd productsum
/bin/bash install.sh
```

### DynamoDB

#### Table details
```
                       Table name  link
            Primary partition key  url (String)
                 Primary sort key  -
                     Table status  Active
                    Creation date  November 29, 2015 at 12:56:24 AM UTC-5
  Provisioned read capacity units  1
 Provisioned write capacity units  1
               Last decrease time  June 6, 2016 at 7:09:57 PM UTC-4
               Last increase time  January 18, 2016 at 3:06:28 AM UTC-5
          Storage size (in bytes)  42.81 GB
                       Item count  17,792,113
                           Region  US East (N. Virginia)
       Amazon Resource Name (ARN)  arn:aws:dynamodb:us-east-1:678643648931:table/link
```

#### Index
```
Name .............. host-index3
Status ............ Active
Type .............. GSI
Partition key ..... host (String)
Sort key .......... updated (Number)
Attributes ........ url, host, updated, body
Read capacity ..... 1
Write capacity .... 1
Size .............. 3,046,811,143
Item count ........ 17,792,113
```

### Set up ElasticSearch

```
https://console.aws.amazon.com/es/home?region=us-east-1

My Elasticsearch domains
Domain  Elasticsearch version   Searchable documents    Cluster health  Free storage space  Minimum free storage space  Configuration state
es0     1.5                     2,238,935               Yellow          5.71 GB             5.71 GB                     Active
```

Access policy:
```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "*"
      },
      "Action": "es:*",
      "Resource": "arn:aws:es:us-east-1:678643648931:domain/es0/*"
    }
  ]
}
```

#### Indicies

```
Product

Count ......... 2238933
Size in bytes ....... 1.53 GB
Query total ...../... 0
Mappings
    product
        available_colors    string
        brand               string
        brand_ascii         string
        brand_orig          string
        brand_orig_ascii    string
        brand_raw           string
        brand_raw_ascii     string
        color               string
        currency            string
        img_urls            string
        in_stock            boolean
        merchant_sku        string
        merchant_slug       string
        name                string
        price_max           float
        price_min           float
        sale_price_max      float
        sale_price_min      float
        stock_level         long
        updated             long
        url                 string
        url_host            string
        url_raw             string
```

### Run a Spider

```sh
/bin/bash spider.sh http://www.example.com/
```


### Spider Archive -> products in SQL

```sh
while true; do time AWS_ACCESS_KEY_ID=AKIAIJSFBGWDARVXQBSA AWS_SECRET_ACCESS_KEY=KaaKt1ZoBzyhDtmMFKtVxp0ei/heAg3dNAPNJ+Qr AWS_DEFAULT_REGION=us-east-1 PYTHONPATH=. python product2db.py www.jcpenney.com www.ln-cc.com www.neimanmarcus.com www.narscosmetics.com www.toryburch.com www.sephora.com www.nastygal.com www1.bloomingdales.com www.skinstore.com shop.riteaid.com www.dillards.com www.belk.com www.revolveclothing.com www.bergdorfgoodman.com www.matchesfashion.com www.zappos.com www.tradesy.com www.bluefly.com www1.bloomingdales.com www1.macys.com www.yoox.com www.nordstrom.com www.stylebop.com www.net-a-porter.com www.therealreal.com www.cvs.com www.bathandbodyworks.com www.selfridges.com www.harrods.com  us.jimmychoo.com shop.mango.com us.christianlouboutin.com us.jimmychoo.com www.6pm.com www.jcrew.com www.ralphlauren.com www.walmart.com www.walgreens.com www.target.com; sleep 5; done
```

### Load Brands

from search/

#### flatten manually-curated brand mapping to something sql can handle.

brands.yml -> brands.csv

```sh
PYTHONPATH=.. python brandload.py > /tmp/brands.csv
```

#### elasticsearch index brand normalization

brands.csv -> brand translate table

```sql
delete from brand_translate;
\copy brand_translate (brand_to, brand_from) from '/tmp/brands.csv' delimiter ',' csv
```

brand translate table -> tag.brands.csv for parser
```
\copy (select brand_from from brand_translate order by brand_from) to '/tmp/brandfrom.csv'
mv /tmp/brandfrom.csv ./data/tag.brand.csv
```

### Load url products from SQL into ES for searching

```sh
time PYTHONPATH=product_mapper/ python search/elasticsearch_create_index.py
```

### Map url_product.name -> url_product_name_attr

```sh
cd search
source ../venv/bin/activate
PYTHONPATH=.. python search/url_product_name_attr.py
```


## Install

### OSX

```
ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
brew install pip
sudo pip-2.7 install virtualenv

# needed?!
brew install pyenv-virtualenv

```

my favorite url:
http://www.lordandtaylor.com/webapp/wcs/stores/servlet/en/SearchDisplay?sType=SimpleSearch&catalogId=10102&top_category=13658&categoryId=14433&storeId=10151&facet=price_USD:(({* 50} 50)+OR+({50 100} 100))&identifier=1448037084586


## On-Page Javascript Tag

```html
<script src="http://s3.amazonaws.com/prod-io/js/search.js"></script>
```

1. `DOM node → [{offset,length,product},...]`



merch
    id
    slug
    shortname
    fullname

manuf
    ...

brand
    id
    name

brand_map
    id
    brand_id_to
    name

merchant
    ...

merchant_site
    ...



list domains
spider domains
    save sku -> contents to s3
    push metadata into queue


```
urlmetadata=> select * from site;
  id  |      name       | host_id | url_id
------+-----------------+---------+--------
 1001 | sephora         |    1002 |   1001
 1002 | shop.nordstrom  |    1005 |  10002
 1009 | bergdorfgoodman |      16 |   1337
 1003 | macys           |    1007 |  10003
 1004 | yoox            |    1009 |  10004
 1005 | neimanmarcus    |    1011 |  10005
 1006 | net-a-porter    |    1013 |  10006
 1007 | barneys         |    1015 |  10007
 1008 | violetgrey      |    1017 |  10008
(9 rows)

urlmetadata=> select site_id, count(*) as links, count(fetch_code) as fetch, sum(fetch_savebytes)/(1024*1024) as mb from link group by site_id order by mb desc nulls last;
 site_id |  links  | fetch | mb
---------+---------+-------+-----
    1005 |  139654 | 24907 | 638
    1002 |  213754 | 10129 | 323
    1007 | 2764983 | 10104 | 295
    1009 |   33796 |  5063 | 184
    1008 |   18491 |  3646 |  91
    1006 |   46306 |  1951 |  33
    1001 |    1170 |   160 |   4
    1004 |     546 |     1 |   0
    1003 |       1 |     0 |
(9 rows)
```

merchants
    amazon.com
    neimanmarcus.com
    dermstore.com
    jet.com
    newegg.com
    walmart.com
    alibaba.com
    macys.com
    http://www.saksfifthavenue.com/
    drugstore.com

http://www.amazon.com/gp/product/B00HFJWKWK/
ua='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36'
curl -H "User-Agent: $ua" -o - http://www.amazon.com/gp/product/B00HFJWKWK/ 2>/dev/null | egrep -o 'asin=(\w+)' | cut -c 6- | sort | uniq

bootstrap with a few asins
forever {
    asin := choose a random asin that hasn't been fetched within $timeframe
    url := construct url with asin
    body := fetch url
    save to s3/amzn/$asin -> gzip(body)
    asins := find all asins in url contents
    save asins to database
}

https://jet.com/product/Lenovo-LaVie-Z-360-20FF0012US-Laptop-Black-8GB-RAM/b8030dcd2f7d4ab78e68b9a0312a8701
jet.core.analytics.raw
Object {sku: "b8030dcd2f7d4ab78e68b9a0312a8701", upc: "889561305553", manufacturer: "Lenovo", packageDimensions: Object, partNumber: "20FF0012US"…}

Weird shit:
    Angular URLs: http://www.sephora.com/{{sku.productSearchUrl}}

https://www.amazon.com/ap/signin?openid.assoc_handle=aws&openid.return_to=https%3A%2F%2Fsignin.aws.amazon.com%2Foauth%3Fresponse_type%3Dcode%26client_id%3Darn%253Aaws%253Aiam%253A%253A015428540659%253Auser%252Fsqs%26redirect_uri%3Dhttps%253A%252F%252Fconsole.aws.amazon.com%252Fsqs%252Fhome%253Fregion%253Dus-east-1%2526state%253DhashArgs%252523queue-browser%25253Aselected%25253Dhttps%25253A%25252F%25252Fsqs.us-east-1.amazonaws.com%25252F678643648931%25252Fqtest1%25253Bprefix%25253D%2526isauthcode%253Dtrue%26noAuthCookie%3Dtrue&openid.mode=checkid_setup&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&action=&disableCorpSignUp=&clientContext=&marketPlaceId=&poolName=&authCookies=&pageId=aws.ssop&siteState=registered%2Cen_US&accountStatusPolicy=P1&sso=&openid.pape.preferred_auth_policies=MultifactorPhysical&openid.pape.max_auth_age=120&openid.ns.pape=http%3A%2F%2Fspecs.openid.net%2Fextensions%2Fpape%2F1.0&server=%2Fap%2Fsignin%3Fie%3DUTF8&accountPoolAlias=&forceMobileApp=0&language=en_US&forceMobileLayout=0
