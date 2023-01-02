import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required#, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
# app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Configure CS50 Library to use SQLite database
# development sql database
db = SQL("sqlite:///database.db")
# deployment sql database
# db = SQL("sqlite:///wineApp.db")

# Global variables
# in case i want to edit, I want to access them in one spot
GLOBAL_CASH_POINTS_CONSTANT = 0


# Make sure API key is set
"""if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")"""


# code borrowed from finance.py
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """ Show the user profile page """
    query = "select * from users where id = ?;"
    user = db.execute(query, session["user_id"])
    if len(user) != 1:
        return render_template("login.html"), 400
    username = user[0]["username"]
    points = user[0]["points"]
    return render_template(
        "profile.html",
        points=points,
        username=username
    )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """List wines the user can buy """
    state = "not_filed"

    query = "select * from users where id = ?;"
    user = db.execute(query, session["user_id"])
    if len(user) != 1:
        return render_template("login.html"), 400
    username = user[0]["username"]
    points = user[0]["points"]

    query = "select * from wines;"
    wines = db.execute(query);
    num_rows = len(wines)

    if request.method == "POST":
        """ take the wine the user clicked and execute purchase """
        basket_price = 0
        item_prices = [float(wine["price"]) for wine in wines]
        str_quants = [request.form.get("quantity" + str(wine["id"])) for wine in wines]
        quantities = [int(str_quant) if str_quant != "" else 0 for str_quant in str_quants]
        total_prices = [item_prices[i] * quantities[i] for i in range(0, num_rows)]
        purchased = [1 if quantity > 0 else 0 for quantity in quantities]
        basket_price = sum(total_prices)

        points_earned = basket_price
        stripe_transaction = "stripe transaction placeholder string"
        query = "insert into baskets (user_id,basket_price,points_earned,transaction_date,stripe_transaction) values (?,?,?,current_timestamp,?);"
        db.execute(
            query,
            session["user_id"],
            basket_price,
            points_earned,
            stripe_transaction
        )
        query = "select points from users where id = ?"
        points = db.execute(query, session["user_id"])[0]["points"]
        points += points_earned
        query = "update users set points = ? where id = ? ;"
        db.execute(query, points, session["user_id"])
        query = "select max(id) as id from baskets;"
        basket_id = int(db.execute(query)[0]["id"])
        for i in range(0, num_rows):
            if purchased[i] == 1:
                query = "insert into purchases (basket_id,wine_id,quantity,item_price) values (?, ?, ?, ?);"
                db.execute(
                    query,
                    basket_id,
                    wines[i]["id"],
                    quantities[i],
                    item_prices[i]
                )
        # consider keeping the user on this page and giving them the feedback of purchase
        return redirect("/history")
    else:
        return render_template(
            "buy.html",
            state=state,
            wines=wines,
            username=username,
            points=points
        )


@app.route("/history")
@login_required
def history():
    """ Show purchase history, maybe also points and stuff """
    query = "select * from ((purchases inner join wines on wines.id = purchases.wine_id) inner join baskets on baskets.id = purchases.basket_id) where baskets.user_id = ?;"
    purchases = db.execute(query, session["user_id"])
    for purchase in purchases:
        purchase.update({"total" : purchase["price"] * purchase["quantity"] })
    query = "select * from users where id = ?;"
    user = db.execute(query, session["user_id"])
    if len(user) != 1:
        return render_template("login.html"), 400
    username = user[0]["username"]
    points = user[0]["points"]
    return render_template(
        "history.html",
        purchases=purchases,
        username=username,
        points=points
    )


