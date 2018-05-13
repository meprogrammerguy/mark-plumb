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
    if (db['market order'] > 0):
        post_display = "buy"
    if (db['market order'] < 0):
        post_display = "sell"
    return render_template('index.html', table = table, allocation_list = allocation_list, balance_list = l['percent list'],
        initial_value =  l['initial value'], profit_value = l['profit value'], profit_percent = l['profit percent'], notes = notes, feedback = feedback, post_display = post_display)

@app.route('/folder/', methods=["GET","POST"])
def folder():
    try:
        if request.method == "POST":
            if (request.form['action'] == "adjust"):
                if (request.form['options'] == "balance"):
                    if (request.form['balance'] == ""):
                        return(render_folder("display: none;", "balance is blank.", ""))
                    else:
                        plumb.Balance(request.form['symbol'], float(request.form['balance']), False)
                        return(render_folder("display: none;", "balance updated.", ""))
                elif (request.form['options'] == "shares"):
                    if (request.form['balance'] == ""):
                        return(render_folder("display: none;", "shares is blank.", ""))
                    else:
                        plumb.Shares(request.form['symbol'], float(request.form['balance']), False)
                        return(render_folder("display: none;", "shares updated.", ""))
                else:
                    if (request.form['balance'] == ""):
                        return(render_folder("display: none;", "amount is blank.", ""))
                    else:
                        amounts = ast.literal_eval(request.form['amount'])
                        for item in amounts:
                            if (item[0] == request.form['symbol']):
                                amount = item[1]
                                break
                        balance = amount + float(request.form['balance'])
                        plumb.Balance(request.form['symbol'], balance, False)
                        return(render_folder("display: none;", "amount updated.", ""))
            elif (request.form['action'] == "remove"):
                plumb.Remove(request.form['symbol'], False)
                return(render_folder("display: none;", "company removed.", ""))
            elif (request.form['action'] == "add"):
                plumb.Add(request.form['symbol'], False) 
                return(render_folder("display: none;", "company added.", ""))
            elif (request.form['action'] != "Ticker symbol"):
                return(render_folder("display: block;", "", request.form['action']))

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
    dt = datetime.now()
    notes = plumb.GetAIMNotes(10, False)
    year_input = dt.year
    year_string = str(dt.year)
    feedback = ""
    history_style = "display: block;"
    try:
        if request.method == "POST":
            if (request.form['action'] == "all"):
                year_input = 1970
                year_string = "all"
            elif (request.form['action'] == "hide"):     #temporary hide code while developing page
                history_style = "display: none;"
            elif (request.form['action'].isnumeric()):
                year_input = int(request.form['action'])
                if year_input < 100:
                    year_input += 2000
                year_string = str(year_input)
            else:
                feedback = "input is not a year or the word all"
                return render_template("history.html", feedback = feedback, history_style = history_style)

    except Exception as e:
        return render_template("history.html", feedback = e, history_style = history_style) 

    return render_template('history.html', table = plumb.PrintAIM(str(year_input), False), year_string = year_string, notes = notes, feedback = feedback, history_style = history_style)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
	app.run()
