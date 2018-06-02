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
            if (request.form['action'] == "initialize"):
                result, log = plumb.CreateAIM(False)
                return(render_index(log))
            elif (request.form['action'] == "post" or request.form['action'] == "buy" or request.form['action'] == "sell"):
                plumb.Post(False)
                return(render_index("AIM system {0} saved.".format(request.form['action'])))

    except Exception as e:
        return (render_index(e))

    return(render_index(""))

def render_index(feedback):
    pid = plumb.get_pid("folder_daemon.py")
    if (pid == []):
        plumb.run_script("./folder_daemon.py")
        if (feedback == ""):
            feedback = "daemon started"
    l, table, db = plumb.Look(False)
    allocation_list, trends, lives = plumb.AllocationTrends(False)
    notes, initialize_day = plumb.GetAIMNotes(10, False)
    post_display = "post"
    initialize_prompt = ""
    if db == {} or initialize_day:
        post_display = "initialize"
        initialize_prompt = "You may reinitialize until tomorrow to make sure you have your portfolio balances the way you want."
    post_background = ""
    if not initialize_day:
        if "market order" in db:
            if (db['market order'] > 0):
                post_background = "background: blue;"
                post_display = "buy"
            if (db['market order'] < 0):
                post_background = "background: green;"
                post_display = "sell"
    balance_list = ""
    initial_value = ""
    profit_value = ""
    profit_percent = ""
    if "percent list" in l:
        balance_list = l['percent list']
        initial_value = l['initial value']
        profit_value = l['profit value']
        profit_percent = l['profit percent']
    return render_template('index.html', table = table, allocation_list = allocation_list, balance_list = balance_list,
        initial_value =  initial_value, profit_value = profit_value, profit_percent = profit_percent, notes = notes, feedback = feedback,
        post_display = post_display, post_background = post_background, initialize_prompt = initialize_prompt, trends = trends, lives = lives)

@app.route('/folder/', methods=["GET","POST"])
def folder():
    try:
        if request.method == "POST":
            if (request.form['action'] == "adjust"):
                if (request.form['options'] == "balance"):
                    if (request.form['balance'] == ""):
                        return(render_folder("display: none;", "balance is blank, cannot adjust.", ""))
                    else:
                        plumb.Balance(request.form['symbol'], request.form['balance'], False)
                        log =  "company {0}, balance is now {1}".format(request.form['symbol'], plumb.as_currency(plumb.to_number(request.form['balance'], False)))
                        return(render_folder("display: none;", log, ""))
                elif (request.form['options'] == "shares"):
                    if (request.form['balance'] == ""):
                        return(render_folder("display: none;", "shares are blank, cannot adjust.", ""))
                    else:
                        plumb.Shares(request.form['symbol'], request.form['balance'], False)
                        log =  "company {0}, shares are now {1}".format(request.form['symbol'], round(plumb.to_number(request.form['balance'], False), 4))
                        return(render_folder("display: none;", log, ""))
                else:
                    if (request.form['balance'] == ""):
                        return(render_folder("display: none;", "amount is blank, cannot adjust.", ""))
                    else:
                        curr_balance = CurrentBalance(request.form['symbol'], request.form['amount'])
                        balance = curr_balance + plumb.to_number(request.form['balance'], False)
                        log = "company {0}, balance {1}, adjusted by {2}.".format(request.form['symbol'], plumb.as_currency(curr_balance), plumb.as_currency(plumb.to_number(request.form['balance'], False)))
                        plumb.Balance(request.form['symbol'], str(balance), False)
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
    defaults, types = plumb.GetDefaults(False)
    folder_name = "folder"
    if ("folder name" in defaults):
        folder_name = defaults['folder name']
    table, symbol_options, balance_options, amount_options = plumb.PrintFolder(False)
    notes, initialize_day = plumb.GetAIMNotes(10, False)
    co = {}
    if (symbol > ""):
        co = plumb.Company(symbol, False)
        if not co:
            feedback = "symbol not found."
            ticker_style = "display: none;"

    return(render_template('folder.html', table = table,  ticker_style = ticker_style, symbol_options = symbol_options, balance_options = balance_options, notes = notes, ticker = co,
        feedback = feedback, amount_options = amount_options, folder_name = folder_name))
 
