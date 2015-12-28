
TODO:
    1. ✔ reduce dynamodb reads using a cache
        * the combination of breadth-first traversals and common web site topology mean that we re-read the same common links over and over, which is expensive, as dynmodb is provisioned by io rate
        * worst situations:
            1. re-starting a spider after a crash
            2. farfetch
            3. bergdorfgoodman
            4. nordstrom
            5. neimanmarcus
            6. macys
            7. violetgrey
    2. ✔ dont save zero-link results from a 'Seed' url
        * if we get it, treat it as an error
    3. ✔ circumvent Saks/Afakami AWS block
        * DigitalOcean (and local) works, whew
        * try different regions
        * try assigning different public IPs
        * try different cloud providers
    4. ✔ reduce cache memory usage by clearing out infrequently accessed keys
    5. ✔ figure out how to handle 5xx/503s better
        * mytheresa.com went down for updates
    6. ✔ handle ProvisionedThroughputExceededException caused by table scans
    7. ✔ report counts and sums from dynamodb
        ...
    8. ✔ figure out how to avoid getting 403d
        * saks is fucking ruthless
            * reduce spider rate to 5+ seconds and use DigitalOcean
    9. ✔ figure out how to use less RAM
        * lordandtaylor keeps crashing...
            * unique url list
    10. ✔ dont save the body of 4xx/5xx pages...
    10. ✔ MVP mapped Product -> SQL database
    11. ✔ evaluate https://github.com/RDFLib/pymicrodata
        * couldnt understand wtf it was doing...
    12. ✔ record Pages along with Products to understand why fewer products are found than expected
    13. ✔ run Product -> SQL database with 2+ product mappers
    14. ✔ figure out how to run a single, targeted product mapper over the metadata without scanning the entire collection
        * working on creating an index and using dynamodb.query() instead of .scan()
            * index created...
            * ...
    15. ✔ prevent spidering non-english and other less valuable urls
            * whitelist/blacklist url paths per host...
    16. ... speed up product2db by not re-parsing the HTML 3 times(!)
            ✔ refactor OG to use soup
            * refactor SchemaOrg to use soup
    17. ✔ product map at least the top 20 merchants before even bothering to analyze data...
    18. ✔ ensure all product mappers report brand, otherwise this thing wont matter...
    19. ✔ make spider not waste so much time on worthless urls
            be smarter, favor canonical urls more
    20. ✔ try re-importing the following merchants after the spider has had a chance to run:
        yoox
        saks
        macys
    21. ✔ track a version number for product mappers, so we know when to re-run all pages, and when we can skip older pages and only run new stuff
    22. ✔ run product2db more efficiently: respect link timestamps and product mapper versions
    23. ✔ normalize brands
    24. ✔ one-time import of url_product + normalized brand to elasticsearch
    25. ✔ www frontend for elasticsearch
    26. ✔ research efficacy of LCD search
    27. ✔ test url -> content -> product extraction -> search by url -> search by product
        e.g. http://www.elle.com/fashion/trend-reports/g27402/biggest-fashion-trends-2015/?slide=1
    28. ✔ get a non-trivial opencv demo script running
    29. ✔ enumerate all mapped brands, and calculate "missing" brands from new product2db runs
    30. ✔ reduce ridiculous flask debug cpu usage
            ref: http://stackoverflow.com/questions/28241989/flask-app-restarting-with-stat
    31. ✔ get ES custom stemming working
    32. ✔ parse product tags/ngrams
    33. ✔ query by multi-term ngrams in elasticsearch
        ref: https://www.elastic.co/guide/en/elasticsearch/guide/current/phrase-matching.html
    34. ✔✔ watch the new star wars
    35. ✔ handle searching by color better...
    35. ✔ why did this url disappear and never come back...? http://www.bluefly.com/sisley-sisley-by-sisley-eye-contour-mask-30ml1oz/p/357805401/detail.fly
    36. ✔ create smart dynamodb index with only the fields i need
    37. ... add second layer in database
        parse out tagged attributes into separate fields
            brand
    38. ✔ add selenium browser support on top of requests for sephora
    39. url_product.updated timestamp should be when the doc was fetched, not when it was processed
    40. normalize product url - use canonical:
            * nordstrom
            * barneys (e.g. 504143194)
            * fwrd (e.g. http://localhost:9998/?q=brand:(Charlotte%20Olympia)%20Aranea%20Suede%20Heels%20$895)
            * ssense /fr-fr/ products...

    ...
    ref: https://lucidworks.com/blog/2014/07/12/solution-for-multi-term-synonyms-in-lucenesolr-using-the-auto-phrasing-tokenfilter/

    23. hook up a script to listen to a process product pages off an SQS queue based on host
    24. set up AWS Lambda on Dynamo to enqueue page metadata to SQS when a page is spidered

    ... download images
    ... analyze images
    ref: http://www.pyimagesearch.com/2014/12/01/complete-guide-building-image-search-engine-python-opencv/
    23. parse/classify Product Name components
    25. figure out how to re-start spider and "catch up" faster; fast-forward though visited links

    24. figure out what to do when a site is "done"
        * happened to bluefly.com... just cycled through things a lot...
    25. gc S3 to keep costs down
    26. dont overwrite dynamodb item 'created' time
    27. use a faster compression algorithm than gzip/zlib; the spider is currently too CPU-intensive when re-starting and seeking through the cach. consider: https://code.google.com/p/lz4/

