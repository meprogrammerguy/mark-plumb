#!/usr/bin/env python

from flask import Flask
from flask import render_template
from flask import request
from datetime import datetime
import pdb

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
        return render_template("index.html", feedback = e) 

    return(render_index(""))

def render_index(feedback):
    l, table, db = plumb.Look(False)
    allocation_list = plumb.PrintPercent(False)
    notes = plumb.GetAIMNotes(10, False)

    return render_template('index.html', table = table, allocation_list = allocation_list, balance_list = l['percent list'],
        initial_value =  l['initial value'], profit_value = l['profit value'], profit_percent = l['profit percent'], notes = notes, feedback = feedback)

@app.route('/folder/', methods=["GET","POST"])
def folder():
    try:
        if request.method == "POST":
            if (request.form['action'] == "adjust"):
                print (request.form['action'])
            elif (request.form['action'][0:3] == "add"):
                plumb.Add(request.form['action'][4:] , False) 
                return(render_folder("display: none;", "company added.", ""))
            elif (request.form['action'] != "Ticker symbol"):
                return(render_folder("display: block;", "", request.form['action']))

    except Exception as e:
        return render_template("folder.html", feedback = e) 

    return(render_folder("display: none;", "", ""))

def render_folder(ticker_style, feedback, symbol):
    table, symbol_options, balance_options = plumb.PrintFolder(False)
    notes = plumb.GetAIMNotes(10, False)
    co = {}
    if (symbol > ""):
        co = plumb.Company(symbol, False)
        if not co:
            feedback = "symbol not found."
            ticker_style = "display: none;"

    return(render_template('folder.html', table = table,  ticker_style = ticker_style, symbol_options = symbol_options, balance_options = balance_options, notes = notes, ticker = co,
        feedback = feedback))
 
@app.route('/defaults/')
def defaults():
    return render_template('defaults.html', table = plumb.PrintDefaults(False))

@app.route('/history/')
def history():
    dt = datetime.now()
    notes = plumb.GetAIMNotes(10, False)
    return render_template('history.html', table = plumb.PrintAIM(str(dt.year), False), year = str(dt.year), notes = notes)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
	app.run()
