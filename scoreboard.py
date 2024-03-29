#!/usr/bin/env python

from flask import Flask
from flask import render_template
from flask import request
from datetime import datetime
import os
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
    if os.name == 'nt':
        pid = plumb.get_pid("poll_stocks.py")
    else:
        pid = plumb.get_pid("folder_daemon.py")
    if (pid == []):
        if os.name == 'nt':
            plumb.run_script("poll_stocks.py")
        else:
            plumb.run_script("./folder_daemon.py")
        if (feedback == ""):
            feedback = "stock polling started"
    l, table, db = plumb.Look(False)
    trends, lives, percents = plumb.AllocationTrends(False)
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
    return render_template('index.html', table = table, balance_list = balance_list, initial_value =  initial_value, profit_value = profit_value,
        profit_percent = profit_percent, notes = notes, feedback = feedback, post_display = post_display, post_background = post_background,
        initialize_prompt = initialize_prompt, trends = trends, lives = lives, percents = percents)

@app.route('/folder/', methods=["GET","POST"])
def folder():
    try:
        if request.method == "POST":
            if "calculate" in request.form:
                if (request.form['calculate'] == "calculate"):
                    folder = plumb.GetFolder(False)
                    log = "Worksheet recalculated"
                    if folder != []:
                        values = []
                        for f in folder:
                            value = {}
                            if (f['symbol'] != "$"):
                                theText = 'box_{0}:{1}'.format(f['symbol'], f['crypto'])
                                value['symbol'] = f['symbol']
                                value['crypto'] = f['crypto']
                                value['adjust'] = request.form[theText]
                                values.append(value)
                        plumb.CalculateWorksheet(values, False)
                    else:
                        log = "Warning: Portfolio not found, cannot recalculate"
                return(render_folder("display: none;", log, "", ""))
            if (request.form['action'] == "adjust"):
                if (request.form['options'] == "calculations"):
                    plumb.PostWorksheet(False)
                    log =  "adjusted portfolio based on worksheet calculations"
                    return(render_folder("display: none;", log, "", ""))
                elif (request.form['options'] == "balance"):
                    if (request.form['balance'] == ""):
                        return(render_folder("display: none;", "balance is blank, cannot adjust.", "", ""))
                    else:
                        chunks = request.form['symbol'].split(',')
                        plumb.Balance(chunks[0], chunks[1], request.form['balance'], False)
                        log =  "company {0}, balance is now {1}".format(chunks[0], plumb.as_currency(plumb.to_number(request.form['balance'], False)))
                        return(render_folder("display: none;", log, "", ""))
                elif (request.form['options'] == "shares"):
                    if (request.form['balance'] == ""):
                        return(render_folder("display: none;", "shares are blank, cannot adjust.", "", ""))
                    else:
                        chunks = request.form['symbol'].split(',')
                        plumb.Shares(chunks[0], chunks[1], request.form['balance'], False)
                        log =  "company {0}, shares are now {1}".format(chunks[0], round(plumb.to_number(request.form['balance'], False), 8))
                        return(render_folder("display: none;", log, "", ""))
                else:
                    if (request.form['balance'] == ""):
                        return(render_folder("display: none;", "amount is blank, cannot adjust.", "", ""))
                    else:
                        chunks = request.form['symbol'].split(',')
                        curr_balance = CurrentBalance(chunks[0], chunks[1], request.form['amount'])
                        balance = curr_balance + plumb.to_number(request.form['balance'], False)
                        log = "company {0}, balance {1}, adjusted by {2}.".format(chunks[0], plumb.as_currency(curr_balance), plumb.as_currency(plumb.to_number(request.form['balance'], False)))
                        plumb.Balance(chunks[0], chunks[1], str(balance), False)
                        return(render_folder("display: none;", log, "", ""))
            elif (request.form['action'] == "remove"):
                s = request.form['remove_symbol']
                e = request.form['remove_type']
                plumb.Remove(s, e, False)
                log =  "company {0} has been removed from portfolio.".format(request.form['remove_symbol'])
                return(render_folder("display: none;", log, "", ""))
            elif (request.form['action'] == "add"):
                s = request.form['add_symbol']
                e = request.form['add_type']
                plumb.Add(s, e, False)
                log =  "company {0} has been added to portfolio.".format(s)
                return(render_folder("display: none;", log, "", ""))
            elif (request.form['action'] == "refresh"):
                plumb.Update(True, False)
                return(render_folder("display: none;", "prices updated.", "", ""))
            elif (request.form['action'] != "symbol"):
                s = request.form['action']
                flag = request.form['symbol']
                return(render_folder("display: block;", "", s, flag))
 
    except Exception as e:
        return (render_folder("display: none;", e, "", ""))

    return(render_folder("display: none;", "", "", ""))

