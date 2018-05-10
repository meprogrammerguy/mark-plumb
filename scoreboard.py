#!/usr/bin/env python

from flask import Flask
from flask import render_template
from datetime import datetime
import json

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

@app.route('/folder/')
def folder():
    result = plumb.Company("AAPL", False)
    json_string = json.dumps(result)
    return render_template('folder.html', table = plumb.PrintFolder(False), ticker_company = json_string)

@app.route('/defaults/')
def defaults():
    return render_template('defaults.html', table = plumb.PrintDefaults(False))

@app.route('/history/')
def history():
    dt = datetime.now()
    return render_template('history.html', table = plumb.PrintAIM(str(dt.year), False), year = str(dt.year))

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
