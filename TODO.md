
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
    12. record Pages along with Products to understand why fewer products are found than expected
    13. run Product -> SQL database with 2+ product mappers
    14. figure out what to do when a site is "done"
        * happened to bluefly.com... just cycled through things a lot...
    15. gc S3 to keep costs down
    16. dont overwrite dynamodb item 'created' time

