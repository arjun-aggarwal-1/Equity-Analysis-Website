import urllib.parse

import logging
logging.getLogger('matplotlib').setLevel(logging.WARNING)

from matplotlib import pyplot as plt
import pyEX as p
from flask import redirect, render_template, request, session
from functools import wraps

# Encode images
import base64
import io


global c
api_token='Tpk_c71760c664aa4e78840f9d6a9ccd27b4'

c = p.Client(api_token=api_token, version='stable')

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""
    try:
        data = c.quote(symbol=symbol)
        return {
            "name": data["companyName"],
            "price": float(data["latestPrice"]),
            "symbol": data["symbol"]
        }
    except:
        return None


def currency(symbol, value):
    """Format value as the respective currency."""
    return f"${value:,.2f}"

def graph1(symbol) :
    #data = pdr.get_data_yahoo(ticker, start, end)
    timeframe='1y'
    data = c.chartDF(symbol=symbol, timeframe=timeframe)[['close']]

    #Visualizing the fetched data
    plt.figure(figsize=(10, 5))
    plt.plot(data['close'])
    plt.title(symbol + ': Historical Stock Value')
    plt.xlabel('Date')
    plt.ylabel('Stock Price')
    my_stringIObytes = io.BytesIO()
    plt.savefig(my_stringIObytes, format='jpg', bbox_inches='tight')
    my_stringIObytes.seek(0)
    my_base64_jpgData = base64.b64encode(my_stringIObytes.read()).decode('ascii')
    return my_base64_jpgData

def graph2(symbol) :
    timeframe='1m'
    data = c.chartDF(symbol=symbol, timeframe=timeframe)[['close']]

    #Visualizing the fetched data
    plt.figure(figsize=(10, 5))
    plt.plot(data['close'])
    plt.title(symbol + ': Historical Stock Value')
    plt.xlabel('Date')
    plt.ylabel('Stock Price')
    my_stringIObytes = io.BytesIO()
    plt.savefig(my_stringIObytes, format='jpg', bbox_inches='tight')
    my_stringIObytes.seek(0)
    my_base64_jpgData = base64.b64encode(my_stringIObytes.read()).decode('ascii')
    return my_base64_jpgData

def graph3(symbol) :
    #data = pdr.get_data_yahoo(ticker, start, end)
    timeframe='1d'

    data = c.chartDF(symbol=symbol, timeframe=timeframe)[['close']]

    x=data.index
    a=[]
    for i in range(len(x)):
        y = x[i][1]
        z = x[i][0].replace(hour=int(y[:2]), minute=int(y[3:]))
        a.append(z)
    data.index = a
    data = data[data['close'] != 0]
    #Visualizing the fetched data
    plt.figure(figsize=(10, 5))
    plt.plot(data['close'])
    plt.title(symbol + ': Historical Stock Value')
    plt.xlabel('Date')
    plt.ylabel('Stock Price')
    my_stringIObytes = io.BytesIO()
    plt.savefig(my_stringIObytes, format='jpg', bbox_inches='tight')
    my_stringIObytes.seek(0)
    my_base64_jpgData = base64.b64encode(my_stringIObytes.read()).decode('ascii')
    return my_base64_jpgData

def graph_list(symbol):
    return [graph1(symbol),graph2(symbol),graph3(symbol)]

def tabs(symbol):
    return ["#"+symbol+"PY","#"+symbol+"PM","#"+symbol+"PD"]