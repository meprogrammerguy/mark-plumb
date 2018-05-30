#!/usr/bin/env python3

import pdb
from bs4 import BeautifulSoup
import html5lib
import contextlib
import urllib.request
import json
import os
from pathlib import Path
import sqlite3
from sqlite3 import Error
import getpass
import time
import datetime
import re
import csv
import math
from flask_table import create_table, Table, Col
import pprint
import pyperclip
import pytz
from dateutil import tz
import subprocess
import signal
from tkinter import *
from tkinter import filedialog
import http.client
from dateutil.tz import tzlocal
from tzlocal import get_localzone

#region stock
def Quote(ticker, verbose):
    result = {}
    defaults, types = GetDefaults(verbose)
    url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={0}&apikey={1}".format(ticker, defaults['alpha vantage key'])
    if (verbose):
        print ("***")
        print ("Quote(1) ticker: {0}".format(ticker))
        print ("Quote(2) key: {0}".format(defaults['alpha vantage key']))
        print ("Quote(3) URL: {0}".format(url))
    try:
        with contextlib.closing(urllib.request.urlopen(url)) as page:
            soup = BeautifulSoup(page, "html5lib")
    except urllib.error.HTTPError as err:
        result['exception'] = err
        result['status'] = False
        result['url'] = url
        if err.code == 404:
            if (verbose):
                print ("Quote(4) page not found for {0}".format(ticker))
                print ("***\n")
            return result
        elif err.code == 503:
            if (verbose):
                print ("Quote(5) service unavailable for {0}".format(ticker))
                print ("***\n")
            return result
        else:
            raise
    returnQuote = json.loads(str(soup.text))
    if (verbose):
        print ("***\n")
    closing = {}
    if (returnQuote):
        for keys, values in returnQuote.items():
            if (keys == "Error Message"):
                closing = returnQuote
                break
            if (keys != "Meta Data"):
                for key, value in values.items():
                    dt = datetime.datetime.strptime(key, '%Y-%m-%d')
                    closing['price time'] = dt.strftime('%m/%d/%y')
                    closing['price'] =  value['4. close']
                    break
        if "Meta Data" in returnQuote:
            closing['symbol'] = returnQuote['Meta Data']['2. Symbol']
            closing['status'] = True
        else:
            closing['exception'] = returnQuote
            closing['status'] = False
    closing['url'] = url
    return closing

def Holiday(verbose):
    url = "/v1/markets/calendar"
    if (verbose):
        print ("***")
        print ("Holiday(1) URL: {0}".format(url))
    opentime = MarketToTime("09:30", "US/Eastern", verbose)
    closetime = MarketToTime("16:00", "US/Eastern", verbose)
    dt = datetime.datetime.now()
    today = dt.strftime('%Y-%m-%d')
    defaults, types = GetDefaults(verbose)
    if ("market status" in defaults):
        js = json.loads(defaults['market status'])
        if "date" in js:
            if js['date'] == today:
                return js

    connection = http.client.HTTPSConnection('sandbox.tradier.com', 443, timeout = 30)

    headers = {}
    headers["Accept"] = "application/json"
    headers["Authorization"] = "Bearer {0}".format(defaults["tradier key"])
    headers["connection"] = "close"

    connection.request('GET', url, None, headers)
    try:
        response = connection.getresponse()
        content = response.read()
        returnContent = json.loads(content)
    except http.client.HTTPException as e:
        print('Exception {0} during request').format(e)
    if (verbose):
        print ("***\n")
    answer = {}
    for itm in returnContent['calendar']['days']['day']:
        if (itm['date'] == today):
            answer = itm
            break
    UpdateDefaultItem("market status", answer, verbose)
    if "open" in answer:
        opentime = MarketToTime(answer['open']['start'], "US/Eastern", verbose)
        closetime = MarketToTime(answer['open']['end'], "US/Eastern", verbose)
        UpdateDefaultItem("open", opentime, verbose)
        UpdateDefaultItem("close", closetime, verbose)
    else:
        UpdateDefaultItem("open", None, verbose)
        UpdateDefaultItem("close", None, verbose) 
    return answer

def Company(ticker, verbose):
    url = "https://api.iextrading.com/1.0/stock/{0}/company".format(ticker)
    if (verbose):
        print ("***")
        print ("Company(1) ticker: {0}".format(ticker))
        print ("Company(2) URL: {0}".format(url))
    try:
        with contextlib.closing(urllib.request.urlopen(url)) as page:
            soup = BeautifulSoup(page, "html5lib")
    except urllib.error.HTTPError as err:
        if err.code == 404:
            if (verbose):
                print ("Company(3) page not found for {0}".format(ticker))
                print ("***\n")
            return {}
        else:
            raise
    returnCompany = json.loads(str(soup.text))
    if (verbose):
        print ("***\n")
    return returnCompany

