import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Global variables
# in case i want to edit, I want to access them in one spot
GLOBAL_CASH_CONSTANT = 10000

# Note to TA or professor
# i am looking at finance.cs50.net/ and I am trying to match their desing
# This was provided in the assignment documentation and I am using it
# as a guide
# later I may change some things around but for first try i am following
# Also the templates are all very similar, I just copy login.html and change
# i edit it so it matches what is see in my inspect element (in tha <main>)
# on finance.cs50.net
# this is also just better for me to test all the functionality as I can
# just compare

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


class Asset():
    def __init__(
        self,
        symbol,
        name,
        shares,
        price,
        total):
        self.symbol = symbol
        self.name = name
        self.shares = shares
        self.price = price
        self.total = total
# this is a class representing an asset so that I can pass it
# this should be like a struct in C


def enrich_asset(asset): # function takes asset and adds results form lookup
    search_result = lookup(asset["symbol"])
    name = search_result["name"]
    price = search_result["price"]
    symbol = search_result["symbol"]
    shares = asset["shares"]
    total = shares * price
    asset = Asset(
        symbol=symbol,
        name=name,
        shares=shares,
        price=price,
        total=total)
    return asset


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    #i must query for the stocks owned by user and feed them into jinja
    query = "select * from assets where user_id in(select id from users where id = ?);"
    assets = db.execute(query, session["user_id"])
    """ I must enrich the assets so it has the name of the stock,
    but nore importantly the current market price and the total value
    """

    assets = [enrich_asset(asset) for asset in assets]
    # I converted the asset form map to object Asset
    sum_assets = sum(asset.total for asset in assets)

    # I collect the cash value from users table
    query = "select cash from users where id = ?;"
    cash = db.execute(query, session["user_id"])[0]["cash"]
    cash = float(cash)
    total = sum_assets + cash

    return render_template(
        "portfolio.html",
        assets=assets,
        cash=cash,
        sum_assets=sum_assets,
        total=total
    )


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    state = "not filled"

    if request.method == "POST":
        symbol = request.form.get("symbol")
        stock = lookup(symbol)
        if stock != None:
            state = "quoted"
            return render_template(
                "quote.html",
                state = state,
                name = stock["name"],
                symbol = stock["symbol"],
                price = stock["price"]
            )
        else:
            # error will be presented
            state = "error"
            return render_template(
                "quote.html",
                state=state,
                name="",
                symbol=symbol,
                price=""
            ), 400
    else:
        return render_template(
            "quote.html",
            state=state,
            name="",
            symbol="",
            price=""
        )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    state = "not_filled"
    query = "select cash from users where id = ?;"
    cash = db.execute(query, session["user_id"])[0]["cash"]

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))
        stock = lookup(symbol)
        if stock != None:
            price = stock["price"]
            total = shares * price
            symbol = stock["symbol"]
            # lets check if they can afford it with volotility!
            if total * 1.01 <= cash:
                state = "can_buy"
                query = "select * from assets where user_id in(select id from users where id = ?) and symbol = ?;"
                # i have taken how many they have in their assets and added to shares (purchasing)
                asset = db.execute(query, session["user_id"], symbol)
                if len(asset) != 0:
                    query = "update assets set shares = ? where id in (select id from assets where user_id = ? and symbol = ?);"
                    db.execute(query, (shares + asset[0]["shares"]), session["user_id"], symbol)
                else:
                    # shares stays the value that is inputted because its new
                    query = "insert into assets (shares, user_id, symbol) values (?, ?, ?);"
                    db.execute(query, shares, session["user_id"], symbol)

                # i update the assets
                # i need to record the transaction
                query = "insert into history (user_id, symbol, shares, price, transacted) values (?, ?, ?, ?, current_timestamp);"
                db.execute(query, session["user_id"], symbol, shares, price)
                # i update the cash
                cash -= total
                query = "update users set cash = ? where id = ? ;"
                db.execute(query, cash, session["user_id"])
            else:
                state = "no_money"
                return render_template(
                    "buy.html",
                    state=state,
                    cash=cash
                ), 400
            return redirect("/")
        else:
            # error will be presented
            state = "error"
            return render_template(
                "buy.html",
                state=state,
                cash=cash
            ), 400
    else:
        return render_template(
            "buy.html",
            state=state,
            cash=cash)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    query = "select * from history where user_id in(select id from users where id = ?);"
    transactions = db.execute(query, session["user_id"])
    if len(transactions) == 0:
        return render_template(
            "history.html",
            transactions=transactions
        )
    else:
        return render_template(
            "history.html",
            transactions=transactions
        )


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # i must query for the stocks owned by user and feed them into jinja
    query = "select * from assets where user_id in(select id from users where id = ?);"
    assets = db.execute(query, session["user_id"])
    """ I must enrich the assets so it has the name of the stock,
    but nore importantly the current market price and the total value
    """
    state = "not_filled"

    query = "select cash from users where id = ?;"
    cash = db.execute(query, session["user_id"])[0]["cash"]

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))
        stock = lookup(symbol)
        if stock != None:
            price = stock["price"]
            total = shares * price
            symbol = stock["symbol"]

            query = "select * from assets where user_id in(select id from users where id = ?) and symbol = ?;"
            # i have taken how many they have in their assets and added to shares (purchasing)
            asset = db.execute(query, session["user_id"], symbol)
            if len(asset) != 0 and int(asset[0]["shares"]) >= shares:
                query = "update assets set shares = ? where id in (select id from assets where user_id = ? and symbol = ?);"
                state = "can_sell"

                # i update the assets
                db.execute(
                    query,
                    (asset[0]["shares"] - shares),
                    session["user_id"], symbol
                )
                # i need to record the transaction
                query = "insert into history (user_id, symbol, shares, price, transacted) values (?, ?, ?, ?, current_timestamp);"
                db.execute(
                    query,
                    session["user_id"],
                    symbol,
                    (- shares),
                    price
                )
                # i update the cash
                cash += total
                query = "update users set cash = ? where id = ? ;"
                db.execute(query, cash, session["user_id"])

                return redirect("/")
            else:
                state = "no_shares"
                return render_template(
                    "sell.html",
                    state=state,
                    shares=shares
                ), 400
        else:
            # error will be presented
            state = "error"
            return render_template(
                "sell.html",
                state=state,
                assets=assets
            ), 400
    else:
        return render_template(
            "sell.html",
            state=state,
            assets=assets
        )


