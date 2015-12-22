
-- sumarize progress per merchant
select merchant_slug, count(distinct merchant_sku) as dsku, count(merchant_sku) as sku, count(brand) as brand, count(distinct brand) as dbrand, count(distinct bt.brand_to) as dbrand2, count(img_url), max(up.updated), min(up.updated) from url_product up left join brand_translate bt on bt.brand_from = up.brand group by merchant_slug order by dsku desc;

-- most popular brands not translated
select distinct brand, count(*) as cnt from url_product where brand not in (select brand_from from brand_translate) group by brand order by cnt desc;


delete from brand_translate;
\copy brand_translate (brand_to, brand_from) from '/tmp/brands.csv' delimiter ',' csv;


\copy (select brand from (select brand, count(*) as cnt from url_product group by brand order by cnt desc) as x) to '/tmp/brands.csv' with csv;
\copy (select brand, count(*) as cnt from url_product group by brand order by cnt desc) to '/tmp/brands.csv' with csv;

select distinct brand, count(*) as cnt from url_product group by brand order by cnt desc;
select distinct brand, count(*) as cnt from url_product group by brand order by brand asc;

—- how are merchants doing overall?
select merchant_slug, count(distinct merchant_sku) as dsku, count(merchant_sku) as sku, count(brand) as br, count(distinct brand) as dbrand from url_product group by merchant_slug order by dsku desc;
select merchant_slug, count(distinct merchant_sku) as dsku, count(merchant_sku) as sku, count(brand) as br, count(distinct brand) as dbrand from url_product group by merchant_slug order by dsku desc;
select merchant_slug, count(*) as cnt from url_product group by merchant_slug order by cnt desc;
select merchant_slug, count(distinct merchant_sku), count(*) as cnt from url_product group by merchant_slug order by cnt desc;
select merchant_sku, count(*) as cnt from url_product where merchant_slug='neimanmarcus' group by merchant_sku having count(*) > 1 order by cnt desc;
select merchant_slug, round(sum(proctime)::numeric/count(*),2) as proctime from url_page group by merchant_slug order by proctime desc;
select merchant_slug, count(*) as cnt from url_page group by merchant_slug order by cnt desc;

select url_canonical from url_page where merchant_slug='neimanmarcus' and url_canonical like '%/p.prod%' and url_canonical not in (select distinct url_canonical from url_product);

select distinct replace(regexp_replace(lower(brand), '[^A-Za-z -]+', '', 'g'), '  ', ' ') as brandx, count(*) as cnt from url_product group by brandx order by cnt desc;

select count(*), round(sum(size)::numeric / (1024*1024*1024), 3) from url_page where updated >= now() - interval '48 hours';

select url_canonical from url_product where merchant_slug='farfetch' order by url_canonical;

select merchant_slug, count(distinct merchant_sku) as dsku, count(merchant_sku) as sku, count(brand) as br, count(color) as c from url_product group by merchant_slug order by dsku desc;

productmap=> select count(*), round(sum(size)::numeric / (1024*1024*1024), 3) from url_page where updated >= now() - interval '72 hours';
 count  | round
--------+--------
 428982 | 81.712
(1 row)

select price_min::integer - (price_min::integer % 25) as p, count(*) as cnt from url_product group by p order by p asc;

\copy (select lower(name) as namelo, count(*) as cnt from url_product group by name order by cnt desc) to '/tmp/productname.csv' with csv;

select url_host, count(*) from url_product where brand = 'Christian Louboutin' group by url_host;


select brand, coalesce(bl.brand_to, brand), url_host,url_canonical from url_product up left join brand_translate bl on bl.brand_from=up.brand where brand='YVES SAINT LAURENT' limit 3;

IPs: 52.91.13.218,54.172.206.22,104.131.215.237,45.55.46.140,104.236.58.197,104.236.83.138

https://678643648931.signin.aws.amazon.com/console

pyMicrodata==2.0
unicodecsv==0.14.1
urllib3==1.12


select * from (select (signals::json->>'og')::json->>'title' as jsontitle from url_page where merchant_slug='macys' limit 100) as x where jsontitle is not null order by jsontitle limit 100;