@app.route('/defaults/', methods=["GET","POST"])
def defaults():
    try:
        if request.method == "POST":
            if (request.form['action'] == "reset"):
                plumb.ResetDefaults(False)
                return (render_defaults("defaults have been reset."))
            elif (request.form['action'] == "update"):
                if request.form['column'] == "delete":
                    plumb.DeleteName(request.form['name'], False)
                    log = '"{0}" has been deleted.'.format(request.form['name'])
                elif request.form['column'] == "switch to":
                    plumb.UpdateDefaultItem("folder name", request.form['name'], False)
                    log = 'folder name has been switched to "{0}".'.format(request.form['name'])
                return (render_defaults(log))
            elif (request.form['action'] == "adjust"):
                if (request.form['value'] == ""):
                    log = "field is blank, cannot adjust."
                elif (request.form['column'] == "folder name" and not plumb.CheckPretty(request.form['value'])):
                    log = "folder name must be alphanumeric, cannot adjust."
                else:
                    plumb.UpdateDefaultItem(request.form['column'], request.form['value'], False)
                    log = "{0} has been updated.".format(request.form['column'])
                return (render_defaults(log))
            elif (request.form['action'] == "restart"):
                plumb.run_script("./folder_daemon.py")
            elif (request.form['action'] == "start"):
                plumb.run_script("./folder_daemon.py")

    except Exception as e:
        return (render_defaults(e))

    return(render_defaults(""))

def render_defaults(feedback):
    defaults, types = plumb.GetDefaults(False)
    alpha_vantage_key_warning = ""
    if ("alpha vantage key" in defaults):
        if (defaults['alpha vantage key'] == "" or defaults['alpha vantage key'] == "demo"):
            alpha_vantage_key_warning = "Remember to obtain your lifetime API key from Alpha Vantage, this is needed for polling the market prices"
    tradier_key_warning = ""
    if ("tradier key" in defaults):
        if (defaults['tradier key'] == "" or defaults['tradier key'] == "demo"):
            tradier_key_warning = "Remember to obtain your lifetime API key from tradier, this is needed for getting the market calendar"
    table, column_options, name_options, folder_options = plumb.PrintDefaults(False)
    hide_folder = ""
    if (name_options == ""):
        hide_folder = "hidden"
    notes, initialize_day = plumb.GetAIMNotes(10, False)
    pid = plumb.get_pid("folder_daemon.py")
    daemon_check = ""
    daemon_color = "green;"
    daemon_action = ""
    if (pid == []):
        daemon_check = "WARNING: folder_daemon.py is not running, your stocks are not updating, please start"
        daemon_color = "red;"
        daemon_action = "start"
    else:
        daemon_check = "folder daemon is running on pid: {0}".format(pid[0])
        daemon_action = "restart"       
    daemon_table, status = plumb.PrintDaemon("all", False)
    daemon_info = ""
    checkOpen = plumb.Holiday(False)
    if checkOpen:
        if (checkOpen['status'] == "closed"):
            daemon_info = checkOpen['description']
        else:
            daemon_info = "{0}, Last active status: {1}".format(checkOpen['description'], status)
    return (render_template('defaults.html', table = table, feedback = feedback, column_options = column_options, notes = notes, alpha_vantage_key_warning = alpha_vantage_key_warning,
        daemon_table = daemon_table, daemon_check = daemon_check, daemon_color = daemon_color, daemon_info = daemon_info, daemon_action = daemon_action,
        name_options = name_options, folder_options = folder_options, hide_folder = hide_folder, tradier_key_warning = tradier_key_warning))

@app.route('/history/', methods=["GET","POST"])
def history():
    try:
        if request.method == "POST":
            if (request.form['action'] == "all"):
                year_input = 1970
                year_string = "all"
                return (render_history("", year_string))
            elif (request.form['action'] == "export"):
                log = plumb.Export(request.form['column'], request.form['value'], False)
                return (render_history(log, ""))
            elif (request.form['action'] == "archive"):
                plumb.Archive(False)
                return (render_history("AIM system archived.", ""))
            elif (request.form['action'].isnumeric()):
                year_input = int(request.form['action'])
                if year_input < 100:
                    year_input += 2000
                year_string = str(year_input)
                return (render_history("", year_string))
            else:
                feedback = "input is not a year or the word all"
                return (render_history(feedback, ""))

    except Exception as e:
        return (render_history(e, ""))

    return(render_history("", ""))

def render_history(feedback, year_string):
    if (year_string == "" or year_string[0].lower() == 'a'):
        year_input = 1970
    else:
        year_input = int(year_string)
    notes, initialize_day = plumb.GetAIMNotes(10, False)
    table = plumb.PrintAIM(str(year_input), False)
    archive_table = plumb.PrintSummary(False)
    return render_template('history.html', table = table, notes = notes, feedback = feedback, archive_table = archive_table)

@app.route('/examples/')
def examples():
    return(render_examples())

def render_examples():
    return render_template('examples.html')

@app.route('/tests/')
def tests():
    return(render_tests())

def render_tests():
    resultFlag, test_stock = plumb.TestDefaults(True)
    resultFlag, test_folder = plumb.TestFolder(True)
    resultFlag, test_history = plumb.TestHistory(True)
    resultFlag, test_aim = plumb.TestAIM("aim", True)
    return render_template('tests.html', test_stock = test_stock, test_folder = test_folder, test_history = test_history, test_aim = test_aim)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

def CurrentBalance(symbol, string):
    amounts_list = ast.literal_eval(string)
    result = [element[1] for element in amounts_list if element[0] == symbol]
    return result[0]

if __name__ == "__main__":
	app.run()