def UpdateDefaultItem(key, item, verbose):
    key_db = key.replace(" ", "_")
    d, t = GetDefaults(verbose)
    if (key_db == "market_status"):
       item = json.dumps(item)
    if (verbose):
        print ("***")
    if (key not in d):
        if (verbose):
            print ("UpdateDefaultItem(1) Error key: {0} is not in the defaults dbase".format(key))
        return False
    username = getpass.getuser()
    db_file = os.getcwd() + "/"  + "defaults.db"
    if (verbose):
        print ("UpdateDefaultItem(2) key: {0}".format(key))
        print ("UpdateDefaultItem(3) value: {0}".format(item))
        print ("UpdateDefaultItem(4) type: {0}".format(t[key]))
        print ("UpdateDefaultItem(5) dbase: {0}".format(db_file))
    result = CreateDefaults(verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("UpdateDefaultItem(6) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("UpdateDefaultItem(7) {0}".format(e))
            return False
        c = conn.cursor()
        query = ""
        if (t[key] == "INTEGER" or t[key] == "REAL"):
            query = "UPDATE defaults SET {0} = ? WHERE username = (?)".format(key_db)
            c.execute(query, (item, username,))
        else:
            query = "UPDATE defaults SET {0} = (?) WHERE username = (?)".format(key_db)
            c.execute(query, (item, username,))
        conn.commit()
        conn.close()
        if (key == "folder name"):
            CreateNames(item, verbose)
    if (verbose):
        print ("***\n")
    return True

def ResetDefaults(verbose):
    username = getpass.getuser()
    db_file = os.getcwd() + "/"  + "defaults.db"
    if (verbose):
        print ("***")
        print ("ResetDefaults(1) dbase: {0}".format(db_file))
    result = CreateDefaults(verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("ResetDefaults(2) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("ResetDefaults(3) {0}".format(e))
            return False
        opentime = MarketToTime("09:30", "US/Eastern", verbose)
        closetime = MarketToTime("16:00", "US/Eastern", verbose)
        desktop = "/home/{0}/Desktop".format(getpass.getuser())
        c = conn.cursor()
        c.execute("UPDATE defaults SET alpha_vantage_key = (?) WHERE username = (?)", ("demo", username,))
        c.execute("UPDATE defaults SET tradier_key = (?) WHERE username = (?)", ("demo", username,))
        c.execute("UPDATE defaults SET daemon_seconds = ? WHERE username = (?)", (300, username,))
        c.execute("UPDATE defaults SET open = (?) WHERE username = (?)", (opentime, username,))
        c.execute("UPDATE defaults SET close = (?) WHERE username = (?)", (closetime, username,))
        c.execute("UPDATE defaults SET test_root = (?) WHERE username = (?)", ("test/", username,))
        c.execute("UPDATE defaults SET export_dir = (?) WHERE username = (?)", (desktop, username,))
        c.execute("UPDATE defaults SET folder_name = (?) WHERE username = (?)", ("Practice Portfolio", username,))
        c.execute("UPDATE defaults SET market_status = (?) WHERE username = (?)", ("{}", username,))
        conn.commit()
        conn.close()
        CreateNames("Practice Portfolio", verbose)
    if (verbose):
        print ("***\n")
    return True

def MarketToTime(theTime, theZone, verbose):
    dt = datetime.datetime.now()
    today = dt.strftime('%m/%d/%Y')
    datestring = "{0} {1}:00".format(today, theTime)
    date=dt.strptime(datestring,"%m/%d/%Y %H:%M:%S")
    utc=pytz.utc
    zone=pytz.timezone(theZone)
    local_tz = get_localzone() 
    date_est=zone.localize(date,is_dst=None)
    date_utc=date_est.astimezone(utc)
    date_local = date_utc.astimezone(local_tz)
    return date_local.strftime("%I:%M%p")

def GetDefaults(verbose):
    username = getpass.getuser()
    db_file = os.getcwd() + "/"  + "defaults.db"
    if (verbose):
        print ("***")
        print ("GetDefaults(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("GetDefaults(2) {0} file is missing, cannot return the key".format(db_file))
            print ("***\n")
        return "", ""
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("GetDefaults(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("GetDefaults(4) {0}".format(e))
        return "", ""
    c = conn.cursor()
    c.execute("SELECT * FROM defaults WHERE username = (?) order by username", (username,))
    keys = list(map(lambda x: x[0].replace("_"," "), c.description))
    values = c.fetchone()
    c.execute('PRAGMA TABLE_INFO(defaults)')
    types = [tup[2] for tup in c.fetchall()]
    conn.close()
    answer = dict(zip(keys, values))
    answer_types = dict(zip(keys, types))
    if (verbose):
        print ("***\n")
    return answer, answer_types

def CreateDefaults(verbose):
    username = getpass.getuser()
    db_file = os.getcwd() + "/"  + "defaults.db"
    if (verbose):
        print ("***")
        print ("CreateDefaults(1) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("CreateDefaults(2) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("CreateDefaults(3) {0}".format(e))
        return False
    c = conn.cursor()
    c.execute("CREATE TABLE if not exists 'defaults' ( `username` TEXT NOT NULL UNIQUE, `folder_name` TEXT, `open` TEXT, `close` TEXT, `daemon_seconds` INTEGER, `test_root` TEXT, `export_dir` TEXT, `alpha_vantage_key` TEXT, `tradier_key` TEXT, `market_status` TEXT, PRIMARY KEY(`username`) )")
    c.execute( "INSERT OR IGNORE INTO defaults(username) VALUES((?))", (username,))
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    return True

def PrintDefaults(verbose):
    username = getpass.getuser()
    db_file = os.getcwd() + "/"  + "defaults.db"
    if (verbose):
        print ("***")
        print ("PrintDefaults(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("PrintDefaults(2) {0} file is missing, cannot print".format(db_file))
            print ("***\n")
        return "", "", ""
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("PrintDefaults(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("PrintDefaults(4) {0}".format(e))
        return "", "", ""
    c = conn.cursor()
    c.execute("SELECT * FROM defaults order by username")
    keys = list(map(lambda x: x[0].replace("_"," "), c.description))
    rows = c.fetchall()
    conn.commit()
    conn.close()
    names = GetNames(verbose)
    column_options = ""
    TableCls = create_table('TableCls')
    for key in keys:
        if (key != "username"):
            column_options += '<option value="{0}">{1}</option>'.format(key, key)
        TableCls.add_column(key, Col(key))
    items = []
    answer = {}
    for row in rows:
        col_list = []
        for i in range(len(row)):
            if (i == 7 or i == 8):
                if row[i] == "demo" or row[i] == "":
                    col_list.append(row[i])
                else:
                    col_list.append("[key]")
            elif (i == 9):
                js = json.loads(row[i])
                if js:
                    if "status" in js:
                        if "date" in js:
                            dt = datetime.datetime.strptime(js['date'], '%Y-%m-%d') 
                            col_list.append(dt.strftime('%b %d') + " " + js['status'])
                else:
                    col_list.append(row[i])
            else:
                col_list.append(row[i])
        answer = dict(zip(keys, col_list))
        items.append(answer)
    table = TableCls(items, html_attrs = {'width':'100%','border-spacing':0})
    folder_options = ""
    folder_options += '<option value="switch to">switch to</option>'
    folder_options += '<option value="delete">delete</option>'
    name_options = ""
    for name in names:
        if (name["pretty name"] != answer["folder name"]):
            name_options += '<option value="{0}">{0}</option>'.format(name["pretty name"], name["pretty name"])
    if (verbose):
        print ("***\n")
    return table.__html__(), column_options, name_options, folder_options
#endregion stock

#region folder
def Add(symbol, verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
        print ("Add(1) symbol: {0}".format(symbol))
        print ("Add(2) dbase: {0}".format(db_file))
    result = CreateFolder(symbol, verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("Add(3) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("Add(4) {0}".format(e))
            return False
        json_data = Company(symbol, verbose)
        json_string = json.dumps(json_data)
        c = conn.cursor()
        c.execute("UPDATE folder SET json_string = (?) WHERE symbol = (?)", (json_string, symbol,))
        dt = datetime.datetime.now()
        c.execute("UPDATE folder SET update_time = (?) WHERE symbol = (?)", (dt.strftime("%m/%d/%y %H:%M"), symbol,))
        conn.commit()
        conn.close()
        quote = Quote(symbol, verbose)
        errors = []
        if ("Error Message" in quote):
            errors.append([symbol, quote['url'], quote["Error Message"]])
        else:
            Price(symbol, quote['price'], quote['price time'], verbose)
            Shares(symbol, None, verbose)
    if (verbose):
        if (errors):
            pprint.pprint(errors)
        print ("***\n")
    return True

def Remove(symbol, verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
        print ("Remove(1) symbol: {0}".format(symbol))
        print ("Remove(2) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("Remove(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("Remove(4) {0}".format(e))
        return False
    c = conn.cursor()
    c.execute("DELETE FROM folder WHERE symbol=(?)", (symbol,))
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    return True

def Price(symbol, price, price_time, verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
        print ("Price(1) symbol: {0}".format(symbol))
        print ("Price(2) price: {0}".format(price))
        print ("Price(3) price_time: {0}".format(price_time))
        print ("Price(4) dbase: {0}".format(db_file))
    result = CreateFolder(symbol, verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("Price(5) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("Price(6) {0}".format(e))
            return False
        c = conn.cursor()
        dt = datetime.datetime.strptime(price_time, '%m/%d/%y') 
        c.execute("UPDATE folder SET price_time = (?) WHERE symbol = (?)", (dt.strftime("%m/%d/%y"), symbol,))
        c.execute("UPDATE folder SET price = ? WHERE symbol = (?)", (price, symbol,))
        conn.commit()
        conn.close()
    if (verbose):
        print ("***\n")
    return True

def Cash(balance, verbose):
    balance = to_number(balance, verbose)
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
        print ("Cash(1) balance: {0}".format(balance))
        print ("Cash(2) dbase: {0}".format(db_file))
    result = CreateFolder("$", verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("Cash(3) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("Cash(4) {0}".format(e))
            return False
        c = conn.cursor()
        c.execute("UPDATE folder SET balance = ? WHERE symbol = '$'", (round(float(balance), 2),))
        dict_string = {'companyName': 'CASH', 'description': 'Cash Account', 'symbol': '$'}
        json_string = json.dumps(dict_string)
        c.execute("UPDATE folder SET json_string = (?) WHERE symbol = '$'", (json_string,))
        c.execute("UPDATE folder SET shares = ? WHERE symbol = '$'", (round(float(balance), 4),))
        dt = datetime.datetime.now()
        c.execute("UPDATE folder SET update_time = (?) WHERE symbol = '$'", (dt.strftime("%m/%d/%y %H:%M"),))
        c.execute("UPDATE folder SET price_time = (?) WHERE symbol = '$'", (dt.strftime("%m/%d/%y"),))
        c.execute("UPDATE folder SET price = 1.00 WHERE symbol = '$'")
        conn.commit()
        conn.close()
    if (verbose):
        print ("***\n")
    return True

def CreateFolder(key, verbose):
    db_file = GetDB(verbose)
    username = getpass.getuser()
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (verbose):
        print ("***")
        print ("CreateFolder(1) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("CreateFolder(2) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("CreateFolder(3) {0}".format(e))
        return False
    c = conn.cursor()
    c.execute("CREATE TABLE if not exists 'folder' ( `symbol` TEXT NOT NULL UNIQUE, `json_string` TEXT, `balance` REAL, `shares` REAL, `update_time` TEXT, `price_time` TEXT, `price` REAL, PRIMARY KEY(`symbol`) )")
    c.execute( "INSERT OR IGNORE INTO folder(symbol) VALUES((?))", (key,))
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    return True

def Shares(symbol, shares, verbose):
    result = {}
    if shares is None:
        shares = "0"
    if (symbol == "$"):
        Cash(shares, verbose)
        result['status'] = True
        result['shares'] = shares
        return result
    shares = to_number(shares, verbose)
    db_file = GetDB(verbose)
    username = getpass.getuser()
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (verbose):
        print ("***")
        print ("Shares(1) symbol: {0}".format(symbol))
        print ("Shares(2) shares: {0}".format(shares))
        print ("Shares(3) dbase: {0}".format(db_file))
    if (symbol == ""):
        e = "Error: symbol cannot be blank"
        print (e)
        result['status'] = False
        result['balance'] = 0
        result['exception'] = e
        return result
    folder = GetFolder(verbose)
    price = GetFolderValue(symbol, "price", folder)
    if price is None:
        price = 0
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("Shares(4) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("Shares(5) {0}".format(e))
        result['status'] = False
        result['balance'] = 0
        result['exception'] = e
        return result
    c = conn.cursor()
    c.execute("UPDATE folder SET shares = ? WHERE symbol = (?)", (shares, symbol,))
    balance = shares * price
    c.execute("UPDATE folder SET balance = ? WHERE symbol = (?)", (balance, symbol,))
    dt = datetime.datetime.now()
    c.execute("UPDATE folder SET update_time = (?) WHERE symbol = (?)", (dt.strftime("%m/%d/%y %H:%M"), symbol,))
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    result['status'] = True
    result['balance'] = balance
    return result

def Balance(symbol, balance, verbose):
    result = {}
    if (balance is None):
        balance = "0"
    if (symbol == "$"):
        Cash(balance, verbose)
        result['status'] = True
        result['shares'] = balance
        return result
    balance = to_number(balance, verbose)
    db_file = GetDB(verbose)
    username = getpass.getuser()
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (verbose):
        print ("***")
        print ("Balance(1) symbol: {0}".format(symbol))
        print ("Balance(2) balance: {0}".format(balance))
        print ("Balance(3) dbase: {0}".format(db_file))
    if (symbol == ""):
        e = "Error: symbol cannot be blank"
        print (e)
        result['status'] = False
        result['shares'] = 0
        result['exception'] = e
        return result
    folder = GetFolder(verbose)
    price = GetFolderValue(symbol, "price", folder)
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("Balance(4) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("Balance(5) {0}".format(e))
        result['status'] = False
        result['shares'] = 0
        result['exception'] = e
        return result
    c = conn.cursor()
    shares = 0
    if (price is None):
        price = 0
    if price > 0:
        shares = balance / price
    c.execute("UPDATE folder SET shares = ? WHERE symbol = (?)", (shares, symbol,))
    c.execute("UPDATE folder SET balance = ? WHERE symbol = (?)", (balance, symbol,))
    dt = datetime.datetime.now()
    c.execute("UPDATE folder SET update_time = (?) WHERE symbol = (?)", (dt.strftime("%m/%d/%y %H:%M"), symbol,))
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    result['status'] = True
    result['shares'] = shares
    return result

def Update(verbose):
    db_file = GetDB(verbose)
    username = getpass.getuser()
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (verbose):
        print ("***")
        print ("Update(1) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("Update(2) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("Update(3) dbase: {0}, {1}".format(db_file, e))
        return False, e
    c = conn.cursor()
    try:
        c.execute("SELECT symbol, shares, balance FROM folder where symbol != '$' order by symbol")
    except Error as e:
        print("Update(4) dbase: {0}, {1}".format(db_file, e))
        return False, e
    rows = c.fetchall()
    conn.commit()
    conn.close()
    errors = []
    for row in rows:
        quote = Quote(row[0], verbose)
        if ("Error Message" in quote):
            errors.append([row[0], quote['url'], quote["Error Message"]])
            continue
        result = Price(row[0], quote['price'], quote['price time'], verbose)
        result = Shares(row[0], str(row[1]), verbose)
        if (result['status']):
            if (verbose):
                print ("symbol: {0}, current shares: {1}, previous balance: {2}, current balance: {3}".format(row[0], row[1], row[2], result['balance']))
    if (verbose):
        if (errors):
            pprint.pprint(errors)
        print ("***\n")
    return True, ""

def GetFolderCash(verbose):     # can be removed use GetFolder() instead
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
        print ("GetFolderCash(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("GetFolderCash(2) {0} file is missing, cannot return the key".format(db_file))
            print ("***\n")
        return 0
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("GetFolderCash(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("GetFolderCash(4) {0}".format(e))
        return 0
    c = conn.cursor()
    c.execute("SELECT * FROM folder WHERE symbol = '$'")
    keys = list(map(lambda x: x[0].replace("_"," "), c.description))
    values = c.fetchone()
    answer = dict(zip(keys, values))
    conn.close()
    if (verbose):
        print ("***\n")
    return answer['balance']

def GetFolder(verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
        print ("GetFolder(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("GetFolder(2) {0} file is missing, cannot return the key".format(db_file))
            print ("***\n")
        return []
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("GetFolder(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("GetFolder(4) {0}".format(e))
        return []
    c = conn.cursor()
    c.execute("SELECT * FROM folder order by symbol")
    keys = list(map(lambda x: x[0].replace("_"," "), c.description))
    values = c.fetchall()
    conn.close()
    if (verbose):
        print ("***\n")
    answer = []
    for row in values:
        answer.append(dict(zip(keys, row)))
    return answer

def GetFolderValue(symbol, key, folder_dict):
    value = None
    for row in folder_dict:
        if row['symbol'] == symbol:
            return row[key]
    return value

def GetFolderStockValue(verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
        print ("GetFolderStockValue(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("GetFolderStockValue(2) {0} file is missing, cannot return the key".format(db_file))
            print ("***\n")
        return 0
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("GetFolderStockValue(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("GetFolderStockValue(4) {0}".format(e))
        return 0
    c = conn.cursor()
    c.execute("SELECT * FROM folder WHERE symbol != '$' order by symbol")
    rows = c.fetchall()
    conn.commit()
    conn.close()
    answer = 0
    for row in rows:
        if (row[2] is not None):
            answer += row[2]
    if (verbose):
        print ("***\n")
    return answer

def PrintFolder(verbose):       #use GetFolder() not regoing to the db
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
    if db_file == "":
        if (verbose):
            print ("PrintFolder(1) could not get dbase, make sure that the defaults dbase is set up")
        return "", "", "", []
    if (verbose):
        print ("PrintFolder(2) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("PrintFolder(4) sqlite3: {0}".format(sqlite3.version))
        if (not checkTableExists(conn, "folder")):
            Cash("0", verbose)
    except Error as e:
        print("PrintFolder(5) {0}".format(e))
        return  e, "", "", []
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("PrintFolder(3) {0} file is missing, cannot print".format(db_file))
            print ("***\n")
        return "", "", "", []
    c = conn.cursor()
    c.execute("SELECT * FROM folder order by symbol")
    keys = list(map(lambda x: x[0].replace("_"," "), c.description))
    rows = c.fetchall()
    conn.commit()
    conn.close()
    TableCls = create_table('TableCls')
    for key in keys:
        if (key != "json string"):
            TableCls.add_column(key, Col(key))
        else:
            TableCls.add_column('company name', Col('company name'))
    keys[1] = 'company name'
    items = []
    answer = {}
    symbol_options = ""
    balance_options = ""
    balance_options += '<option value="balance">balance</option>'
    balance_options += '<option value="shares">shares</option>'
    balance_options += '<option value="amount">amount</option>'
    amount_options = []
    for row in rows:
        json_string = json.loads(row[1])
        col_list = []
        for i in range(len(keys)):
            if (i == 0):
                symbol_options += '<option value="{0}">{1}</option>'.format(row[i], row[i])
            if (i == 1):
                col_list.append(json_string['companyName'])
            elif (i == 3):
                if (row[0] == "$"):
                    col_list.append("")
                else:
                    if row[i] is None:
                        col_list.append(round(0, 2))
                    else:
                        col_list.append(round(row[i], 2))
            else:
                if (i == 2 or i == 6):
                    if (i == 2):
                        amount_option = []
                        amount_option.append(row[0])
                        amount_option.append(row[i])
                        amount_options.append(amount_option)
                    if (i ==6 and row[0] == "$"):
                        col_list.append("")
                    else:
                        col_list.append(as_currency(row[i]))
                else:
                    col_list.append(row[i])
        answer = dict(zip(keys, col_list))
        items.append(answer)
    table = TableCls(items, html_attrs = {'width':'100%','border-spacing':0})
    if (verbose):
        print ("***\n")
    button_table = AddRemoveButtons(table.__html__())
    return button_table, symbol_options, balance_options, amount_options

def AddRemoveButtons(table):
    table = table.replace("<thead><tr><th>", "<thead><tr><th></th><th>", 1)
    pattern = "<tr><td>"
    index = 0
    done = False
    row = -1
    while (not done):
        start = table.find(pattern, index)
        if start == -1:
            done = True
            continue
        symbol = table[start + 8 :table.find("</td>", start + 8)]
        row += 1
        if (symbol != "$"):
            r_button = '<tr><td><form action="#" method="post"><input class="submit" type="submit" name="action" value="remove"/><input hidden type="text" name="remove_symbol" value="{0}"/></form></td><td>'.format(symbol)
            table = table[0 : start] + table[start:].replace(pattern, r_button, 1)
        else:
            table = table[0 : start] + table[start:].replace(pattern, "<tr><td></td><td>", 1)
        index = start + 1
    return table

def AllocationTrends(verbose):      # use GetFolder() 
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
    if db_file == "":
        if (verbose):
            print ("AllocationTrends(1) could not get dbase, make sure that the defaults dbase is set up")
        return "", "", ""
    prev = GetLastAIM(verbose)
    if ("json string" not in prev):
        if (verbose):
            print ("AllocationTrends(2) could not get previous balances, make sure you have initialized AIM system")
        return "", "", ""
    js = json.loads(prev['json string'])
    last_list = []
    for col in js:
        if ("symbol" in col):
            if (col['symbol'] != "$"):
                last_list.append(col)
    first = GetFirstAIM(verbose)
    if ("json string" not in first):
        if (verbose):
            print ("AllocationTrends(3) could not get initial balances, make sure you have initialized AIM system")
        return "", "", ""
    js = json.loads(first['json string'])
    first_list = []
    for col in js:
        if ("symbol" in col):
            if (col['symbol'] != "$"):
                first_list.append(col)
    if (verbose):
        print ("AllocationTrends(4) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("AllocationTrends(5) {0} file is missing, cannot print".format(db_file))
            print ("***\n")
        return "", "", ""
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("AllocationTrends(6) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("AllocationTrends(7) {0}".format(e))
        return "", "",""
    c = conn.cursor()
    c.execute("SELECT * FROM folder where symbol != '$' order by symbol")
    rows = c.fetchall()
    conn.commit()
    conn.close()
    total = 0
    for row in rows:
        if (row[2] is not None):
            total = total + row[2]
    allocation = ""
    for row in rows:
        pst = 0
        if (row[2] is not None):
            pst = row[2] / total * 100.
        allocation = allocation + "<li>{0} {1}</li>".format(row[0], as_percent(pst))

    trends = []
    for row in rows:
        for col in last_list:
            if (row[0] == col['symbol']):
                pst = 0
                test = 0
                trend = {}
                if (row[2] is not None):
                    pst = (row[2] - col['balance']) / col['balance'] * 100.
                    if pst == 0:
                        trend['arrow'] = "flat"
                        trend['percent'] = "{0} {1}".format(row[0], as_percent(pst))
                    elif pst > 0:
                        trend['arrow'] = "up"
                        trend['percent'] = "{0} {1}".format(row[0], as_percent(pst))
                    else:
                        trend['arrow'] = "down"
                        trend['percent'] = "{0} {1}".format(row[0], as_percent(pst))
                    trends.append(trend)
    life_trends = []
    for row in rows:
        for col in first_list:
            if (row[0] == col['symbol']):
                pst = 0
                test = 0
                trend = {}
                if (row[2] is not None):
                    pst = (row[2] - col['balance']) / col['balance'] * 100.
                    if pst == 0:
                        trend['arrow'] = "flat"
                        trend['percent'] = "{0} {1}".format(row[0], as_percent(pst))
                    elif pst > 0:
                        trend['arrow'] = "up"
                        trend['percent'] = "{0} {1}".format(row[0], as_percent(pst))
                    else:
                        trend['arrow'] = "down"
                        trend['percent'] = "{0} {1}".format(row[0], as_percent(pst))
                    life_trends.append(trend)        
    return allocation, trends, life_trends
#endregion folder

#region aim
def GetAIM(verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
        print ("GetAIM(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("GetAIM(2) {0} file is missing, cannot return the key".format(db_file))
            print ("***\n")
        return []
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("GetAIM(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("GetAIM(4) {0}".format(e))
        return []
    c = conn.cursor()
    c.execute("SELECT * FROM aim order by post_date")
    keys = list(map(lambda x: x[0].replace("_"," "), c.description))
    values = c.fetchall()
    conn.close()
    if (verbose):
        print ("***\n")
    answer = []
    for row in values:
        answer.append(dict(zip(keys, row)))
    return answer

def CreateAIM(verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
    if db_file == "":
        log = "CreateAIM(1) could not get dbase, make sure that the defaults dbase is set up"
        if (verbose):
            print (log)
        return False, log
    stock = GetFolderStockValue(verbose)
    if (stock == 0):    # test then set to ==
        return False, "Please purchase some shares in a company for your Folder before initializing AIM" 
    cash = GetFolderCash(verbose)
    if (cash == 0):    # test then set to ==
        return False, "Please add some cash to your Folder before initializing AIM"
    count = GetAIMCount(verbose)
    if (count > 1):
        return False, "You must go to the History Tab and archive your AIM data first"
    pv = PortfolioValue(cash, stock, verbose)
    username = getpass.getuser()
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (verbose):
        print ("***")
        print ("CreateAIM(1) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("CreateAIM(2) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("CreateAIM(3) {0}".format(e))
        return False, e
    c = conn.cursor()
    c.execute("CREATE TABLE if not exists 'aim' ( `post_date` TEXT NOT NULL UNIQUE, `stock_value` REAL, `cash` REAL, `portfolio_control` REAL, `buy_sell_advice` REAL, `market_order` REAL, `portfolio_value` REAL, `json_string` TEXT, PRIMARY KEY(`post_date`) )")
    c.execute("DELETE FROM aim where post_date = '1970/01/01'")
    dt = datetime.datetime.now()
    ds = {}
    ds['start date'] = dt.strftime("%Y/%m/%d")
    table, symbol_options, balance_options, amount_options = PrintFolder(False)
    dl = GetCurrentStockList(amount_options)
    dl.insert(0, ds)
    json_string = json.dumps(dl) 
    c.execute( "INSERT INTO aim VALUES((?),?,?,?,?,?,?,(?))", ("1970/01/01", stock, cash, stock, 0, 0, pv, json_string,))
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    return True, "AIM system initialized."

def Safe(stockvalue, verbose): 
    if (verbose):
        print ("***")
        print ("Safe(1) stockvalue: {0}".format(stockvalue))
        print ("***\n")           
    answer = math.ceil(stockvalue/10.-.4)
    return answer

def PortfolioControl(marketorder, previous, verbose):
    if (verbose):
        print ("***")
        print ("PortfolioControl(1) marketorder: {0}".format(marketorder))
        print ("PortfolioControl(2) previous: {0}".format(previous))
        print ("***\n")
    if (marketorder <= 0):
        return previous
    return math.ceil((previous + (marketorder / 2.)-.4))

def PortfolioValue(cash, stockvalue, verbose):
    if (verbose):
        print ("***")
        print ("PortfolioValue(1) cash: {0}".format(cash))
        print ("PortfolioValue(2) stockvalue: {0}".format(stockvalue))
        print ("***\n")
    return (cash + stockvalue)

def BuySellAdvice(portfoliocontrol, stockvalue, verbose):
    if (verbose):
        print ("***")
        print ("BuySellAdvice(1) portfoliocontrol: {0}".format(portfoliocontrol))
        print ("BuySellAdvice(2) stockvalue: {0}".format(stockvalue))
        print ("***\n")
    if (portfoliocontrol <= 0):
        return 0
    answer = portfoliocontrol - stockvalue
    return answer

def MarketOrder(buyselladvice, safe, verbose):
    if (verbose):
        print ("***")
        print ("MarketOrder(1) buyselladvice: {0}".format(buyselladvice))
        print ("MarketOrder(2) safe: {0}".format(safe))
        print ("***\n")
    if (buyselladvice == 0):
        return 0
    if (safe > abs(buyselladvice)):
        return 0
    answer = abs(buyselladvice) - safe
    if (buyselladvice < 0):
        return -answer
    return answer

def GetAIMCount(verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
    if db_file == "":
        if (verbose):
            print ("GetAIMCount(1) could not get dbase name, make sure that the defaults dbase is set up")
        return 0
    if (verbose):
        print ("GetAIMCount(2) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("GetAIMCount(3) {0} file is missing, cannot return the row count".format(db_file))
            print ("***\n")
        return 0
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("GetAIMCount(4) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("GetAIMCount(5) {0}".format(e))
        return 0
    if (checkTableExists(conn, "aim")):
        c = conn.cursor()
        c.execute("select * from aim")
        results = c.fetchall()
    else:
        results = ""
    conn.close()
    if (verbose):
        print ("***\n")
    return len(results)

def checkTableExists(dbcon, tablename):
    dbcur = dbcon.cursor()
    dbcur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=(?);", (tablename,))
    test = dbcur.fetchone()
    if test is None:
        dbcur.close()
        return False
    dbcur.close()
    return True

def GetLastAIM(verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
    if db_file == "":
        if (verbose):
            print ("GetLastAIM(1) could not get dbase name, make sure that the defaults dbase is set up")
        return {}
    if (verbose):
        print ("GetLastAIM(2) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("GetLastAIM(3) {0} file is missing, cannot return the last row".format(db_file))
            print ("***\n")
        return {}
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("GetLastAIM(4) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("GetLastAIM(5) {0}".format(e))
        return {}
    answer = {}
    if (checkTableExists(conn, "aim")):
        c = conn.cursor()
        c.execute("SELECT * FROM aim ORDER BY post_date DESC LIMIT 1")
        keys = list(map(lambda x: x[0].replace("_"," "), c.description))
        values = c.fetchone()
        answer = dict(zip(keys, values))
        conn.close()
    if (verbose):
        print ("***\n")
    return answer

def GetAIMNotes(count, verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
    if db_file == "":
        if (verbose):
            print ("GetAIMNotes(1) could not get dbase name, make sure that the defaults dbase is set up")
        return {}, True
    if (verbose):
        print ("GetAIMNotes(2) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("GetAIMNotes(3) {0} file is missing, cannot return the notes".format(db_file))
            print ("***\n")
        return {}, True
    count = GetAIMCount(verbose)
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("GetAIMNotes(4) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("GetAIMNotes(5) {0}".format(e))
        return {}, True
    if (checkTableExists(conn, "aim")):
        c = conn.cursor()
        c.execute("SELECT * FROM aim ORDER BY post_date DESC LIMIT ?", (count,))
        keys = list(map(lambda x: x[0].replace("_"," "), c.description))
        rows = c.fetchall()
        conn.close()
    else:
        keys = []
        rows = []
    notes = []
    defaults, types =  GetDefaults(False)
    initialize_day = False
    for row in rows:
        note = {}
        answer = dict(zip(keys, row))
        js = json.loads(row[7])
        dt = datetime.datetime.now()
        if (answer['post date'] == "1970/01/01"):
            if (count < 2):
                initialize_day = True
            if (js is not {}):
                if ("start date" in js[0]):
                    dt = datetime.datetime.strptime(js[0]['start date'], '%Y/%m/%d')
                    if (dt.date != datetime.datetime.now().date):
                        initialize_day = False
            note['date'] = noteDate(js[0]['start date'])
            note['content'] = "A.I.M. Was initialized with {0} for '{1}'".format(as_currency(answer['cash'] + answer['stock value']), defaults['folder name'])            
        else:
            note['date'] = noteDate(answer['post date'])
            if (answer['market order'] == 0):
                note['content'] = "hold current position."
            elif (answer['market order'] < 0):
                note['content'] = "sold {0} of '{1}'".format(as_currency(answer['market order']), defaults['folder name'])
            else:
                note['content'] = "purchased {0} for '{1}'".format(as_currency(answer['market order']), defaults['folder name'])
        notes.append(note)
    if (verbose):
        print ("***\n")
    return notes, initialize_day

def noteDate(value):
    if (value == ""):
        return ""
    dt = datetime.datetime.strptime(value, '%Y/%m/%d') 
    return custom_strftime('%B {S}, %Y', dt)

def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

def GetFirstAIM(verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
    if db_file == "":
        if (verbose):
            print ("GetFirstAIM(1) could not get dbase name, make sure that the defaults dbase is set up")
        return {}
    if (verbose):
        print ("GetFirstAIM(2) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("GetFirstAIM(3) {0} file is missing, cannot return the first row".format(db_file))
            print ("***\n")
        return {}
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("GetFirstAIM(4) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("GetFirstAIM(5) {0}".format(e))
        return {}
    answer = {}
    if (checkTableExists(conn, "aim")):
        c = conn.cursor()
        c.execute("SELECT * FROM aim where post_date = '1970/01/01'")
        keys = list(map(lambda x: x[0].replace("_"," "), c.description))
        values = c.fetchone()
        answer = dict(zip(keys, values))
        conn.close()
    if (verbose):
        print ("***\n")
    return answer

def to_number(string, verbose):
    negative = False
    percent = False
    if ('(' in string):
        negative = True
    if ('%' in string):
        percent = true
    if (verbose):
        print ("***")
        print ("to_number(1) raw: {0}".format(string))
        print ("to_number(2) negative: {0}".format(negative))
        print ("to_number(3) percent: {0}".format(percent))

    string = string.replace("$", "")
    if (verbose):
        print ("to_number(4) remove $: {0}".format(string))

    string = string.replace(",", "")
    if (verbose):
        print ("to_number(5) remove ,: {0}".format(string))

    string = string.replace("(", "")
    if (verbose):
        print ("to_number(6) remove (: {0}".format(string))
    string = string.replace(")", "")
    if (verbose):
        print ("to_number(7) remove ): {0}".format(string))

    string = string.replace("%", "")
    if (verbose):
        print ("to_number(8) remove %: {0}".format(string))

    clean_number = float(string)
    if (percent):
        clean_number = clean_number / 100.
    if (negative):
        clean_number = - clean_number
    if (verbose):
        print ("to_number(9) clean_number: {0}".format(clean_number))
        print ("***\n")
    return clean_number

def as_currency(amount):
    if (amount is None):
        amount = 0
    if amount >= 0:
        return '${:,.2f}'.format(amount)
    else:
        return '(${:,.2f})'.format(-amount)

def as_percent(amount):
    if amount >= 0:
        return "{:.2f}%".format(amount)
    else:
        return '({:.2f}%)'.format(-amount)

def Look(verbose):
    first = GetFirstAIM(verbose)
    if not first:
        if (verbose):
            print ("Look(1) could not get defaults, make sure that the defaults dbase is set up")
        return {}, "", {}
    prev = GetLastAIM(verbose)
    cd = datetime.datetime.now()
    pushed = False
    if cd.strftime("%Y/%m/%d") == prev['post date']:
        pushed = True
    prev_pc = math.ceil(prev['portfolio control'] -.4)
    db_keys = prev.keys()
    keys = []
    for key in db_keys:
        if (key == 'cash'):
            keys.append("safe") # safe is not in the db (want to see it though)
        if key != "json string":
            keys.append(key)
    stock = GetFolderStockValue(verbose)
    cash = GetFolderCash(verbose)
    bsa = BuySellAdvice(prev_pc, stock, verbose)
    safe = Safe(stock, verbose)
    mo = MarketOrder(bsa, safe, verbose)
    pc = PortfolioControl(mo, prev_pc, verbose)
    pv = PortfolioValue(cash, stock, verbose)
    values = []
    values.append(cd.strftime("%b, %d"))
    values.append(as_currency(stock))
    values.append(safe)
    values.append(as_currency(cash))
    values.append(as_currency(pc))
    values.append(as_currency(bsa))
    values.append(as_currency(mo))
    values.append(as_currency(pv))
    values_db = []
    values_db.append(cd.strftime("%Y/%m/%d"))
    values_db.append(stock)
    values_db.append(safe)
    values_db.append(cash)
    values_db.append(pc)
    values_db.append(bsa)
    values_db.append(mo)
    values_db.append(pv)
    values_db.append({})
    pretty = dict(zip(keys, values))
    answer_db = dict(zip(keys, values_db))
    TableCls = create_table('TableCls')
    for key in keys:
        TableCls.add_column(key, Col(key))
    items = []
    items.append(pretty)
    table = TableCls(items, html_attrs = {'width':'100%','border-spacing':0})
    pct_cash = cash / pv * 100.
    pct_stock = stock / pv * 100.
    pretty['initial value'] = as_currency(first['portfolio value'])
    pretty['profit value'] = as_currency(pv - first['portfolio value'])
    pretty['profit percent'] = as_percent((pv - first['portfolio value']) / first['portfolio value'] * 100.)
    pretty['percent list'] = "<li>Cash {0}</li><li>Stock {1}</li>".format(as_percent(pct_cash), as_percent(pct_stock))
    return pretty, table.__html__(), answer_db, pushed

def Post(verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
        print ("Post(1) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("Post(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("Post(4) {0}".format(e))
        return False
    look, table, db_values, pushed = Look(verbose)
    if (verbose):
        print("Post(5) {0}".format(look))
    table, symbol_options, balance_options, amount_options = PrintFolder(False)
    dl = GetCurrentStockList(amount_options)
    json_string = json.dumps(dl)
    c = conn.cursor()
    c.execute( "INSERT OR IGNORE INTO aim(post_date) VALUES((?))", (db_values['post date'],))
    c.execute("UPDATE aim SET stock_value = ? WHERE post_date = (?)", (db_values['stock value'], db_values['post date'],))
    c.execute("UPDATE aim SET cash = ? WHERE post_date = (?)", (db_values['cash'], db_values['post date'],))
    c.execute("UPDATE aim SET portfolio_control = ? WHERE post_date = (?)", (db_values['portfolio control'], db_values['post date'],))
    c.execute("UPDATE aim SET buy_sell_advice = ? WHERE post_date = (?)", (db_values['buy sell advice'], db_values['post date'],))
    c.execute("UPDATE aim SET market_order = ? WHERE post_date = (?)", (db_values['market order'], db_values['post date'],))
    c.execute("UPDATE aim SET portfolio_value = ? WHERE post_date = (?)", (db_values['portfolio value'], db_values['post date'],))
    c.execute("UPDATE aim SET json_string = (?) WHERE post_date = (?)", (json_string, db_values['post date'],))
    conn.commit()
    conn.close()
    if (db_values['market order'] != 0):
        pyperclip.copy(str(db_values['market order']))
        #
        # you must install this for pyperclip in ubuntu
        # sudo apt install xclip
        #
    if (verbose):
        print ("***\n")
    return True

def GetCurrentStockList(stock_list):
    dl = []
    for item in stock_list:
        ds = {}
        ds['symbol'] = item[0]
        ds['balance'] = round(item[1], 2)
        dl.append(ds)
    return dl

def PrintAIM(printyear, verbose):
    if (printyear[0] == 'a'):
        intyear = 1970
    else:
        intyear = int(printyear)
        if (intyear < 100):
            intyear = 2000 + intyear
        printyear = str(intyear)
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
    if db_file == "":
        if (verbose):
            print ("PrintAIM(1) could not get dbase name, make sure that the defaults dbase is set up")
        return ""
    if (verbose):
        print ("PrintAIM(2) dbase: {0}".format(db_file))
        print ("PrintAIM(3) year: {0}".format(printyear))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("PrintAIM(4) {0} file is missing, cannot print".format(db_file))
            print ("***\n")
        return ""
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("PrintAIM(5) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("PrintAIM(6) {0}".format(e))
        return ""
    keys_db = []
    rows = []
    if (checkTableExists(conn, "aim")):
        c = conn.cursor()
        c.execute("SELECT * FROM aim order by post_date")
        keys_db = list(map(lambda x: x[0].replace("_"," "), c.description))
        rows = c.fetchall()
        conn.commit()
        conn.close()
    keys = []
    for key in keys_db:
        if (key == 'cash'):
            keys.append("safe") # safe is not in the db (want to see it though)
        if key != "json string":
            keys.append(key)
    TableCls = create_table('TableCls')
    for key in keys:
        TableCls.add_column(key, Col(key))
    items = []
    answer = {}
    for row in rows:
        js = json.loads(row[7])
        dt = datetime.datetime.strptime(row[0], '%Y/%m/%d')
        if (intyear == 1970 or dt.year == intyear):
            if (js is not {}):
                if ("start date" in js[0]):
                    dt = datetime.datetime.strptime(js[0]['start date'], '%Y/%m/%d')
            col_list = []
            for i in range(len(keys)):
                if (i == 0):
                    col_list.append(dt.strftime("%b, %d"))
                elif (i == 1):
                    col_list.append(as_currency(row[i]))
                elif (i == 2):
                    stock = math.ceil(row[1] -.4)
                    safe = Safe(stock, verbose)
                    col_list.append(safe)
                else:
                    col_list.append(as_currency(row[i - 1]))
            answer = dict(zip(keys, col_list))
            items.append(answer)
    table = TableCls(items, html_attrs = {'width':'100%','border-spacing':0})
    if (verbose):
        print ("***\n")
    return table.__html__()
#endregion aim

#region tests
def TestStock(verbose):
    count = 0
    defaults, types =  GetDefaults(False)
    if (verbose):
        print ("***")
        print ("\tRunning tests will preserve your original defaults")
        print ("***\n")
        print ("Test #{0} - Company('AAPL', verbose)".format(count + 1))
    result = Company("AAPL", verbose)
    if (result['companyName'] == "Apple Inc."):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #{0} - UpdateDefaultItem('alpha vantage key', 'TEST', verbose)".format(count + 1))
    result = UpdateDefaultItem("alpha vantage key", "TEST", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #{0} - UpdateDefaultItem('tradier key', 'TEST', verbose)".format(count + 1))
    result = UpdateDefaultItem("tradier key", "TEST", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #{0} - UpdateDefaultItem('daemon seconds', 600, False)".format(count + 1))
    result = UpdateDefaultItem('daemon seconds', 600, verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #{0} - UpdateDefaultItem('test root', 'test/', False)".format(count + 1))
    result = UpdateDefaultItem("test root", "test/", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #{0} - UpdateDefaultItem('open', '8:30AM', False)".format(count + 1))
    result = UpdateDefaultItem("open", "8:30AM", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #{0} - UpdateDefaultItem('close', '15:00', False)".format(count + 1))
    result = UpdateDefaultItem("close", "15:00", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #{0} - Quote('AAPL', verbose)".format(count + 1))
    result = Quote("AAPL", verbose)
    if (result['status'] and result['symbol'] == "AAPL"):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #{0} - GetDefaults(False)".format(count + 1))
    result, types = GetDefaults(verbose)
    if (result['alpha vantage key'] == "TEST"
        and result['tradier key'] == "TEST"
        and result['daemon seconds'] == 600
        and result['open'] == "8:30AM"
        and result['close'] == "15:00"
        and result['test root'] == "test/"
        and result['folder name'] == "Practice Portfolio"):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    reset = defaults
    for k,v in reset.items():
        if (k != "username"):
            if (verbose):
                print ("Test #{0} - resets {1} back".format(count + 1, k))
            result = UpdateDefaultItem(k, v, verbose)
            if (result):
                if (verbose):
                    print ("\tpass.")
                count += 1
            else:
                if (verbose):
                    print ("\tfail.")
    if (count == 17):
        print ("ran 17 tests, all pass")
        return True
    else:
        print ("test count expected 17 passes, received {0}".format(count))
    return False

def TestFolder(verbose):
    count = 0
    defaults, types = GetDefaults(verbose)
    if (verbose):
        print ("Test #{0} - UpdateDefaultItem('folder name', 'Test Folder', verbose)".format(count + 1))
    result = UpdateDefaultItem("folder name", "Test Folder", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #{0} - Add('AAPL', verbose)".format(count + 1))
    result = Add( "AAPL", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #{0} - Balance('$', '5000', verbose)".format(count + 1))
    result = Balance( "$", "5000", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #{0} - Balance('AAPL', '5000', verbose)".format(count + 1))
    result = Balance("AAPL", "5000", verbose)
    if (result['status']):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #{0} - Shares('AAPL', '50', verbose)".format(count + 1))
    result = Shares("AAPL", "50", verbose)
    if (result['status']):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #{0} - Update(verbose)".format(count + 1))
    result = Update(verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #{0} - Remove('AAPL', verbose)".format(count + 1))
    result = Remove("AAPL", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    username = getpass.getuser()
    if (verbose):
        print ("Test #{0} - UpdateDefaultItem('folder name', 'Test Folder', verbose)".format(count + 1))
    result = UpdateDefaultItem("folder name", defaults['folder name'], verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #{0} - DeleteName('Test Folder', verbose)".format(count + 1))
    result = DeleteName("Test Folder", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (count == 9):
        print ("ran 9 tests, all pass")
        return True
    else:
        print ("test count expected 9 passes, received {0}".format(count))
    return False

def TestAIM(location, verbose):
    count = 0
    defaults, types = GetDefaults(False)
    status, keys, rows = LoadTest(location, verbose)
    if (status and (defaults is not None)):
        if (verbose):
            print ("Test #{0} - UpdateDefaultItem('folder name', 'Test Aim', verbose)".format(count + 1))
        result = UpdateDefaultItem("folder name", "Test Aim", verbose)
        if (result):
            if (verbose):
                print ("\tpass.")
            count += 1
        else:
            if (verbose):
                print ("\tfail.")
        if (verbose):
            print ("testing {0} spreadsheet rows".format(len(rows)))
        for item in rows.items():
            index = item[0]
            if (index == 0):
                continue
            curr = dict(zip(keys, item[1]))
            prev = GetPrevious(index, keys, rows)
            if (verbose):
                print ("Test #{0} - Safe(<Stock Value>, verbose)".format(count + 1))
            result = Safe(myFloat(curr['Stock Value']), verbose)
            if (result == myFloat(curr['Safe'])):
                if (verbose):
                    print ("\tSafe({0}) - pass.".format(index))
                count += 1
            else:
                if (verbose):
                    print ("\tSafe({0}) - expected: {1}, calculated: {2}, fail.".format(index, curr['Safe'], result))
            if (verbose):
                print ("Test #{0} - PortfolioControl(<Market Order>, <Prev Portfolio Control>, verbose)".format(count + 1))
            result = PortfolioControl(myFloat(curr['Market Order']), myFloat(prev['Portfolio Control']), verbose)
            if (result == myFloat(curr['Portfolio Control'])):
                if (verbose):
                    print ("\tPortfolioControl({0}) - pass.".format(index))
                count += 1
            else:
                if (verbose):
                    print ("\tPortfolioControl({0}) - expected: {1}, calculated: {2}, fail.".format(index, curr['Portfolio Control'], result))
            if (verbose):
                print ("Test #{0} - BuySellAdvice(<Portfolio Control>, <Stock Value>, verbose)".format(count + 1))
            result = BuySellAdvice(myFloat(prev['Portfolio Control']), myFloat(curr['Stock Value']), verbose)
            if (result == myFloat(curr['Buy (Sell) Advice'])):
                if (verbose):
                    print ("\tBuySellAdvice({0}) - pass.".format(index))
                count += 1
            else:
                if (verbose):
                    print ("\tBuySellAdvice({0}) - expected: {1}, calculated: {2}, fail.".format(index, curr['Buy (Sell) Advice'], result))
            if (verbose):
                print ("Test #{0} - MarketOrder(<Buy (Sell) Advice>, <Safe>, verbose)".format(count + 1))
            result = MarketOrder(myFloat(curr['Buy (Sell) Advice']), myFloat(curr['Safe']), verbose)
            if (result == myFloat(curr['Market Order'])):
                if (verbose):
                    print ("\tMarketOrder({0}) - pass.".format(index))
                count += 1
            else:
                if (verbose):
                    print ("\tMarketOrder({0}) - expected: {1}, calculated: {2}, fail.".format(index, curr['Market Order'], result))
            if (verbose):
                print ("Test #{0} - PortfolioValue(<Cash>, <Stock Value>, verbose)".format(count + 1))
            result = PortfolioValue(myFloat(curr['Cash']), myFloat(curr['Stock Value']), verbose)
            if (result == myFloat(curr['Portfolio Value'])):
                if (verbose):
                    print ("\tPortfolioValue({0}) - pass.".format(index))
                count += 1
            else:
                if (verbose):
                    print ("\tPortfolioValue({0}) - expected: {1}, calculated: {2}, fail.".format(index, curr['Portfolio Value'], result))
        username = getpass.getuser()
        if (verbose):
            print ("Test #{0} - UpdateDefaultItem('folder name', '<reset back to what it was>', verbose)".format(count + 1))
        result = UpdateDefaultItem("folder name", defaults['folder name'], verbose)
        if (result):
            if (verbose):
                print ("\tpass.")
            count += 1
        else:
            if (verbose):
                print ("\tfail.")
        if (verbose):
            print ("Test #{0} - DeleteName('Test Aim', verbose)".format(count + 1))
        result = DeleteName("Test Aim", verbose)
        if (result):
            if (verbose):
                print ("\tpass.")
            count += 1
        else:
            if (verbose):
                print ("\tfail.")
        if (count == 453):
            print ("ran 453 tests, all pass")
            return True
        else:
            print ("test count expected 453 passes, received {0}".format(count))
    return False

def myFloat(value):
    try:
        answer = float(value)
    except ValueError:
        return 0
    return answer

def GetPrevious(index, keys, rows):
    count = index - 1
    values = []
    for i in keys:
        values.append('')
    if (count < 0):
        return  dict(zip(keys, values))
    value = rows[count]
    answer = dict(zip(keys, value))
    return answer

def GetIndex(item):
    filename = os.path.basename(str(item))
    idx = re.findall(r'\d+', str(filename))
    if (len(idx) == 0):
        idx.append("0")
    return int(idx[0])

def GetFiles(path, templatename):
    A = []
    for p in Path(path).glob(templatename):
        A.append(str(p))
    file_list = []
    for item in range(0, 17):
        file_list.append("?")
    for item in A:
        idx = GetIndex(item)
        file_list[idx] = item
    file_list = [x for x in file_list if x != "?"]
    return file_list

def LoadTest(location, verbose):
    defaults, types = GetDefaults(False)
    test_dir = defaults['test root'] + location
    if not os.path.isdir(test_dir):
        print ("test directory: {0} does not exist - cannot continue.".format(test_dir))
        return False, [], {}
    file_list = GetFiles(test_dir, "*.csv")
    if not file_list:
        print ("could not find any .csv files - cannot continue.")
        return False, [], {}
    keys = []
    values = {}
    index = -1
    for f in file_list:
        with open(f, mode='r') as infile:
            reader = csv.reader(infile)
            for item in reader:
                if (not keys):
                    keys = item
                if item[0] != "Stock Price":
                    index += 1
                    values[index] = item               
    return True, keys, values
#endregion tests
#region daemon
def LogDaemon(log, verbose):
    if (verbose):
        print ("***")
    if "status" not in log:
        print ("LogDaemon(1) - could not find any status to log - cannot continue.")
        return False
    status = log['status']
    del log['status']
    json_string = json.dumps(log)
    if (verbose):
        print ("LogDaemon(2) status: {0}".format(status))
    username = getpass.getuser()
    db_file = username + "/daemon.db"
    if (verbose):
        print ("LogDaemon(3) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("LogDaemon(4) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("LogDaemon(6) {0}".format(e))
        return False
    c = conn.cursor()
    c.execute("CREATE TABLE if not exists `log` ( `status` TEXT NOT NULL UNIQUE, `timestamp` TEXT, `json_string` TEXT, PRIMARY KEY(`status`) )")
    c.execute( "INSERT OR IGNORE INTO log(status) VALUES((?))", (status,))
    c.execute("UPDATE log SET timestamp = (?) WHERE status = (?)", (datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f"), status,))
    c.execute("UPDATE log SET json_string = (?) WHERE status = (?)", (json_string, status,))
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    return True

def PrintDaemon(status, verbose):
    if (status == ""):
        status = "all"
    username = getpass.getuser()
    if (verbose):
        print ("***")
    db_file = username + "/daemon.db"
    if (verbose):
        print ("PrintDaemon(1) status: {0}".format(status))
        print ("PrintDaemon(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("PrintDaemon(2) {0} file is missing, cannot print".format(db_file))
            print ("***\n")
        return "", ""
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("PrintDaemon(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("PrintDaemon(4) {0}".format(e))
        return  e, ""
    c = conn.cursor()
    if (status == "" or status =="all"):
        c.execute("SELECT * FROM log order by timestamp DESC")
    else:
        c.execute("SELECT * FROM log where status = (?) order by timestamp DESC", (status,))
    keys = list(map(lambda x: x[0].replace("_"," "), c.description))
    rows = c.fetchall()
    conn.commit()
    conn.close()
    TableCls = create_table('TableCls')
    for key in keys:
        if (key != "json string"):
            TableCls.add_column(key, Col(key))
        else:
            TableCls.add_column('pid', Col('pid'))
    keys[2] = 'pid'
    items = []
    answer = {}
    status = ""
    for row in rows:
        if row[0] != "sleep" and status == "":
            status = row[0]
        json_string = json.loads(row[2])
        col_list = []
        for i in range(len(keys)):
            if (i == 1):
                dt = datetime.datetime.strptime(row[i], '%Y/%m/%d %H:%M:%S.%f')
                col_list.append(dt.strftime("%b %d %I:%M %p"))
            elif (i == 2):
                col_list.append(json_string['pid'])
            else:
                col_list.append(row[i])
        answer = dict(zip(keys, col_list))
        items.append(answer)
    table = TableCls(items, html_attrs = {'width':'100%','border-spacing':0})
    if (verbose):
        print ("***\n")
    return table.__html__(), status

def get_pid(name):
    child = subprocess.Popen(['pgrep', '-f', name], stdout=subprocess.PIPE, shell=False)
    response = child.communicate()[0]
    return [int(pid) for pid in response.split()]

def kill_pid(pid):
    return(os.kill(pid, signal.SIGTERM))

def run_script(name):
    pid = get_pid(name)
    if pid != []:
        log = {}
        log['status'] = "stop"
        log['pid'] = pid[0]
        LogDaemon(log, False)
        kill_pid(pid[0])
    os.system(name)
#endregion daemon
#region history
def ActivitySheet(filename, verbose):
    aim = GetAIM(verbose)
    if aim == []:
        return False
    header = True
    sheet = open(filename, 'w', newline='')
    csvwriter = csv.writer(sheet)
    for row in aim:
        if (header):
            keys = row.keys()
            header = False
            csvwriter.writerow(keys)
        values = row.values()
        csvwriter.writerow(values)
    sheet.close()  
    return True

def FolderSheet(filename, verbose):
    folder = GetFolder(verbose)
    if folder == []:
        return False
    header = True
    sheet = open(filename, 'w', newline='')
    csvwriter = csv.writer(sheet)
    for row in folder:
        if (header):
            keys = row.keys()
            header = False
            csvwriter.writerow(keys)
        values = row.values()
        csvwriter.writerow(values)
    sheet.close()  
    return True

def ArchiveSheet(filename, verbose):
    return True

def Export(etype, filename, verbose):
    d, t = GetDefaults(verbose)
    if (filename =="" or filename == "enter filename"):
        filename = etype
    if "export dir" in d:
        desktop = d['export dir']
    else:
        desktop = "/home/{0}/Desktop".format(getpass.getuser())
    options = {}
    options['defaultextension'] = ".csv"
    options['filetypes'] = [('Text CSV (.csv)','*.csv'),]
    options['initialdir'] = desktop
    options['initialfile'] = filename
    options['title'] = "Saving {0} as a spreadsheet".format(etype)
    root = Tk()
    root.withdraw()
    filename = filedialog.asksaveasfilename(parent=root, **options)
    root.destroy()
    log = ""
    if len(filename ) > 0:
        log = "Now saving under {0}".format(filename)
        if (etype == "activity"):
            result = ActivitySheet(filename, verbose)
        elif (etype == "portfolio"):
            result = FolderSheet(filename, verbose)
        else:
            result = ArchiveSheet(filename, verbose)
        if (verbose):
            if (result):
                print ("file saved.")
            else:
                print ("failed.")
    else:
        log = "save was cancelled."
    return log

def Archive(verbose):
    return True
#endregion history
#region names
def GetNames(verbose):
    defaults, types = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/names.db"
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (verbose):
        print ("***")
        print ("GetNames(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("GetNames(2) {0} file is missing, cannot return the names".format(db_file))
            print ("***\n")
        return []
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("GetNames(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("GetNames(4) {0}".format(e))
        return []
    c = conn.cursor()
    c.execute("SELECT * FROM names order by pretty_name")
    keys = list(map(lambda x: x[0].replace("_"," "), c.description))
    values = c.fetchall()
    conn.close()
    if (verbose):
        print ("***\n")
    answer = []
    for row in values:
        answer.append(dict(zip(keys, row)))
    return answer

def DeleteName(pretty, verbose):
    username = getpass.getuser()
    db_file = username + "/names.db"
    db_remove = ""
    names = GetNames(verbose)
    for name in names:
        if (name["pretty name"] == pretty):
            db_remove =  username + "/" + name["db name"]
            break
    if (verbose):
        print ("***")
        print ("DeleteName(1) pretty: {0}".format(pretty))
        print ("DeleteName(2) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("DeleteName(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("DeleteName(4) {0}".format(e))
        return False
    c = conn.cursor()
    c.execute("DELETE FROM names where pretty_name = (?)", (pretty,))
    conn.commit()
    conn.close()
    if (os.path.exists(db_remove)):
        os.unlink(db_remove)
        if (verbose):
            print ("DeleteName(5), remove {0}".format(db_remove))
    if (verbose):
        print ("***\n")
    return True

def CreateNames(pretty, verbose):
    db_name = pretty.replace(" ", "_")
    db_name += ".db"
    username = getpass.getuser()
    db_file = username + "/names.db"
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (verbose):
        print ("***")
        print ("CreateNames(1) pretty_name: {0}".format(pretty))
        print ("CreateNames(1) db_name: {0}".format(db_name))
        print ("CreateNames(1) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("CreateNames(2) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("CreateNames(3) {0}".format(e))
        return False
    c = conn.cursor()
    c.execute("CREATE TABLE if not exists `names` ( `pretty_name` TEXT NOT NULL UNIQUE, `db_name` TEXT, PRIMARY KEY(`pretty_name`) )")
    c.execute( "INSERT OR IGNORE INTO names(pretty_name) VALUES((?))", (pretty,))
    c.execute("UPDATE names SET db_name = (?) WHERE pretty_name = (?)", (db_name, pretty,))
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    return True

def CheckPretty(ex):
    ex = ex.rstrip()
    if re.match(r'^[a-zA-Z0-9][ A-Za-z0-9_-]*$', ex):
        return True
    return False

def GetDB(verbose):
    db_file = ""
    defaults, types = GetDefaults(verbose)
    if ("folder name" in defaults):
        username = getpass.getuser()
        db_file = username + "/"  + defaults['folder name']
    names = GetNames(verbose)
    for name in names:
        if (name["pretty name"] == defaults['folder name']):
            db_file =  username + "/" + name["db name"]
            break
    return db_file
#endregion names
