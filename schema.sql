create table
  public.global_ledger (
    id bigint generated by default as identity,
    gold_difference bigint not null default '0'::bigint,
    red_difference bigint not null default '0'::bigint,
    green_difference bigint not null default '0'::bigint,
    blue_difference bigint not null default '0'::bigint,
    dark_difference bigint not null default '0'::bigint,
    created_at timestamp with time zone not null default now(),
    order_id bigint not null default '-1'::bigint,
    order_type text not null default 'unknown'::text,
    potion_capacity bigint not null default '0'::bigint,
    ml_capacity bigint not null default '0'::bigint,
    constraint global_ledger_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.potion_ledger (
    id bigint generated by default as identity,
    potion_id bigint null,
    inventory_change bigint not null default '0'::bigint,
    created_at timestamp with time zone not null default now(),
    order_id bigint not null default '-1'::bigint,
    order_type text not null default 'unknown'::text,
    constraint potion_ledger_pkey primary key (id),
    constraint potion_ledger_id_key unique (id),
    constraint potion_ledger_potion_id_fkey foreign key (potion_id) references potions (potion_id)
  ) tablespace pg_default;

create table
  public.potions (
    item_sku text not null default 'unknown'::text,
    red_ml integer not null default 0,
    green_ml integer not null default 0,
    blue_ml integer not null default 0,
    dark_ml integer not null default 0,
    price bigint not null default '0'::bigint,
    potion_id bigint generated by default as identity,
    constraint potions_pkey primary key (potion_id),
    constraint potions_item_sku_key unique (item_sku),
    constraint potions_potion_id_key unique (potion_id)
  ) tablespace pg_default;

create table
  public.carts (
    cart_id bigint generated by default as identity,
    customer_name text null,
    constraint carts_pkey primary key (cart_id),
    constraint carts_cart_id_key unique (cart_id)
  ) tablespace pg_default;

create table
  public.cart_items (
    cart_id integer not null,
    potion_id bigint not null,
    quantity bigint not null default 0,
    id bigint generated by default as identity,
    constraint cart_items_pkey primary key (id),
    constraint cart_items_id_key unique (id),
    constraint cart_items_potion_id_fkey foreign key (potion_id) references potions (potion_id),
    constraint public_cart_items_cart_id_fkey foreign key (cart_id) references carts (cart_id) on update cascade on delete cascade
  ) tablespace pg_default;