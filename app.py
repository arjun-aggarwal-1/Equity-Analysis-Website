from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpinglib import apology, login_required, lookup, currency, tabs, graph_list

import datetime as dt
import logging
import requests
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.getLogger('requests').setLevel(logging.DEBUG)



# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["currency"] = currency

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def home():
    """Show portfolio of stocks"""
    tally = tally_table()
    temp = {}
    graphs = {}
    tab={}
    total = 0
    for symbol in tally.keys():
        shares = tally[symbol]
        data = lookup(symbol)
        price = data["price"]
        name = data["name"]
        value = shares * price
        total += value
        temp[symbol] = (name, shares, currency(symbol,price), currency(symbol,value))
        graphs[symbol] = graph_list(symbol)
        tab[symbol]= tabs(symbol)

    return render_template("home.html", tally=temp, graphs=graphs,tab = tab)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add shares of stock"""
    if(request.method == "POST"):
        time = dt.datetime.now(dt.timezone.utc)
        uid = session["user_id"]
        symbol = request.form.get("symbol")
        data = lookup(symbol)
        if(data):
            try:
                shares = float(request.form.get("shares"))
            except:
                return apology("Positive integer values only")
            if(shares != int(shares)):
                return apology("Positive integer values only", 400)
            shares = int(shares)
            if(shares <= 0):
                return apology("Share to be bought must be a positive integer", 400)
            price = data["price"]
            try:
                graph_list(symbol)
            except:
                return apology("Invalid Symbol")
            db.execute("insert into history (uid, type,symbol, price, shares, time) values (?,?, ?, ?, ?, ?)",
                        uid, "Add", symbol, price, shares, time)
            temp = db.execute("select * from tally where uid=? and symbol=?", uid, symbol)
            if(len(temp) == 1):
                db.execute("update tally set shares=? where uid=? and symbol=?", shares+int(temp[0]["shares"]), uid, symbol)
            else:
                db.execute("insert into tally (uid,symbol,shares) values(?,?,?)", uid, symbol, shares)

            return(render_template("add.html", checker=1, symbol=symbol, shares=shares))
        return apology("Inavlid Symbol", 400)
    return render_template("add.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    data = db.execute("select type,symbol, price, shares, time from history where uid = ? order by time asc", session["user_id"])
    if(len(data) > 0):
        return render_template("history.html", data=data, checker=1)
    return render_template("history.html", data=data)


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
        rows = db.execute("select * from users where username = ?", request.form.get("username"))

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
    if(request.method == "POST"):
        symbol = request.form.get("symbol")
        answer = lookup(symbol)
        graphs = {}
        tab={}
        if(answer):
            try:
                graphs[symbol] = graph_list(symbol)
                tab[symbol]= tabs(symbol)
            except:
                return apology("Invalid symbol", 400)
            return render_template("quote.html", symbol=symbol, name=answer["name"], price=currency(symbol,answer["price"]), checker=1, temp=1, tab=tab, graphs=graphs)
        else:
            return apology("Invalid symbol", 400)
    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if(request.method == "POST"):

        usr = request.form.get("username")
        pwd = request.form.get("password")
        cpwd = request.form.get("confirmation")
        if(usr == ""):
            return apology("Blank username/password is not acceptable", 400)
        elif(len(db.execute("select username from users where username = ?", usr)) > 0):
            return apology("Username already exists", 400)
        if(pwd == ""):
            return apology("Blank username/passowrd is not acceptable", 400)
        elif(pwd != cpwd):
            return apology("Passwords do not match", 400)
        temp1 = 0
        temp2 = 0
        temp3 = 0
        temp4 = 0
        temp5 = 1
        for i in pwd:
            if(i.isupper()):
                temp1 = 1
                continue
            if(i.islower()):
                temp2 = 1
            if(i.isnumeric()):
                temp3 = 1
            if(i == " "):
                temp5 = 0
            if(not i.isalnum()):
                temp4 = 1
        if(temp1 == 1 and temp2 == 1 and temp3 == 1 and temp4 == 1 and temp5 == 1 and len(pwd) >= 8 and len(pwd) <= 16):

            db.execute('insert into users(username,hash) values(?,?)', usr, generate_password_hash(pwd))
            rows = db.execute("select * from users where username = ?", usr)

            session["user_id"] = rows[0]["id"]

            return redirect("/")
        else:
            return apology("Password must contain at least one uppercase letter, one lowercase letter, one number, one symbol, no spaces and should be 8-16 characters long", 403)
    return render_template("register.html")


@app.route("/remove", methods=["GET", "POST"])
@login_required
def remove():
    """Remove shares of stock"""
    tally = tally_table()
    if(request.method == "POST"):
        time = dt.datetime.now(dt.timezone.utc)
        uid = session["user_id"]
        symbol = request.form.get("symbol")
        try:
            old_shares = tally[symbol]
        except:
            old_shares = 0
        data = lookup(symbol)
        if(data):
            try:
                shares = int(request.form.get("shares"))
            except:
                return apology("Positive integer values only", 400)
            if(shares != int(shares)):
                return apology("Positive integer values only", 400)
            shares = int(shares)
            if(old_shares < shares):
                return apology("Shares to be removed must be less than original shares")
            if(shares <= 0):
                return apology("Share should to be removed must be a positive integer", 400)
            price = data["price"]
            db.execute("insert into history (uid, type,symbol, price, shares, time) values (?,?, ?, ?, ?, ?)",
                        uid, "Remove", symbol, price, shares, time)
            if(old_shares == shares):
                db.execute("delete from tally where uid=? and symbol=?", uid, symbol)
            else:
                db.execute("update tally set shares=? where uid=? and symbol=?", old_shares-shares, uid, symbol)
            return render_template("remove.html",checker=1)
        return apology("Invalid Input", 400)  # will probably never be caused
    return render_template("remove.html", tally=tally)


def tally_table():
    uid = session["user_id"]
    tally = {}
    data = db.execute("select symbol, shares from tally where uid = ?", uid)
    for d in data:
        symbol = d["symbol"]
        shares = d["shares"]
        if(shares > 0):
            tally[symbol] = shares
    return tally

db.execute("CREATE TABLE if not exists users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL);")

db.execute("CREATE UNIQUE INDEX if not exists username ON users (username);")
db.execute("CREATE TABLE IF NOT EXISTS tally (id integer primary key AUTOINCREMENT not null, uid NUMERIC NOT NULL, symbol text not null, shares numeric not null, FOREIGN KEY(uid) REFERENCES users(id))")
db.execute("create table if not exists history (id integer primary key AUTOINCREMENT not null, uid numeric not null, type varchar(5) not null, symbol text not null, price numeric not null, shares numeric not null, time text not null, FOREIGN KEY(uid) REFERENCES users(id))")