@app.route("/baskets")
@login_required
def baskets():
    """ Show history in basket centered way, purchases + wines data shown in table and basket info outside"""
    """ I am considering rendering the wine details in specific way making cards instead of table rows """
    query = "select * from ((purchases inner join wines on wines.id = purchases.wine_id) inner join baskets on baskets.id = purchases.basket_id) where baskets.user_id = ?;"
    purchases = db.execute(query, session["user_id"])
    for purchase in purchases:
        purchase.update({"total" : purchase["price"] * purchase["quantity"] })
    query = "select * from users where id = ?;"
    user = db.execute(query, session["user_id"])
    if len(user) != 1:
        return render_template("login.html"), 400
    #i am considering making some functions around this
    baskets = {}
    for i in range(0, len(purchases)):
        basket_id = purchases[i]["basket_id"]
        if basket_id in baskets:
            # append purchase data to purchases
            # first we make the purchase variable
            purchase = {
                "name" : purchases[i]["name"],
                "brand" : purchases[i]["brand"],
                "class" : purchases[i]["class"],
                "country" : purchases[i]["country"],
                "region" : purchases[i]["region"],
                "volume" : purchases[i]["volume"],
                "alcohol" : purchases[i]["alcohol"],
                "year" : purchases[i]["year"],
                "quantity" : purchases[i]["quantity"],
                "item_price" : purchases[i]["item_price"],
                "total" : purchases[i]["quantity"] * purchases[i]["item_price"]
            }
            # we append it to the list of purchases
            # list is one of the fields in map basket["basket_id"]
            baskets[basket_id]["purchases"].append(purchase)
        else:
            # we make a new basket giving it basket specific fields
            # also we give it a list of purchases with the first purchase being this on
            # first we make a basket with an empty list of purchases
            basket = {
                "purchases" : [],
                "basket_price" : purchases[i]["basket_price"],
                "points_earned" : purchases[i]["points_earned"],
                "transaction_date" : purchases[i]["transaction_date"],
                "stripe_transaction" : purchases[i]["stripe_transaction"]
            }
            # now we make a purchase and append it
            purchase = {
                "name" : purchases[i]["name"],
                "brand" : purchases[i]["brand"],
                "class" : purchases[i]["class"],
                "country" : purchases[i]["country"],
                "region" : purchases[i]["region"],
                "volume" : purchases[i]["volume"],
                "alcohol" : purchases[i]["alcohol"],
                "year" : purchases[i]["year"],
                "quantity" : purchases[i]["quantity"],
                "item_price" : purchases[i]["item_price"],
                "total" : purchases[i]["quantity"] * purchases[i]["item_price"]
            }
            basket["purchases"].append(purchase)
            # now we put this basket into the map baskets
            baskets.update({basket_id : basket})
    # print(baskets)
    username = user[0]["username"]
    points = user[0]["points"]
    return render_template(
        "baskets.html",
        baskets=baskets,
        username=username,
        points=points
    )


@app.route("/manager", methods = ["GET", "POST"])
@login_required
def manager():
    """ Page for the operator to add items to the shopping list """
    if request.method == "POST":
        wine = {}
        wine["name"] = request.form.get("name")
        wine["class"] = request.form.get("class")
        wine["brand"] = request.form.get("brand")
        wine["country"] = request.form.get("country")
        wine["region"] = request.form.get("region")
        wine["volume"] = float(request.form.get("volume"))
        wine["alcohol"] = float(request.form.get("alcohol"))
        wine["year"] = int(request.form.get("year"))
        wine["price"] = float(request.form.get("price"))
        query = "insert into wines (name, class, brand, country, region, volume, alcohol, year, price) values (?, ?, ?, ?, ?, ?, ?, ?, ?);"
        db.execute(
            query,
            wine["name"],
            wine["class"],
            wine["brand"],
            wine["country"],
            wine["region"],
            wine["volume"],
            wine["alcohol"],
            wine["year"],
            wine["price"]
        )
        return render_template(
            "manager.html",
            state="",
            error_message=""
        )
    else:
        return render_template(
            "manager.html",
            state="",
            error_message=""
        )


@app.route("/login", methods = ["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html", state = "invalid"), 400

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()
    # code largely copied from the login since a lot footwork is the same
    # I change what I do if the username and password are a valid addition
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        # Ensure username was submitted
        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not password:
            # i am considering implementing some password rules
            # will implement if I have time and energy
            return render_template(
                "register.html",
                state = "invalid",
                error_message = "Must provide password!!!"
            ), 400

        # ensure confirmation of password is submitted
        elif not confirmation:
            return render_template(
                "register.html",
                state = "invalid",
                error_message = "Must provide confirmation!!!"
            ), 400

        # checking password and repeat password to match
        elif confirmation != password:
            return render_template(
                "register.html",
                state = "invalid",
                error_message = "Must match password and confirmation!!!"
            ), 400

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username exists and password is correct
        if len(rows) == 1:
            return render_template(
                "register.html",
                state = "invalid",
                error_message = "Username already in use!!!"
            ), 400

        hash = generate_password_hash(password, "sha256")

        points = GLOBAL_CASH_POINTS_CONSTANT

        query = "insert into users (username, hash, points) values (?, ?, ?);"
        db.execute(query, username, hash, points)

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    query = "select * from users where id = ?;"
    user = db.execute(query, session["user_id"])
    state = "not filled"
    if request.method == "POST":
        password = request.form.get("password")
        newpassword = request.form.get("newpassword")
        confirmation = request.form.get("confirmation")
        if not check_password_hash(user[0]["hash"], password):
            state = "incorrect"
            return render_template(
                "settings.html",
                username = user[0]["username"],
                state = state
            ), 400
        elif newpassword != confirmation:
            state = "no match"
            return render_template(
                "settings.html",
                username = user[0]["username"],
                state = state
            ), 400
        else:
            state = "match"
            hash = generate_password_hash(newpassword, "sha256")
            query = "update users set hash = ? where id = ?;"
            db.execute(query, hash, session["user_id"])
        return render_template(
            "settings.html",
            username = user[0]["username"],
            state = state
        )
    else:
        return render_template(
            "settings.html",
            username = user[0]["username"],
            state = state
        )


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")