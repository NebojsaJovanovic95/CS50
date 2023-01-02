# Wine Conosour
#### Video Demo:  https://youtu.be/PrsG2uUdyVA
#### Description:
TODO
Making a web app using python and flask
I will try to add some ajax and js for dynamicism


First steps:
I took the liberty to copy over the layout and login and register from my finance app assigment that I submitted
I will redesign it and make it look different, but i just like to have some structure
I am copying over the app.py for the routing of requests and of course I will change it to suit my app

So just for entry functionality, I am making the skeleton similar to what I was provided for assignment finance

My app will be a wine selling app.
#### Histoy, why I ended up making a wine app
I really wanted to implement MLP classifier that can classify some data.
And MLP classifier was my wish to implement, but as of starting this project, I am still programming my MLP.
Yes I know I can use pytorch or tensorflow, but where is the fun in that
The idea I had was to have a loaded and trianed MLP and have it classify data and I would later allow people to
submit their own MLP (or a spec of an MLP - weights biases activation functions).
Then I asked myself what data will I use, soon leading me to realise that I would be making a ML/NN project
and this is not a topic. I remembered using some wine data when I was following along some Udemy course on ML
and it occured to me that I should just work with some wine data and make a wine classifier.
This is when it occured to me that I could make an app that could classify wine. Now that is just pointless
and I concluded I should make a wine app where users can make profiles and purchase or learn about wine.
So a wine membership/purchassing web app is what I settled with. The MLP would be a nice addition that could make
the app a litle bit cooler, and would make some sense for like discovery of wines and so on.

So a wine web app that has memberships, purchases and some more features is the plan
it would be nice to implement a stripe integration for purchasses
Membership tier lists and rewards program

#### What I decide my app should be
So I set out to build out the skeleton for this app and then reexamined the scope and concluded
that just the basics should be enough
Maybe I expand on this in the future, maybe for CS50 Web and CS50 AI

#### The Final scope of the project

Make a user login and register
users are stored in users table and their id is used to link to their purchases

#### Tables
baskets, purchases, wines
have been made and the rule is:
Baskets have user_id which links it to the user who bought it, every basket has its own id as prim key
    baskets also have their basket_price and points_earned as well as transaction_date and
    stripe_transaction (unused). Only transaction_date is used and it is used for sorting.
    Points were there to keep track of rewards, but no reward was implemented
    stripe_transaction just gets a placeholder string, the idea was to enable future stripe api use
Wines are the items you can buy with their id as prim key
    it holds descriptions of the wine and the price
Each purhcase references a basket_id and wine_id and has the number of purchases of the given wine
    The item_price holds the price of the wine at the time of purchase this way when price changes
    the record will not change
    Each purhcase also has quantity which is how many of the given wine was bought in the given basket

In purchase history I would pull the data from excel by joining these 3 tables
```
select * from (
    (
        purchases inner join wines on wines.id = purchases.wine_id
    ) inner join baskets on baskets.id = purchases.basket_id
)
where baskets.user_id = ?;
```

in the basket view this data is reorganised to group by basket as described underneath

Baskets
```
bakets = map {basket_id : basket}
> for every basket_id --- this is better than using lists
basket = {
    "purchases" : purchases[] that belong in basket,
    "basket_price" : basket_price float value,
    "points_earned" : points_earned float value,
    "transaction_date" : transaction_date datetime preferably but maybe also string,
    stripe_transaction : stripe_transaction string
}

purchases = list of purchase
    where purchase is a map
    purchase = {
        "name" : name, "brand" : brand, and so on ...
    }
```
I first displayed the baskets as table for all purchases in the basket next and in seperate div
the general info for the basket


In history.html I display all the purchases in a table <tr> by <tr>
in baskets.html I have them organized as above and I have a more elaborate display that is
somewhat more pleasent to view


#### Buy page
I pull the data from wines and display it in a table along with some input cells so the customer
can choose how many bottles he will buy
> select * from wines;
The input cell has its id changed wiht jinja2 and that way I can target it in my python code
```
quantities = [int(str_quant) if str_quant != "" else 0 for str_quant in str_quants]
total_prices = [item_prices[i] * quantities[i] for i in range(0, num_rows)]
```

For buying I added some javascript to each <td> where the total would be updated automatically
as well as the basket total. This felt essential so that the user could see how much they were
spending.

#### Javascrip
```
<script>
document.getElementById("quantity{{ wine.id }}").onkeyup = function() {
    let sum = document.getElementById("basket_total").innerHTML;
    let this_total = document.getElementById("total{{ wine.id }}").innerHTML;
    // before updating anything I record the current basket_sum and the total that will be changing
    // then I take what needs to be the new total
    let new_total = this.value * {{ wine.price }};
    // I update the local total
    document.getElementById("total{{ wine.id }}").innerHTML = new_total;
    // I update the basket total as
    // old sum - old local total + new local total
    let new_sum = sum - this_total + new_total
    document.getElementById("basket_total").innerHTML = new_sum.toFixed(2);
    // this method save me from having to for loop through all inputs
}</script>
```

I ploped this script tag in every <td> where the total would be because I needed it to work for
every entry and the code would be somewhat different due to jinja2
It looks a littlebit frankenstein but it works like a charm
Note that the javascript is used only for display to the user, the final purhcase calc is done
from scratch in the python code. This means that you cant change your price of purchase.
Also, in order to update the basket price, I save the old price, save what was the total in the
given line then compute new total. I update the total for that wine and then
let new_sum = sum - this_total + new_total
allowing me to change the sum without looping over everithing which is both slow and also
very dificult with jinja2 generated html

#### Use of Jinja2
I realy tried to utilize the custom html page building using jinja2 and I used the
> {% for wine in wines %}
tags wherever I could. Also I used the
> {% for basket in baskets.values() | sort(attribute = 'transaction_date', reverse = True) %}
Which allows me to go through baskets and to sort them so the latest one shows at the top of the page