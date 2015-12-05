
begin;

savepoint sephora;
insert into domain (id, name) values (1001, 'sephora.com');
insert into host   (id, domain_id, name) values (1001, 1001, 'sephora.com');
insert into host   (id, domain_id, name) values (1002, 1001, 'www.sephora.com');
insert into host   (id, domain_id, name) values (1003, 1001, 'community.sephora.com');
insert into host_blacklist (host_id) select id from host where name='community.sephora.com';
insert into site   (id, name, host_id, url_id) values (1001, 'sephora', 1002, 1001);
insert into link   (id, datetime_created, site_id, host_id, url_scheme, url_path)
    values (1001, now(), 1001, 1002, 'http', '/');
release savepoint sephora;

savepoint nordstrom;
insert into domain (id, name) values (1002, 'nordstrom.com');
insert into host   (id, domain_id, name) values (1004, 1002, 'nordstrom.com');
insert into host   (id, domain_id, name) values (1005, 1002, 'shop.nordstrom.com');
insert into site   (id, name, host_id, url_id) values (1002, 'shop.nordstrom', 1005, null);
insert into link   (id, datetime_created, site_id, host_id, url_scheme, url_path)
    values (10002, now(), 1002, 1005, 'http', '/');
update site set url_id=10002 where id=1002;
release savepoint nordstrom;

savepoint macys;
insert into domain (id, name) values (1003, 'macys.com');
insert into host   (id, domain_id, name) values (1006, 1003, 'macys.com');
insert into host   (id, domain_id, name) values (1007, 1003, 'www1.macys.com');
insert into site   (id, name, host_id, url_id) values (1003, 'macys', 1007, null);
insert into link   (id, datetime_created, site_id, host_id, url_scheme, url_path)
    values (10003, now(), 1003, 1007, 'http', '/');
update site set url_id=10003 where id=1003;
release savepoint macys;

savepoint yoox;
insert into domain (id, name) values (1004, 'yoox.com');
insert into host   (id, domain_id, name) values (1008, 1004, 'yoox.com');
insert into host   (id, domain_id, name) values (1009, 1004, 'www.yoox.com');
insert into site   (id, name, host_id, url_id) values (1004, 'yoox', 1009, null);
insert into link   (id, datetime_created, site_id, host_id, url_scheme, url_path)
    values (10004, now(), 1004, 1009, 'http', '/us/women');
update site set url_id=10004 where id=1004;
release savepoint yoox;

savepoint neimanmarcus;
insert into domain (id, name) values (1005, 'neimanmarcus.com');
insert into host   (id, domain_id, name) values (1010, 1005, 'neimanmarcus.com');
insert into host   (id, domain_id, name) values (1011, 1005, 'www.neimanmarcus.com');
insert into site   (id, name, host_id, url_id) values (1005, 'neimanmarcus', 1011, null);
insert into link   (id, datetime_created, site_id, host_id, url_scheme, url_path)
    values (10005, now(), 1005, 1011, 'http', '/');
update site set url_id=10005 where id=1005;
release savepoint neimanmarcus;

savepoint netaporter;
insert into domain (id, name) values (1006, 'net-a-porter.com');
insert into host   (id, domain_id, name) values (1012, 1006, 'net-a-porter.com');
insert into host   (id, domain_id, name) values (1013, 1006, 'www.net-a-porter.com');
insert into site   (id, name, host_id, url_id) values (1006, 'net-a-porter', 1013, null);
insert into link   (id, datetime_created, site_id, host_id, url_scheme, url_path)
    values (10006, now(), 1006, 1013, 'http', '/us/en/');
update site set url_id=10006 where id=1006;
release savepoint netaporter;

savepoint barneys;
insert into domain (id, name) values (1007, 'barneys.com');
insert into host   (id, domain_id, name) values (1014, 1006, 'barneys.com');
insert into host   (id, domain_id, name) values (1015, 1006, 'www.barneys.com');
insert into site   (id, name, host_id, url_id) values (1007, 'barneys', 1015, null);
insert into link   (id, datetime_created, site_id, host_id, url_scheme, url_path)
    values (10007, now(), 1007, 1015, 'http', '/');
update site set url_id=10007 where id=1007;
release savepoint barneys;

savepoint violetgrey;
insert into domain (id, name) values (1008, 'violetgrey.com');
insert into host   (id, domain_id, name) values (1016, 1006, 'violetgrey.com');
insert into host   (id, domain_id, name) values (1017, 1006, 'www.violetgrey.com');
insert into site   (id, name, host_id, url_id) values (1008, 'violetgrey', 1017, null);
insert into link   (id, datetime_created, site_id, host_id, url_scheme, url_path)
    values (10008, now(), 1008, 1017, 'http', '/');
update site set url_id=10008 where id=1008;
release savepoint violetgrey;

savepoint bergdorfgoodman;
--insert into domain (id, name) values (12, 'bergdorfgoodman.com');
--insert into host   (id, domain_id, name) values (16, 12, 'www.bergdorfgoodman.com');
insert into site   (id, name, host_id, url_id) values (1009, 'bergdorfgoodman', 16, null);
--insert into link   (id, datetime_created, site_id, host_id, url_scheme, url_path)
--    values (10009, now(), 1337, 16, 'http', '/');
update site set url_id=1337 where id=1009;
release savepoint bergdorfgoodman;



commit;

