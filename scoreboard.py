#!/usr/bin/env python

from flask import Flask
from flask import render_template
from flask import request
from datetime import datetime
import pdb

import plumb

app = Flask(__name__)

@app.route('/')
def index():
    l, table, db = plumb.Look(False)
    allocation_list = plumb.PrintPercent(False)
    note_list = plumb.GetAIMNotes(10, False)
    notes = []
    for n in note_list:
        note = Note(n['date'], n['content'])
        notes.append(note)
    return render_template('index.html', table = table, allocation_list = allocation_list, balance_list = l['percent list'],
        initial_value =  l['initial value'], profit_value = l['profit value'], profit_percent = l['profit percent'], notes = notes)

@app.route('/folder/', methods=["GET","POST"])
def folder():
    error = ''
    table, symbol_options, balance_options = plumb.PrintFolder(False)
    note_list = plumb.GetAIMNotes(10, False)
    notes = []
    for n in note_list:
        note = Note(n['date'], n['content'])
        notes.append(note)
    try:
        if request.method == "POST":
            if (request.form['action'] == "adjust"):
                print (request.form['action'])
            elif (request.form['action'][0:3] == "add"):
                plumb.Add(request.form['action'][4:] , False) 
                table, symbol_options, balance_options = plumb.PrintFolder(False)
                return render_template('folder.html', table = table,  ticker_style = "display: none;", symbol_options = symbol_options, balance_options = balance_options, notes = notes)
            elif (request.form['action'] != "Ticker symbol"):
                co = plumb.Company(request.form['action'], False)
                if not co:
                    return render_template('folder.html', table = table,  ticker_style = "display: none;", symbol_options = symbol_options, search_error = "symbol not found.", notes = notes)
                else:
                    return render_template('folder.html', table = table, ticker_symbol = co['symbol'], ticker_name = co['companyName'], ticker_description = co['description'],
                        ticker_exchange =  co['exchange'], ticker_industry =  co['industry'], ticker_website =  co['website'], ticker_ceo =  co['CEO'],
                        ticker_issuetype =  co['issueType'], ticker_sector =  co['sector'], ticker_style = "display: block;", symbol_options = symbol_options, add_symbol = co['symbol'], notes = notes)
            return redirect(url_for('folder'))

    except Exception as e:
        return render_template("folder.html", search_error = e) 

    return render_template('folder.html', table = table,  ticker_style = "display: none;", symbol_options = symbol_options, balance_options = balance_options, notes = notes)
 
@app.route('/defaults/')
def defaults():
    return render_template('defaults.html', table = plumb.PrintDefaults(False))

@app.route('/history/')
def history():
    dt = datetime.now()
    note_list = plumb.GetAIMNotes(10, False)
    notes = []
    for n in note_list:
        note = Note(n['date'], n['content'])
        notes.append(note)
    return render_template('history.html', table = plumb.PrintAIM(str(dt.year), False), year = str(dt.year), notes = notes)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

class Note(object):
    def __init__(self, date, content):
        self.date = date
        self.content = content

    def noteDate(self):
        dt = datetime.strptime(self.date, '%Y/%m/%d') 
        return custom_strftime('%B {S}, %Y', dt)

def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

if __name__ == "__main__":
	app.run()
