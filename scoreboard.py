#!/usr/bin/env python

from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/folder/')
def folder():
    return render_template('folder.html')

@app.route('/defaults/')
def defaults():
    return render_template('defaults.html')

@app.route('/examples/')
def examples():
    return render_template('examples.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
	app.run()
