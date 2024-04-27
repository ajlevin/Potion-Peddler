create table
  public.global_inventory (
    num_green_ml bigint not null default '0'::bigint,
    gold bigint not null default '100'::bigint,
    num_red_ml bigint not null default '0'::bigint,
    num_blue_ml bigint not null default '0'::bigint,
    num_dark_ml bigint not null default '0'::bigint,
    id integer generated by default as identity,
    potion_capacity bigint not null default '50'::bigint,
    ml_capacity bigint not null default '10000'::bigint,
    constraint global_inventory_pkey primary key (id),
    constraint global_inventory_id_key unique (id)
  ) tablespace pg_default;

create table
  public.potions (
    item_sku text not null,
    red_ml integer not null default 0,
    green_ml integer not null default 0,
    blue_ml integer not null default 0,
    dark_ml integer not null default 0,
    price bigint not null default '0'::bigint,
    inventory bigint not null default '0'::bigint,
    constraint potions_pkey primary key (item_sku)
  ) tablespace pg_default;

create table
  public.cart_items (
    cart_id integer generated by default as identity,
    item_sku text not null,
    quantity bigint not null default 0,
    constraint cart_items_pkey primary key (cart_id),
    constraint public_cart_items_cart_id_fkey foreign key (cart_id) references carts (cart_id) on update cascade on delete cascade,
    constraint public_cart_items_item_fkey foreign key (item_sku) references potions (item_sku)
  ) tablespace pg_default;

create table
  public.carts (
    cart_id bigint generated by default as identity,
    customer_name text null,
    constraint carts_pkey primary key (cart_id),
    constraint carts_cart_id_key unique (cart_id)
  ) tablespace pg_default;