@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    query = "select cash from users where id = ?;"
    cash = db.execute(query, session["user_id"])[0]["cash"]
    state = "not filled"
    if request.method == "POST":
        deposit = float(request.form.get("deposit"))

        if deposit > 0:
            # i update the cash
            cash += deposit
            query = "update users set cash = ? where id = ? ;"
            db.execute(query, cash, session["user_id"])
            # i need to record the transaction
            query = "insert into history (user_id, symbol, shares, price, transacted) values (?, ?, ?, ?, current_timestamp);"
            db.execute(
                query,
                session["user_id"],
                "deposit",
                1,
                deposit
            )
            state = "done"
        else:
            state = "negative"
        return render_template(
            "deposit.html",
            state=state,
            cash=cash
        )
    else:
        return render_template(
            "deposit.html",
            state=state,
            cash=cash
        )


@app.route("/login", methods=["GET", "POST"])
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
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


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
            return apology("must provide password", 400)

        # ensure confirmation of password is submitted
        elif not confirmation:
            return apology("must provide confirmation", 400)

        # checking password and repeat password to match
        elif confirmation != password:
            return apology("must match password and confirmation", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username exists and password is correct
        if len(rows) == 1:
            return apology("Username already in use", 400)

        hash = generate_password_hash(password, "sha256")

        cash = GLOBAL_CASH_CONSTANT

        query = "insert into users (username, hash, cash) values (?, ?, ?);"
        db.execute(query, username, hash, cash)

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
            username=user[0]["username"],
            state=state
        )
    else:
        return render_template(
            "settings.html",
            username=user[0]["username"],
            state=state
        )