import os

from time import gmtime, strftime

from cs50 import SQL, eprint
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Ensure environment variable is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.route("/pwd", methods=["GET", "POST"])
@login_required
def pwd():
    # user try to change the password
    if request.method=="POST":
        # user must provide the old and new password as well as to confirm the new password
        pwd_0 = request.form.get("old_pwd")
        pwd = request.form.get("password")
        conf = request.form.get("confirmation")
        if not pwd_0 or not pwd or not conf:
            return apology("provide old and new password and confirm new password")
            # select the old hashed password and compare it to the old password the user typed in
        rows = db.execute("SELECT hash FROM users WHERE id = :id",
                                                                id=session.get("user_id"))
        # compare password
        for row in rows:
            hashh = row["hash"]
        if not check_password_hash(rows[0]["hash"], pwd_0):
            return apology("incorrect password")
        # confirm password
        elif pwd != conf:
            return apology("passwords don't match")
        # everything is ready then update the password
        db.execute("UPDATE users SET hash = :hah", hah=generate_password_hash(pwd))
        return redirect("/")
    else:
        return render_template("pwd.html")


@app.route("/add_cash", methods=["GET", "POST"])
@login_required
def add_cash():
    # user try to add some additional cash
    if request.method == "POST":
        cash = int(request.form.get("cash"))
        if not cash or cash < 0:
            return apology("please provide a positive number!")
        db.execute("UPDATE users SET cash = cash + :ca WHERE id = :id",
                                            ca=cash, id=session.get("user_id"))
        return redirect("/")
    else:
        return render_template("add_cash.html")


