
psql -h productsum-urlmetadata.ccon1imhl6ui.us-east-1.rds.amazonaws.com -U root -W urlmetadata

select site_id, count(*) as links, count(fetch_code) as fetch, sum(fetch_savebytes)/(1024*1024) as mb from link group by site_id order by mb desc nulls last;

select site_id, host_id, count(*) as links, count(fetch_code) as fetch, sum(fetch_savebytes)/(1024*1024) as mb from link group by site_id, host_id order by site_id asc, host_id desc;

select site_id, host_id, count(*) as links, count(fetch_code) as fetch, sum(fetch_savebytes)/(1024*1024) as mb from link group by site_id, host_id having count(*) > 10 order by site_id asc, host_id desc;

