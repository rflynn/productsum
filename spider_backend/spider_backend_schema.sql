-- postgresql 9.4+ only

begin;

create extension if not exists pgcrypto;

--drop index if exists uniq_link_url;
drop index if exists idx_link_enqueued;
drop index if exists idx_link_updated;
drop table if exists link;
drop table if exists site;
drop table if exists host_blacklist;
drop table if exists host;
drop table if exists domain;


-- foo.co.uk
-- foo.com
create table domain (
    id                  bigserial primary key,
    name                varchar(256) not null unique
);

-- take subdomains into account
-- foo.bar.com
create table host (
    id                  bigserial primary key,
    domain_id           bigint not null references domain (id),
    name                varchar(256) not null unique
);

-- seed sites that we care about
create table site (
    id                  serial primary key,
    name                varchar(256) not null unique,
    host_id             bigint not null references host (id),
    url_id              bigint unique
);

-- _URLTuple(host=u'www.google.com', username=None, password=None, scheme=u'http', port=None, path=u'/search', query=u'q=q', fragment='a')

-- urls as they are described by others; urls start here
create table link (
    id                  bigserial primary key,
    datetime_created    timestamp with time zone not null,
    -- url details
    site_id             integer not null references site (id),
    host_id             bigint not null references host (id),
    -- postgresql distinct doesn't work with NULLs...
    url_scheme          varchar(32)   not null,
    url_userinfo        varchar(64)   not null default '',
    url_port            varchar(6)    not null default '',
    url_path            varchar(1024) not null,
    url_query           varchar(1024) not null default '', -- TODO: canonicalize
    url_fragment        varchar(1024) not null default '',
    unique (host_id, url_scheme, url_path, url_query),
    -- results of a fetch
    datetime_enqueued   timestamp with time zone,
    datetime_updated    timestamp with time zone,
    datetime_last_ok    timestamp with time zone,
    fetch_canonical_id  bigint references link (id),
    fetch_code          smallint,
    fetch_origbytes     integer,
    fetch_savebytes     integer,
    fetch_mimetype      varchar(64),
    fetch_sha256        bytea
);
-- create unique index uniq_link_url on link (digest(host_id::text || url_scheme::text || url_path || url_query, 'sha1'));
create index idx_link_enqueued on link (datetime_enqueued asc nulls first);
create index idx_link_updated  on link (datetime_updated asc nulls first);

drop function link_fetch_next();
create or replace function link_fetch_next(site_id int, out link_id bigint, out link_next text) as $$
begin
    select l.id,
        concat(l.url_scheme, '://',
            case when l.url_userinfo != ''
                then concat(l.url_userinfo, '@')
                else '' end,
            h.name, l.url_path, coalesce(l.url_query, ''), coalesce(l.url_fragment, ''))
    into link_id, link_next
    from link l join host h on h.id = l.host_id
    where datetime_enqueued is null -- already queued up...
    and fetch_canonical_id is null -- there's a canonical version of this...
    and site_id = site_id
    -- and host_id in (select host_id from site)
    order by datetime_updated asc nulls first limit 1;
    update link set datetime_enqueued = now() where id = link_id;
end;
$$ language plpgsql;

drop function if exists link_fetch_next_site(site_id int);
create or replace function link_fetch_next_site(site_id int, out link_id bigint, out link_next text) as $$
begin
    select l.id,
        concat(l.url_scheme, '://',
            case when l.url_userinfo != ''
                then concat(l.url_userinfo, '@')
                else '' end,
            h.name, l.url_path, coalesce(l.url_query, ''), coalesce(l.url_fragment, ''))
    into link_id, link_next
    from link l join host h on h.id = l.host_id
    where datetime_enqueued is null -- already queued up...
    and fetch_canonical_id is null -- there's a canonical version of this...
    and host_id in (select host_id from site)
    and l.site_id = $1
    order by datetime_updated asc nulls first limit 1;
    update link set datetime_enqueued = now() where id = link_id;
end;
$$ language plpgsql;

-- TODO: eventually we'll want url scheduling implemented via a view+queue...

drop function if exists link_fetch_next_site2(site_id int);
create or replace function link_fetch_next_site2(site_id int, out link_id bigint, out link_next text) as $$
declare
    declare _host_id bigint;
    declare _host_name text;
begin
    _host_id := (select host_id from site where id=$1);
    _host_name := (select name from host where id=_host_id);

    -- explain
    select l.id,
        concat(l.url_scheme, '://',
            case when l.url_userinfo != ''
                then concat(l.url_userinfo, '@')
                else '' end,
            _host_name, l.url_path,
            coalesce(l.url_query, ''), coalesce(l.url_fragment, ''))
    into link_id, link_next
    from link l
    where l.host_id = _host_id
    and datetime_enqueued is null -- already queued up...
    -- and datetime_updated is null -- already queued up...
    and fetch_canonical_id is null -- there's a canonical version of this...
    order by datetime_updated asc nulls first
    limit 1;
    -- update link set datetime_enqueued = now() where id = link_id;
end;
$$ language plpgsql;

commit;


    -- explain
    select l.id,
        concat(l.url_scheme, '://',
            case when l.url_userinfo != ''
                then concat(l.url_userinfo, '@')
                else '' end,
            l.url_path,
            coalesce(l.url_query, ''), coalesce(l.url_fragment, ''))
    -- into link_id, link_next
    from link l
    where l.host_id = (select host_id from site where name='neimanmarcus')
    and datetime_enqueued is null -- already queued up...
    -- and datetime_updated is null -- already queued up...
    and fetch_canonical_id is null -- there's a canonical version of this...
    order by datetime_updated nulls first
    limit 1;

