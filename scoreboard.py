#!/usr/bin/env python

from flask import Flask
from flask import render_template

#app = Flask(__name__, static_folder='templates')
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/page/')
def page():
    return render_template('page.html',  title="Page")

@app.route('/another_page/')
def another_page():
    return render_template('another_page.html',  title="Another Page")

@app.route('/examples/')
def examples():
    return render_template('examples.html',  title="Examples")

@app.route('/contact/')
def contact():
    return render_template('contact.html',  title="Contact")

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
	app.run()
