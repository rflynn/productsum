
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
    17. ... product map at least the top 20 merchants before even bothering to analyze data...
    18. ... ensure all product mappers report brand, otherwise this thing wont matter...

        ```sql
productmap=> select merchant_slug, count(*), count(brand) as has_brand, count(*)-count(brand) as brand_missing from url_product group by merchant_slug order by brand_missing desc;
  merchant_slug  | count | has_brand | brand_missing
-----------------+-------+-----------+---------------
 netaporter      | 19000 |         3 |         18997
 lordandtaylor   | 10840 |         0 |         10840
 neimanmarcus    | 12376 |      9150 |          3226
 macys           |  1912 |         0 |          1912
 bergdorfgoodman |  3164 |      1346 |          1818
 farfetch        |  3846 |      3821 |            25
 bluefly         |  6980 |      6980 |             0
 nordstrom       |  4564 |      4564 |             0
 yoox            |     7 |         7 |             0
 dermstore       |   743 |       743 |             0
 saks            |   264 |       264 |             0
(11 rows)
        ```

    19. map/match Brands
    20. parse/classify Product Name components
    21. figure out what to do when a site is "done"
        * happened to bluefly.com... just cycled through things a lot...
    22. gc S3 to keep costs down
    23. dont overwrite dynamodb item 'created' time

