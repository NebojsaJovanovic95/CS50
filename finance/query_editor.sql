CREATE TABLE users
(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL,
    cash NUMERIC NOT NULL DEFAULT 10000.00
);

create table history(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    user_id integer not null,
    symbol text not null,
    shares integer not null,
    price integer not null,
    transacted datetime
);

create table assets(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    user_id integer not null,
    symbol text not null,
    shares integer not null
);

--find user
select * from users where id = ?;

--adding a new user
insert into users (username, hash, cash) values (?, ?, ?);

--selection query for history uses the user_id which is found from session
select * from history
where user_id in(
    select id from users
    where username = ?
);
--session remembers the id from the database, no the sql
--it might be stupid to not just say where user_id = ?
--but I am being carefull
--like maybe user disapears or smthg
select * from history
where user_id in(
    select id from users
    where id = ?
);

--selection query for assets uses the user_id which is found from session
select * from assets
where user_id in(
    select id from users
    where username = ?
);
--session saves the id of the user not the actual username
select * from assets
where user_id in(
    select id from users
    where id = ?
);

select cash from users
where username = ?;

--session saves the id of the user not the actual username
select cash from users
where id = ?;

select * from assets
where user_id in(
    select id from users
    where id = ?
) and symbol = ?;


--update the asset value
update assets
set shares = ?
where id in (
    select id
    from assets
    where user_id = ?
    and symbol = ?
);

--insert new asset
insert into assets (user_id, symbol, shares)
values (?, ?, ?);

--insert new transaction
insert into history (user_id, symbol, shares, price, transacted)
values (?, ?, ?, ?, ?);

--update cash balance for user where id = sesssion["user_id"]
update users
set cash = ?
where id = ?;

--update password
update users
set hash = ?
where id = ?;