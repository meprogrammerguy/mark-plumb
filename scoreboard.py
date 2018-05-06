#!/usr/bin/env python

from flask import Flask
from flask import render_template

app = Flask(__name__, static_folder='static', static_url_path='')

@app.route('/')
def index(name=None):
    return render_template('index.html', name=name)

@app.route('/page')
@app.route('/<name>/')
def page(name=None):
    return render_template('page.html', name=name)