def render_folder(ticker_style, feedback, symbol, flag):
    defaults, types = plumb.GetDefaults(False)
    folder_name = "folder"
    if ("folder name" in defaults):
        folder_name = defaults['folder name']
    symbol_options, balance_options, amount_options, items, keys = plumb.PrintFolder(False)
    notes, initialize_day = plumb.GetAIMNotes(10, False)
    co = {}
    if (symbol > ""):
        if (flag == "stock"):
            co = plumb.Company(symbol, False)
        if (flag == "crypto"):
            co = plumb.CryptoCompany(symbol, False)
        if not co:
            feedback = "symbol not found."
            ticker_style = "display: none;"
    worksheet_table, worksheet_warning = plumb.PrintWorksheet(False)
    worksheet_style = "display: none;"
    if worksheet_table > "":
        worksheet_style = "display: block;"

    return(render_template('folder.html', items = items, keys = keys, ticker_style = ticker_style, symbol_options = symbol_options, balance_options = balance_options, notes = notes, ticker = co,
        feedback = feedback, amount_options = amount_options, folder_name = folder_name, worksheet_table = worksheet_table, worksheet_style = worksheet_style, worksheet_warning = worksheet_warning))
 
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
            elif (request.form['action'] == "restart" or request.form['action'] == "start"):
                if os.name == 'nt':
                    plumb.run_script("poll_stocks.py")
                else:
                    plumb.run_script("./folder_daemon.py")

    except Exception as e:
        return (render_defaults(e))

    return(render_defaults(""))

def render_defaults(feedback):
    defaults, types = plumb.GetDefaults(False)
    tradier_key_warning = ""
    if ("tradier key" in defaults):
        if (defaults['tradier key'] == "" or defaults['tradier key'] == "demo"):
            tradier_key_warning = "Remember to obtain your lifetime API key from tradier, this is needed for getting the market calendar and quotes"
    IEX_key_warning = ""
    if ("IEX key" in defaults):
        if (defaults['IEX key'] == "" or defaults['IEX key'] == "demo"):
            IEX_key_warning = "Remember to obtain your lifetime API key from IEX cloud, this is needed for getting company ticker information"
    coin_key_warning = ""
    if ("coin key" in defaults):
        if (defaults['coin key'] == "" or defaults['coin key'] == "demo"):
            coin_key_warning = "Remember to obtain your lifetime API key from coin market cap, this is needed for getting cryptocoin information"
    table, column_options, name_options, folder_options = plumb.PrintDefaults(False)
    hide_folder = ""
    if (name_options == ""):
        hide_folder = "hidden"
    notes, initialize_day = plumb.GetAIMNotes(10, False)
    if os.name == 'nt':
        pid = plumb.get_pid("poll_stocks.py")
    else:
        pid = plumb.get_pid("folder_daemon.py")
    daemon_check = ""
    daemon_color = "green;"
    daemon_action = ""
    if (pid == []):
        daemon_check = "WARNING: stock polling is not running, your stocks are not updating, please start"
        daemon_color = "red;"
        daemon_action = "start"
    else:
        daemon_check = "stock polling is running on pid: {0}".format(pid[0])
        daemon_action = "restart"       
    daemon_table, status = plumb.PrintDaemon("all", False)
    daemon_info = ""
    checkOpen = plumb.Holiday(False)
    if checkOpen:
        if (checkOpen['status'] == "closed"):
            daemon_info = checkOpen['description']
        else:
            daemon_info = "{0}, Last active status: {1}".format(checkOpen['description'], status)
    return (render_template('defaults.html', table = table, feedback = feedback, column_options = column_options, notes = notes,
        daemon_table = daemon_table, daemon_check = daemon_check, daemon_color = daemon_color, daemon_info = daemon_info, daemon_action = daemon_action,
        name_options = name_options, folder_options = folder_options, hide_folder = hide_folder, tradier_key_warning = tradier_key_warning, IEX_key_warning = IEX_key_warning, coin_key_warning = coin_key_warning))