# implement a route that could alow user to change their password and add some additional cash
@app.route("/setting", methods=["GET", "POST"])
@login_required
def setting():
    if request.method == "POST":
        setting = request.form.get("setting")
        if not setting:
            return apology("chose what you want to set please!")
        # switch which way the user want to take either "password" or "cash" and send them the right route to continue the setting
        elif setting == "password":
            return redirect("/pwd")
        elif setting == "cash":
            return redirect("/add_cash")
    else:
        return render_template("setting.html")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # select cash and transaction of detail that we want to show to users
    cash = db.execute("SELECT cash FROM users WHERE id = :id", id=session.get("user_id"))
    rows = db.execute("SELECT symbol, price, shares, total FROM summ WHERE userId = :id",
                       id=session.get("user_id"))

    total = 0
    for row in rows:
        # change the price to current price
        row["price"] = lookup(row["symbol"])["price"]
        # obtain "total" by adding the total of each row iterately
        total += row["total"]
    # also add cash to "total"
    for ca in cash:
        cash = ca["cash"]
        total += cash
    return render_template("index.html", rows=rows, cash=usd(cash), total=usd(total), usd=usd)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # get the symbol,and shares user typed in
        symb = request.form.get("symbol")
        # check if the user filled the blank or not
        if not symb:
            return apology("provide symbol please!")

        # check the symbol via lookup() function
        symbo = lookup(symb)
        # if the symbol isn't valid do an apology
        if not symbo:
            return apology("invalid symbol!")
        # get the price of the stock
        price = symbo["price"]
        # get the symbol of the stock
        symbol = symbo["symbol"]
        share = request.form.get("shares")
        if not share:
            return apology("missing shares")
        n = 0
        for c in share:
            if c.isdigit():
                n += 1
        if n == len(share):
            # convert share to "int" type
            shares = int(share)

            if shares > 0:
                # figure out how much money does the user cost to buy the stock
                cash = price * shares
                # select the current cash the user has
                rows = db.execute("SELECT cash FROM users WHERE id = :id", id=session.get("user_id"))
                for row in rows:
                    # check if the user could afford the exchange
                    if row["cash"] < cash:
                        return apology("sorry, couldn't afford it!")
                    else:
                        # reduce cash from user and add stock to the user's portfolio
                        db.execute("UPDATE users SET cash = cash - :ca WHERE id = :id",
                                    ca=price * shares, id = session.get("user_id"))
                        # get the date and time when the transaction occurs
                        time = strftime("%Y-%m-%d  %H:%M:%S ", gmtime())
                        # add stock to user's portfolio
                        db.execute("INSERT INTO portfolio (userId, symbol, shares, price, time) VALUES(:id, :sy, :sh, :pr, :time)",
                                                                        id = session.get("user_id"), sy=symbol, sh=shares, pr=price, time=time)
                        # select the row in sql table(summ) where the stock belong to the current user and the symbol is get symbol("symbol")
                        items = db.execute("SELECT userId, symbol FROM summ WHERE userId = :id AND symbol = :symbol",
                                            id=session.get("user_id"), symbol=symbol)
                        # if that row dosen't exist then add it to table("summ")
                        if len(items) < 1:
                            db.execute("INSERT INTO summ (userId, symbol, shares, price, total) VALUES(:id, :sy, :sh, :pr, :tot)", id=session.get("user_id"), sy=symbol, sh=shares, pr=price, tot=shares * price)
                        # if the row exists then just update "shares" and "total" in that row
                        else:
                            db.execute("UPDATE summ SET shares = shares + :share WHERE symbol = :sy",
                                        sy=symbol, share=shares)
                            db.execute("UPDATE summ SET total = total + :tot WHERE symbol = :sy",
                                        sy=symbol, tot=shares * price)

                        # send user "index.html" where the page show him or her the summary of his or her transaction
                        return redirect("/")
            else:
                apology("positive integer only")
        else:
            return apology("positive integer only")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # select all we want show to the user from table "portfolio"
    rows = db.execute("SELECT symbol, shares, price, time FROM portfolio WHERE userId = :id",
                        id=session.get("user_id"))

    return render_template("history.html", rows=rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        # store whatever symbol the user typed in in "symbol"
        symbol = request.form.get("symbol")
        # check did the user fill the blank
        if not symbol:
            return apology("missing symbol!")
        # check whether the symbol is valid of not, if it's not valid do an apology,else send them the "quoted.html" page(which show them the current price of that symbol)
        quote = lookup(symbol)
        if not quote:
            return apology("invalid symbol!")
        return render_template("quoted.html", quote=quote, usd=usd)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # get whatever the user typed in
        name = request.form.get("username")
        pwd = request.form.get("password")
        cof = request.form.get("confirmation")
        # make sure the user filled each blank
        if not name or not pwd or not cof:
            return apology("Missing name or password!")
        # make sure the user confirmed the password
        elif pwd != cof:
            return apology("password isn't matched!")
        # hash password
        hash_pwd = generate_password_hash(pwd)
        # try to insert user's name and hashed password into "users"(which is a sql table)
        result = db.execute("INSERT INTO users (username,hash) VALUES(:username, :hash)",
                            username=name, hash=hash_pwd)
        # check if the username has already existed, if existed then do an apology
        if not result:
            return apology("Sorry the user name already exists!")
        # the user has been registered then send he or she the "index.html" page
        return redirect("/")
    # if the method is "GET",then show them the "register.html"
    else:
        return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        # get the symbol,and shares user typed in
        symb = request.form.get("symbol")
        # check if the user filled the blank or not
        if not symb:
            return apology("provide symbol please!")

        # check the symbol via lookup() function
        symbo = lookup(symb)
        if not symbo:
            return apology("can't sell it")

        # get the price and symbol of the stock
        price = symbo["price"]
        symbol = symbo["symbol"]

        share = request.form.get("shares")
        if not share:
            return apology("missing shares")
        n = 0
        for c in share:
            if c.isdigit():
                n += 1
        if n == len(share):
            shares = int(share)

            if shares > 0:
                # get the amount of money from the transaction
                cash = price * shares
                # record the date and time when the transaction occurs
                time = strftime("%Y-%m-%d  %H:%M:%S ", gmtime())
                # select the row that the user has that contains the "symbol" via "GET"

                items = db.execute("SELECT symbol, shares, price, total FROM summ WHERE userId = :id AND symbol = :sy",
                                    id=session.get("user_id"), sy=symbol)
                if len(items) != 1:
                    return apology("don't have this stock")
                else:

                    for item in items:
                        # check if the user have  enough stock to sell
                        if shares > item["shares"]:
                            return apology(" can't sell such a number of stocks!")
                        elif shares < item["shares"]:

                            # insert the transaction into the user's portfolio
                            db.execute("INSERT INTO portfolio (symbol, shares, price, time, userId) VALUES(:sy, :sh, :pr, :time, :id)",
                                        sy=symbol, sh=-shares, pr=price, time=time, id=session.get("user_id"))
                            # update the cash the user has
                            db.execute("UPDATE users SET cash = cash + :ca WHERE id = :id",
                                        ca = cash, id = session.get("user_id"))
                            # update the total and shares of that symbol
                            db.execute("UPDATE summ SET shares = shares - :sh WHERE symbol = :sy",
                                        sh = shares, sy = symbol)
                            db.execute("UPDATE summ SET total = total - :tot WHERE symbol = :sy",
                                        tot = shares * price, sy = symbol)
                        # if the user sell all the stock of the same symbol then delete it from the table "summ" and also update the data in sql tables
                        elif shares == item["shares"]:
                            db.execute("INSERT INTO portfolio (symbol, shares, price, time, userId) VALUES(:sy, :sh, :pr, :time, :id)",
                                        sy=symbol, sh=-shares, pr=price, time=time, id=session.get("user_id"))
                            db.execute("UPDATE users SET cash = cash + :ca WHERE id = :id",
                                        ca=cash, id=session.get("user_id"))
                            db.execute("DELETE FROM summ WHERE userId = :id AND symbol = :sy",
                                        id = session.get("user_id"), sy=symbol)
                        return redirect("/")
            else:
                apology("positive integer only")
        else:
            return apology("positive integer only")
    else:
        rows = db.execute("SELECT symbol FROM summ WHERE userId = :id",
                            id=session.get("user_id"))
        if len(rows) < 1:
            return apology("nothing to sell")
        else:
            return render_template("sell.html", rows=rows)


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
