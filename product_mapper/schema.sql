
begin;

-- record the last run of each page we tried to extract a product from
create table url_page (
    --id                  serial primary key,
    created             timestamp with time zone not null default (now() at time zone 'utc'),
    updated             timestamp with time zone not null default (now() at time zone 'utc'),
    merchant_slug       varchar(16)   not null,
    url_host            varchar(32)   not null,
    url_canonical       varchar(2048) not null unique,
    size                integer,
    proctime            float,
    signals             json
);
-- for fast updated timestamp lookup by url_host by product2db script
create index idx_url_page_url_host on url_page (url_host);

create table url_product (
    --id                  serial primary key,
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

alter table url_product add column id bigserial primary key;
alter table url_page    add column id bigserial primary key;

alter table url_product add column product_mapper_version smallint;
alter table url_product drop column product_mapper_version;
alter table url_page    add column product_mapper_version smallint;

alter table url_product add column asin char(10);

alter table url_product add column isbn13 char(13);
alter table url_product add column isbn10 char(10);

alter table url_product alter column merchant_sku type varchar(64); -- double length

-- double length to make way for 'christianlouboutin'
alter table url_page    alter column merchant_slug type varchar(32);
alter table url_product alter column merchant_slug type varchar(32);


create table brand_translate (
    id                  serial primary key,
    created             timestamp with time zone not null default (now() at time zone 'utc'),
    updated             timestamp with time zone not null default (now() at time zone 'utc'),
    brand_from          varchar(64) not null unique,
    brand_to            varchar(64) not null
);

-- update it like this
-- \copy brand_translate (brand_to, brand_from) from '/tmp/brands.csv' with csv;

-- drop table url_product_name_attr;
create table url_product_name_attr (
    id                  bigserial primary key,
    created             timestamp with time zone not null default (now() at time zone 'utc'),
    updated             timestamp with time zone not null default (now() at time zone 'utc'),

    url_product_id      bigint not null unique references url_product (id),
    url_product_name    text, -- input that drives everything else

    -- attributes extracted from url_product.name
    name_brand          text[],
    name_color          text[],
    name_material       text[],
    name_product        text[],
    name_pattern        text[],
    name_qty            int[],
    name_size_raw       text[],
    name_size_gram      int[],
    name_size_inch      float[],
    name_size_mm        float[],
    name_size_ounce     float[],
    name_size_fl_ounce  float[],
    name_size_liter     float[],
    name_size_gallon    float[],
    name_size_quart     float[],
    name_size_num       float[]

);

alter table url_product_name_attr add column demographic text[];
alter table url_product_name_attr add column name_size_ml float[];

commit;