@app.route('/history/', methods=["GET","POST"])
def history():
    try:
        if request.method == "POST":
            if (request.form['action'] == "export"):
                log = plumb.Export(request.form['column'], request.form['value'], False)
                return (render_history(log))
            elif (request.form['action'] == "archive"):
                plumb.Archive(False)
                return (render_history("AIM system archived."))
            elif (request.form['action'] == "remove"):
                plumb.DeleteSnapshot(request.form['remove_snapshot'], False)
                log =  "snapshot {0} has been removed from archive.".format(request.form['remove_snapshot'])
                return(render_history(log))
            else:
                return (render_history(""))

    except Exception as e:
        return (render_history(e))

    return(render_history(""))

def render_history(feedback):
    notes, initialize_day = plumb.GetAIMNotes(10, False)
    table, export_options = plumb.PrintAIM("all", False)
    archive_table = plumb.PrintSummary(False)
    return render_template('history.html', table = table, notes = notes, feedback = feedback, archive_table = archive_table, export_options = export_options)

@app.route('/examples/')
def examples():
    return(render_examples())

def render_examples():
    return render_template('examples.html')

@app.route('/tests/')
def tests():
    return(render_tests())

def render_tests():
    count_pass = 0
    count_failures = 0
    count_total = 0

    testDefaults = plumb.TestDefaults(True, True)
    count_pass += testDefaults['pass']
    count_failures += testDefaults['fails']
    count_total += testDefaults['total']
    test_defaults = testDefaults['output']

    testFolder = plumb.TestFolder(True, True)
    count_pass += testFolder['pass']
    count_failures += testFolder['fails']
    count_total += testFolder['total']
    test_folder = testFolder['output']

    testCrypto = plumb.TestCrypto(True, True)
    count_pass += testCrypto['pass']
    count_failures += testCrypto['fails']
    count_total += testCrypto['total']
    test_crypto = testCrypto['output']

    testHistory = plumb.TestHistory(True, True)
    count_pass += testHistory['pass']
    count_failures += testHistory['fails']
    count_total += testHistory['total']
    test_history = testHistory['output']

    testAIM = plumb.TestAIM("aim", True, True)
    count_pass += testAIM['pass']
    count_failures += testAIM['fails']
    count_total += testAIM['total']
    test_aim = testAIM['output']

    testLow = plumb.TestLow(True, True)
    count_pass += testLow['pass']
    count_failures += testLow['fails']
    count_total += testLow['total']
    test_low = testLow['output']

    test_results = "{0} passes, {1} failures out of {2} total tests run.".format(count_pass, count_failures, count_total)
    test_color = "green;"
    if (count_failures > 0):
        test_color = "red;"
    return render_template('tests.html', test_defaults = test_defaults, test_folder = test_folder, test_crypto = test_crypto, test_history = test_history, test_aim = test_aim, test_results = test_results,
        test_color = test_color, test_low = test_low)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

def CurrentBalance(symbol, crypto, string):
    amounts_list = ast.literal_eval(string)
    result = [element[2] for element in amounts_list if (element[0] == symbol) and (element[1] == int(crypto))]
    return result[0]

if __name__ == "__main__":
    app.run()
