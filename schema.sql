-- postgresql 9.4+ only

begin;

create table merchant (
    id                  serial primary key,
    slug                varchar(32) not null unique,
    name                varchar(255)
);

create table merchant_site (
    id                  serial primary key,
    merchant_id         integer not null references merchant (id),
    domain              varchar(255) not null unique,
    url                 varchar(255) not null unique
);

create table merchant_product_etl (
    id                  serial primary key,
    datetime_created    timestamp without time zone not null,
    datetime_updated    timestamp without time zone not null,
    merchant_id         integer not null references merchant (id),
    url                 varchar(1024),
    sku                 varchar(100),
    title               varchar(256),
    description         varchar(256),
    brand               varchar(256),
    manuf               varchar(256),
    gtin8               varchar(8),
    gtin12              varchar(12),
    gtin13              varchar(13),
    mpn                 varchar(64),
    ean                 varchar(64),
    price               varchar(64),
    image_url           varchar(1024),
    colors              text[],
    sizes               text[],
    height              varchar(256),
    width               varchar(256),
    length              varchar(256),
    weight              varchar(256)
);

create table brand (
    id                  integer not null primary key autoincrement,
    name                varchar(256) not null unique
);

create table merchant_product (
    id                  serial primary key,
    merchant_product_etl_id integer references merchant_product_etl (id),
    guid                uuid not null unique, -- ref: http://www.postgresql.org/docs/9.4/static/datatype-uuid.html
    datetime_created    timestamp without time zone not null,
    datetime_updated    timestamp without time zone not null,
    url                 varchar(1024),
    merch_id            integer,
    sku                 varchar(64),
    title               varchar(256),
    description         varchar(256),
    brand_id            integer,
    manuf_id            integer,
    gtin8               varchar(8),
    gtin12              varchar(12),
    gtin13              varchar(13),
    mpn                 varchar(64),
    ean                 varchar(64),
    image_url           varchar(1024),
    price               money,
    colors              text[],
    sizes               text[],
    height              float,
    width               float,
    length              float,
    weight              float,
);

commit;

