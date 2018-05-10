#!/usr/bin/env python

from flask import Flask
from flask import render_template
import datetime

import plumb

app = Flask(__name__)

@app.route('/')
def index():
    l, table, db = plumb.Look(False)
    allocation_list = plumb.PrintPercent(False)
    return render_template('index.html', table = table, allocation_list = allocation_list, balance_list = l['percent list'],
        initial_value =  l['initial value'], profit_value = l['profit value'], profit_percent = l['profit percent'])

@app.route('/folder/')
def folder():
    return render_template('folder.html', table = plumb.PrintFolder(False))

@app.route('/defaults/')
def defaults():
    return render_template('defaults.html', table = plumb.PrintDefaults(False))

@app.route('/history/')
def history():
    dt = datetime.datetime.now()
    return render_template('history.html', table = plumb.PrintAIM(str(dt.year), False), year = str(dt.year))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
	app.run()
