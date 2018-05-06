#!/usr/bin/env python

from flask import Flask
from flask import render_template

app = Flask(__name__, static_folder='templates')

@app.route('/')
def index(name=None):
    return render_template('index.html', name=name)

#@app.route('/page')
#def page(name=None):
#    return render_template('page.html', name=name)
