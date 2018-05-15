#!/usr/bin/env python

from flask import Flask
from flask import render_template
from flask import request
from datetime import datetime
import pdb
import ast

import plumb

app = Flask(__name__)

@app.route('/', methods=["GET","POST"])
def index():
    try:
        if request.method == "POST":
            if (request.form['action'] == "post" or request.form['action'] == "buy" or request.form['action'] == "sell"):
                plumb.Post(False)
                return(render_index("{0} saved.".format(request.form['action'])))

    except Exception as e:
        return (render_folder(feedback))

    return(render_index(""))

def render_index(feedback):
    l, table, db = plumb.Look(False)
    allocation_list = plumb.PrintPercent(False)
    notes = plumb.GetAIMNotes(10, False)
    post_display = "post"
    post_background = ""
    if (db['market order'] > 0):
        post_background = "background: blue;"
        post_display = "buy"
    if (db['market order'] < 0):
        post_background = "background: green;"
        post_display = "sell"
    return render_template('index.html', table = table, allocation_list = allocation_list, balance_list = l['percent list'],
        initial_value =  l['initial value'], profit_value = l['profit value'], profit_percent = l['profit percent'], notes = notes, feedback = feedback,
        post_display = post_display, post_background = post_background)

@app.route('/folder/', methods=["GET","POST"])
def folder():
    try:
        if request.method == "POST":
            if (request.form['action'] == "adjust"):
                if (request.form['options'] == "balance"):
                    if (request.form['balance'] == ""):
                        return(render_folder("display: none;", "balance is blank, cannot adjust.", ""))
                    else:
                        plumb.Balance(request.form['symbol'], float(request.form['balance']), False)
                        log =  "company {0}, balance is now {1}".format(request.form['symbol'], as_currency(float(request.form['balance'])))
                        return(render_folder("display: none;", log, ""))
                elif (request.form['options'] == "shares"):
                    if (request.form['balance'] == ""):
                        return(render_folder("display: none;", "shares are blank, cannot adjust.", ""))
                    else:
                        plumb.Shares(request.form['symbol'], float(request.form['balance']), False)
                        log =  "company {0}, shares are now {1}".format(request.form['symbol'], round(float(request.form['balance']), 4))
                        return(render_folder("display: none;", log, ""))
                else:
                    if (request.form['balance'] == ""):
                        return(render_folder("display: none;", "amount is blank, cannot adjust.", ""))
                    else:
                        curr_balance = CurrentBalance(request.form['symbol'], request.form['amount'])
                        balance = curr_balance + float(request.form['balance'])
                        log = "company {0}, balance {1}, adjusted by {2}.".format(request.form['symbol'], as_currency(curr_balance), as_currency(float(request.form['balance'])))
                        plumb.Balance(request.form['symbol'], balance, False)
                        return(render_folder("display: none;", log, ""))
            elif (request.form['action'] == "remove"):
                plumb.Remove(request.form['remove_symbol'], False)
                log =  "company {0} has been removed from portfolio.".format(request.form['remove_symbol'])
                return(render_folder("display: none;", log, ""))
            elif (request.form['action'] == "add"):
                s = request.form['add_symbol']
                plumb.Add(s, False)
                log =  "company {0} has been added to portfolio.".format(s)
                return(render_folder("display: none;", log, ""))
            elif (request.form['action'] != "Ticker symbol"):
                s = request.form['action']
                return(render_folder("display: block;", "", s))

    except Exception as e:
        return (render_folder("display: none;", e, ""))

    return(render_folder("display: none;", "", ""))

def render_folder(ticker_style, feedback, symbol):
    table, symbol_options, balance_options, amount_options = plumb.PrintFolder(False)
    notes = plumb.GetAIMNotes(10, False)
    co = {}
    if (symbol > ""):
        co = plumb.Company(symbol, False)
        if not co:
            feedback = "symbol not found."
            ticker_style = "display: none;"

    return(render_template('folder.html', table = table,  ticker_style = ticker_style, symbol_options = symbol_options, balance_options = balance_options, notes = notes, ticker = co,
        feedback = feedback, amount_options = amount_options))
 
@app.route('/defaults/')
def defaults():
    return render_template('defaults.html', table = plumb.PrintDefaults(False))

@app.route('/history/', methods=["GET","POST"])
def history():
    try:
        if request.method == "POST":
            if (request.form['action'] == "all"):
                year_input = 1970
                year_string = "all"
                return (render_history("display: block;", "", year_string))
            elif (request.form['action'] == "hide"):     #temporary hide code while developing page
                return (render_history("display: none;", "hiding help HTML, remove this at release time", "all"))
            elif (request.form['action'].isnumeric()):
                year_input = int(request.form['action'])
                if year_input < 100:
                    year_input += 2000
                year_string = str(year_input)
                return (render_history("display: block;", "", year_string))
            else:
                feedback = "input is not a year or the word all"
                return (render_history("display: block;", feedback, ""))

    except Exception as e:
        return (render_history("display: block;", e, ""))

    return(render_history("display: block;", "", ""))

def render_history(history_style, feedback, history_year):
    if (history_year == ""):
        dt = datetime.now()
        year_input = dt.year
        year_string = str(dt.year)
    elif (history_year[0].lower() == 'a'):
        year_input = 1970
        year_string = "all"
    else:
        year_string = history_year
        year_input = int(year_string)
    notes = plumb.GetAIMNotes(10, False)
    return render_template('history.html', table = plumb.PrintAIM(str(year_input), False), year_string = year_string, notes = notes, feedback = feedback, history_style = history_style)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

def CurrentBalance(symbol, string):
    amounts_list = ast.literal_eval(string)
    result = [element[1] for element in amounts_list if element[0] == symbol]
    return result[0]

def as_currency(amount):
    if (amount is None):
        amount = 0
    if amount >= 0:
        return '${:,.2f}'.format(amount)
    else:
        return '(${:,.2f})'.format(-amount)   

if __name__ == "__main__":
	app.run()
