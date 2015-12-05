
begin;

-- record the last run of each page we tried to extract a product from
create table url_page (
    created             timestamp with time zone not null default (now() at time zone 'utc'),
    updated             timestamp with time zone not null default (now() at time zone 'utc'),
    merchant_slug       varchar(16)   not null,
    url_host            varchar(32)   not null,
    url_canonical       varchar(2048) not null unique,
    size                integer,
    proctime            float,
    signals             json
);

create table url_product (
    created             timestamp with time zone not null default (now() at time zone 'utc'),
    updated             timestamp with time zone not null default (now() at time zone 'utc'),
    merchant_slug       varchar(16)   not null,
    url_host            varchar(32)   not null,
    url_canonical       varchar(2048) not null,
    merchant_sku        varchar(32)   not null,
    unique (url_canonical, merchant_sku),
    gtin8               char(8),
    gtin12              char(12),
    gtin13              char(13),
    gtin14              char(14),
    mpn                 varchar(32),
    -- price ranges
    price_min           numeric(10, 3),
    price_max           numeric(10, 3),
    sale_price_min      numeric(10, 3),
    sale_price_max      numeric(10, 3),
    currency            char(3),
    brand               text,
    category            text,
    bread_crumb         text[],
    in_stock            bool,
    stock_level         integer,
    name                text,
    title               text,
    descr               text,
    features            text[],
    color               text,
    available_colors    text[],
    size                text,
    available_sizes     text[],
    img_url             text,
    img_urls            text[]
);

alter table url_product add column upc varchar(16);

commit;

