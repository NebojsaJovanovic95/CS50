CREATE TABLE users
(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL,
    points NUMERIC NOT NULL DEFAULT 10000.00
);

create table baskets
(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    user_id integer not null,
    basket_price float not null,
    points_earned float not null,
    transaction_date datetime,
    stripe_transaction text not null
);

create table purchases
(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    basket_id integer not null,
    wine_id integer not null,
    quantity integer not null,
    item_price float not null
);

create table wines
(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name text not null,
    class text not null,
    brand text not null,
    country text not null,
    region text not null,
    volume float not null,
    alcohol float not null,
    year integer not null,
    price float not null
);


--select user data
select * from users
where id = ?;

select * from purchases
where basket_id in (
    select id from baskets
    where user_id = ?
);

select * from baskets
where user_id = ?;

--select joined wines and purchases
select * from wines
inner join purchases
on wines.id = purchases.wine_id;

--select joined purchases and baskets
select * from purchases
inner join baskets
on purchases.basket_id = baskets.id;

--attempt to joing wines to purchases to baskets
select * from wines
inner join (
    select * from purchases
    inner join baskets
    on purchases.basket_id = baskets.id
) on wines.id = purchases.wine_id;

--join three tables
select * from (
    (
        purchases inner join wines on wines.id = purchases.wine_id
    ) inner join baskets on baskets.id = purchases.basket_id
);

--now we select all where id is our session["user_id"]
select * from (
    (
        purchases inner join wines on wines.id = purchases.wine_id
    ) inner join baskets on baskets.id = purchases.basket_id
)
where baskets.user_id = ?;


--wines listed for purchase
select * from wines;

--inserting an item into wines
insert into wines (
    name, class, brand, country, region, volume, alcohol, year, price
)
values (
    ?, ?, ?, ?, ?, ?, ?, ?, ?
);


-- Inserting a new basket and getting a scoped identity
insert into baskets (
    user_id,
    basket_price,
    points_earned,
    transaction_date,
    stripe_transaction
) values (
    ?,
    ?,
    ?,
    current_timestamp,
    ?
) output scope_identity;


--unit insertion into purchases
insert into (
    basket_id,
    wine_id,
    quantity,
    item_price
) values (
    ?, ?, ?, ?
);--- use , to separate