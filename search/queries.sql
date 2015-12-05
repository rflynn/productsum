select merchant_sku, count(*) as cnt from url_product where merchant_slug='neimanmarcus' group by merchant_sku having count(*) > 1 order by cnt desc;

\copy (select brand from (select distinct brand, count(*) as cnt from url_product group by brand order by brand asc) as x) to '/tmp/brands.csv' with csv;


