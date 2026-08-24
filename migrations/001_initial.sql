create extension if not exists pgcrypto;

create table if not exists public.categories (
    id uuid primary key default gen_random_uuid(),
    name text not null check (char_length(trim(name)) between 1 and 120),
    sort_order integer not null default 0,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.products (
    id uuid primary key default gen_random_uuid(),
    category_id uuid not null references public.categories(id) on update cascade on delete restrict,
    name text not null check (char_length(trim(name)) between 1 and 160),
    description text not null default '',
    price numeric(12, 2) not null check (price >= 0),
    image_file_id text,
    is_active boolean not null default true,
    sort_order integer not null default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.customers (
    id uuid primary key default gen_random_uuid(),
    telegram_id bigint not null unique,
    username text,
    first_name text,
    phone text,
    address text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.orders (
    id uuid primary key default gen_random_uuid(),
    customer_id uuid not null references public.customers(id) on update cascade on delete restrict,
    total_amount numeric(12, 2) not null check (total_amount >= 0),
    status text not null default 'new' check (status in ('new', 'accepted', 'preparing', 'delivering', 'completed', 'cancelled')),
    payment_method text not null check (payment_method in ('cash', 'card', 'online')),
    address text not null,
    comment text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.order_items (
    id uuid primary key default gen_random_uuid(),
    order_id uuid not null references public.orders(id) on update cascade on delete cascade,
    product_id uuid not null references public.products(id) on update cascade on delete restrict,
    product_name text not null,
    quantity integer not null check (quantity > 0),
    price numeric(12, 2) not null check (price >= 0),
    total numeric(12, 2) not null check (total >= 0)
);

create index if not exists products_category_active_order_idx on public.products(category_id, is_active, sort_order);
create index if not exists categories_active_order_idx on public.categories(is_active, sort_order);
create index if not exists orders_status_created_idx on public.orders(status, created_at desc);
create index if not exists orders_customer_created_idx on public.orders(customer_id, created_at desc);

create or replace function public.set_updated_at() returns trigger
language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists categories_set_updated_at on public.categories;
create trigger categories_set_updated_at before update on public.categories for each row execute function public.set_updated_at();
drop trigger if exists products_set_updated_at on public.products;
create trigger products_set_updated_at before update on public.products for each row execute function public.set_updated_at();
drop trigger if exists customers_set_updated_at on public.customers;
create trigger customers_set_updated_at before update on public.customers for each row execute function public.set_updated_at();
drop trigger if exists orders_set_updated_at on public.orders;
create trigger orders_set_updated_at before update on public.orders for each row execute function public.set_updated_at();

alter table public.categories enable row level security;
alter table public.products enable row level security;
alter table public.customers enable row level security;
alter table public.orders enable row level security;
alter table public.order_items enable row level security;

-- The bot uses the server-side Supabase key. Keep that key only in .env.
-- If the frontend reads Supabase directly, add a separate anon-key policy layer rather than exposing the service key.
