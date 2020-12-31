import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

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

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    total = 0
    current = db.execute("SELECT * FROM current WHERE id = :userid", userid=session["user_id"])
    for i in range(len(current)):
        reader = lookup(current[i]["symbol"])
        current[i]["price"] = usd(reader["price"])
        current[i]["total"] = reader["price"] * current[i]["shares"]
        current[i]["usd_total"] = usd(current[i]["total"])
        total = total + current[i]["total"]
    cash = db.execute("SELECT cash FROM users WHERE id = :userid", userid=session["user_id"])
    usd_cash = float(cash[0]["cash"])
    money = usd(usd_cash + total)
    return render_template("index.html", current=current, usd_cash=usd(usd_cash), money=money)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # Give the form
    if request.method == "GET":
        return render_template("buy.html")
    else:
        symbol = request.form.get("symbol")
        reader = lookup(symbol)

        # No symbol
        if not symbol:
            return apology("You must provide the symbol of the stock", 403)

        # Invalid stock
        elif lookup(symbol) == None:
            return apology("The stock that you want to buy do not exist", 403)

        # No share
        share = int(request.form.get("share"))
        if not share:
            return apology("You must provide the number of share you want to buy", 403)

        # Invalid share
        elif share <= 0:
            return apology("Invalid share", 403)

        # check amount of cash
        cash = db.execute("SELECT cash FROM users WHERE id = :userid", userid=session["user_id"])
        shareprice = reader["price"] * share
        for row in cash:
            money = row["cash"]
        if money < shareprice:
            return apology("You do not have enough money to buy the stock", 403)

        # insert into transaction table
        db.execute("INSERT INTO record (id, symbol, name, shares, price) VALUES (:userid, :symbol, :name, :shares, :price)", userid=session["user_id"], symbol=reader["symbol"], name=reader["name"], shares=share, price=reader["price"])

        # update cash
        db.execute("UPDATE users SET cash = cash - :shareprice WHERE id = :userid", shareprice=shareprice, userid=session["user_id"])

        # check symbol
        check = db.execute("Select * FROM current WHERE id = :userid AND symbol = :symbol", userid=session["user_id"], symbol= reader["symbol"])
        if len(check) != 1:
            db.execute("INSERT INTO current (id, symbol, name, shares) VALUES (:userid, :symbol, :name, :share)", userid=session["user_id"], symbol=reader["symbol"], name=reader["name"], share=share)
        else:
            db.execute("UPDATE current SET shares = shares + :share WHERE id = :userid AND symbol = :symbol", share=share, userid=session["user_id"], symbol=reader["symbol"])
    return redirect("/")


@app.route("/change", methods=["GET", "POST"])
@login_required
def change():
    """Change password"""
    if request.method == "GET":
        return render_template("change.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")

        # No username
        if not username:
            return apology("You must provide a username", 403)

        # No password
        if not password:
            return apology("You must provide a password", 403)

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)

        # return apology if username or password incorrect
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("Invalid username and/or password", 403)

        # check new password
        new = request.form.get("new")
        if not new:
            return apology("You must provide your new password", 403)
        elif check_password_hash(rows[0]["hash"], new):
            return apology("You must provide a different password", 403)

        # check password confirmation
        confirmation = request.form.get("confirmation")
        if not confirmation:
            return apology("You must confirm your password", 403)
        elif confirmation != new:
            return apology("Your new passwords do not match", 403)

        # Update table
        db.execute("UPDATE users SET hash = :password WHERE id = :userid", password=generate_password_hash(new), userid=session["user_id"])
        return redirect("/")




@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # query the table
    rows = db.execute("SELECT * FROM record WHERE id = :userid", userid=session["user_id"])
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
    if request.method == "GET":
        return render_template("quote.html")
    else:
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("You must provide the symbol of the stock", 403)
        elif lookup(symbol) == None:
            return apology("The stock that you looked up do not exist", 403)
        else:
            reader = lookup(symbol)
            return render_template("quoted.html", company=reader["name"], price=usd(reader["price"]), symbol=reader["symbol"])


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        if not username:
            return apology("You must provide a username", 403)
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)
        if len(rows) == 1:
            return apology("The username already exists", 403)
        password = request.form.get("password")
        if not password:
            return apology("You must provide a password", 403)
        confirmation = request.form.get("confirmation")
        if not confirmation:
            return apology("You must confirm your password", 403)
        elif confirmation != password:
            return apology("Your passwords do not match", 403)
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :password)", username=username, password=generate_password_hash(password))
        return redirect("/")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # request action is get
    if request.method == "GET":
        rows = db.execute("SELECT symbol FROM current WHERE id = :userid", userid=session["user_id"])
        return render_template("sell.html", rows=rows)

    # request action is get
    else:
        symbol = request.form.get("symbol")
        reader = lookup(symbol)

        # no symbol provide
        if not symbol:
            return apology("You need to select a symbol", 403)

        # check share
        share = int(request.form.get("share"))
        find = db.execute("SELECT shares FROM current WHERE id = :userid AND symbol = :symbol", userid=session["user_id"], symbol=symbol)
        for row in find:
            check = row["shares"]
        if share > check:
            return apology("Too many shares", 403)
        elif share <= 0:
            return apology("Invalid share", 403)

        # update cash
        shareprice = reader["price"] * share
        db.execute("UPDATE users SET cash = cash + :shareprice WHERE id = :userid", shareprice=shareprice, userid=session["user_id"])
        # update table
        db.execute("UPDATE current SET shares = shares - :share WHERE id = :userid AND symbol = :symbol", share=share, userid=session["user_id"], symbol=reader["symbol"])
        # insert into record
        db.execute("INSERT INTO record (id, symbol, name, shares, price) VALUES (:userid, :symbol, :name, :shares, :price)", userid=session["user_id"], symbol=reader["symbol"], name=reader["name"], shares=-share, price=reader["price"])
        # delete row if there isn't any share
        db.execute("DELETE FROM current WHERE id = :userid AND shares = 0", userid=session["user_id"])
        return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
