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

#region stock
def Quote(ticker, verbose):
    result = {}
    defaults = GetDefaults(verbose)
    url = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={0}&interval={1}min&apikey={2}".format(ticker, defaults['interval'], defaults['api key'])
    if (verbose):
        print ("***")
        print ("Quote(1) ticker: {0}".format(ticker))
        print ("Quote(2) interval: {0}".format(defaults['interval']))
        print ("Quote(3) key: {0}".format(defaults['api key']))
        print ("Quote(4) URL: {0}".format(url))
    try:
        with contextlib.closing(urllib.request.urlopen(url)) as page:
            soup = BeautifulSoup(page, "html5lib")
    except urllib.error.HTTPError as err:
        result['exception'] = err
        result['status'] = False
        if err.code == 404:
            if (verbose):
                print ("Quote(5) page not found for {0}".format(ticker))
                print ("***\n")
            return result
        elif err.code == 503:
            if (verbose):
                print ("Quote(6) service unavailable for {0}".format(ticker))
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
                    dt = datetime.datetime.strptime(key, '%Y-%m-%d %H:%M:%S')
                    closing['price time'] = dt.strftime('%m/%d/%y %H:%M')
                    closing['price'] =  value['4. close']
                    break
        if "Meta Data" in returnQuote:
            closing['symbol'] = returnQuote['Meta Data']['2. Symbol']
            closing['status'] = True
        else:
            closing['exception'] = returnQuote
            closing['status'] = False
    return closing

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

def Key(key, verbose):
    username = getpass.getuser()
    db_file = os.getcwd() + "/"  + "defaults.db"
    if (verbose):
        print ("***")
        print ("Key(1) key: {0}".format(key))
        print ("Key(2) dbase: {0}".format(db_file))
    result = CreateDefaults(verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("Key(3) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("Key(4) {0}".format(e))
            return False
        c = conn.cursor()
        c.execute("UPDATE defaults SET api_key = (?) WHERE username = (?)", (key, username,))
        conn.commit()
        conn.close()
    if (verbose):
        print ("***\n")
    return True

def Interval(interval, verbose):
    username = getpass.getuser()
    db_file = os.getcwd() + "/"  + "defaults.db"
    if (verbose):
        print ("***")
        print ("Interval(1) interval: {0}".format(interval))
        print ("Interval(2) dbase: {0}".format(db_file))
    result = CreateDefaults(verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("Interval(3) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("Interval(4) {0}".format(e))
            return False
        c = conn.cursor()
        c.execute("UPDATE defaults SET interval = ? WHERE username = (?)", (interval, username,))
        conn.commit()
        conn.close()
    if (verbose):
        print ("***\n")
    return True

def Daemon(seconds, verbose):
    username = getpass.getuser()
    db_file = os.getcwd() + "/"  + "defaults.db"
    if (verbose):
        print ("***")
        print ("Daemon(1) seconds: {0}".format(seconds))
        print ("Daemon(2) dbase: {0}".format(db_file))
    result = CreateDefaults(verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("Daemon(3) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("Daemon(4) {0}".format(e))
            return False
        c = conn.cursor()
        c.execute("UPDATE defaults SET daemon_seconds = ? WHERE username = (?)", (seconds, username,))
        conn.commit()
        conn.close()
    if (verbose):
        print ("***\n")
    return True

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
        return ""
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("GetDefaults(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("GetDefaults(4) {0}".format(e))
        return False
    c = conn.cursor()
    c.execute("SELECT * FROM defaults WHERE username = (?)", (username,))
    keys = list(map(lambda x: x[0].replace("_"," "), c.description))
    values = c.fetchone()
    answer = dict(zip(keys, values))
    conn.close()
    if (verbose):
        print ("***\n")
    return answer

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
    c.execute("CREATE TABLE if not exists 'defaults' ( `username` TEXT NOT NULL UNIQUE, `api_key` TEXT, `interval` INTEGER, `daemon_seconds` INTEGER, `open` TEXT, `close` TEXT, `aim_db` TEXT, `folder_db` TEXT, `test_root` TEXT, `cash` REAL, `stocks` REAL, `start` TEXT, PRIMARY KEY(`username`) )")
    c.execute( "INSERT OR IGNORE INTO defaults(username) VALUES((?))", (username,))
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    return True

def Begin(begin, verbose):
    username = getpass.getuser()
    db_file = os.getcwd() + "/"  + "defaults.db"
    if (verbose):
        print ("***")
        print ("Begin(1) begin: {0}".format(begin))
        print ("Begin(2) dbase: {0}".format(db_file))
    result = CreateDefaults(verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("Begin(3) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("Begin(4) {0}".format(e))
            return False
        c = conn.cursor()
        c.execute("UPDATE defaults SET open = (?) WHERE username = (?)", (begin, username,))
        conn.commit()
        conn.close()
    if (verbose):
        print ("***\n")
    return True

def End(end, verbose):
    username = getpass.getuser()
    db_file = os.getcwd() + "/"  + "defaults.db"
    if (verbose):
        print ("***")
        print ("End(1) end: {0}".format(end))
        print ("End(2) dbase: {0}".format(db_file))
    result = CreateDefaults(verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("End(3) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("End(4) {0}".format(e))
            return False
        c = conn.cursor()
        c.execute("UPDATE defaults SET close = (?) WHERE username = (?)", (end, username,))
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
        return ""
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("PrintDefaults(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("PrintDefaults(4) {0}".format(e))
        return ""
    c = conn.cursor()
    c.execute("SELECT * FROM defaults")
    keys = list(map(lambda x: x[0].replace("_"," "), c.description))
    rows = c.fetchall()
    conn.commit()
    conn.close()
    keys.remove('interval')
    keys.remove('daemon seconds')
    TableCls = create_table('TableCls')
    for key in keys:
        TableCls.add_column(key, Col(key))
    items = []
    answer = {}
    for row in rows:
        col_list = []
        for i in range(len(row)):
            if (i != 2 and i != 3):
                if (i == 9 or i == 10):
                    col_list.append(as_currency(row[i]))
                else:
                    col_list.append(row[i])
        answer = dict(zip(keys, col_list))
        items.append(answer)
    table = TableCls(items, html_attrs = {'width':'100%','border-spacing':0})
    if (verbose):
        print ("***\n")
    return table.__html__()
#endregion stock

#region folder
def Add(symbol, verbose):
    defaults = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/"  + defaults['folder db']
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
    if (verbose):
        print ("***\n")
    return True

def Remove(symbol, verbose):
    defaults = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/"  + defaults['folder db']
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

def Cash(balance, verbose):
    defaults = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/"  + defaults['folder db']
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
        c.execute("UPDATE folder SET balance = ? WHERE symbol = '$'", (math.ceil(float(balance)-.4),))
        dict_string = {'companyName': 'CASH', 'description': 'Cash Account', 'symbol': '$'}
        json_string = json.dumps(dict_string)
        c.execute("UPDATE folder SET json_string = (?) WHERE symbol = '$'", (json_string,))
        c.execute("UPDATE folder SET shares = ? WHERE symbol = '$'", (math.ceil(float(balance)-.4),))
        dt = datetime.datetime.now()
        c.execute("UPDATE folder SET update_time = (?) WHERE symbol = '$'", (dt.strftime("%m/%d/%y %H:%M"),))
        c.execute("UPDATE folder SET price_time = (?) WHERE symbol = '$'", (dt.strftime("%m/%d/%y %H:%M"),))
        c.execute("UPDATE folder SET price = 1.00 WHERE symbol = '$'")
        conn.commit()
        conn.close()
    if (verbose):
        print ("***\n")
    return True

def CreateFolder(key, verbose):
    defaults = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/"  + defaults['folder db']
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
    defaults = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/"  + defaults['folder db']
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
    resultAdd = Add(symbol, verbose)
    if (resultAdd):
        price = Quote(symbol, verbose)
        if (price['status']):
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
            c.execute("UPDATE folder SET shares = ? WHERE symbol = (?)", (round(float(shares), 2), symbol,))
            c.execute("UPDATE folder SET price_time = (?) WHERE symbol = (?)", (price['price time'], symbol,))
            c.execute("UPDATE folder SET price = ? WHERE symbol = (?)", (float(price['price']), symbol,))
            balance = float(shares) * float(price['price'])
            c.execute("UPDATE folder SET balance = ? WHERE symbol = (?)", (math.ceil(balance-.4), symbol,))
            dt = datetime.datetime.now()
            c.execute("UPDATE folder SET update_time = (?) WHERE symbol = (?)", (dt.strftime("%m/%d/%y %H:%M"), symbol,))
            conn.commit()
            conn.close()
        else:
            result['exception'] = price['exception']
            result['status'] = False
            result['balance'] = 0
            return result
    else:
        if (verbose):
            print ("***\n")
        result['status'] = False
        result['balance'] = 0
        result['exception'] = "Error on Add()"
        return result
    if (verbose):
        print ("***\n")
    result['status'] = True
    result['balance'] = balance
    return result

def Balance(symbol, balance, verbose):
    result = {}
    defaults = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/"  + defaults['folder db']
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
    resultAdd = Add(symbol, verbose)
    if (resultAdd):
        price = Quote(symbol, verbose)
        if (price['status']):
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
            shares = 1.0
            if float(price['price']) > 0:
                shares = float(balance) / float(price['price'])
            c.execute("UPDATE folder SET shares = ? WHERE symbol = (?)", (round(shares,2), symbol,))
            c.execute("UPDATE folder SET price_time = (?) WHERE symbol = (?)", (price['price time'], symbol,))
            c.execute("UPDATE folder SET price = ? WHERE symbol = (?)", (float(price['price']), symbol,))
            c.execute("UPDATE folder SET balance = ? WHERE symbol = (?)", (math.ceil(float(balance)-.4), symbol,))
            dt = datetime.datetime.now()
            c.execute("UPDATE folder SET update_time = (?) WHERE symbol = (?)", (dt.strftime("%m/%d/%y %H:%M"), symbol,))
            conn.commit()
            conn.close()
        else:
            result['exception'] = price['exception']
            result['status'] = False
            result['shares'] = 0
            return result
    else:
        if (verbose):
            print ("***\n")
        result['status'] = False
        result['shares'] = 0
        result['exception'] = "Error on Add()"
        return result
    if (verbose):
        print ("***\n")
    result['status'] = True
    result['shares'] = shares
    return result

def Update(verbose):
    defaults = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/"  + defaults['folder db']
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (verbose):
        print ("***")
        print ("Update(1) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("Update(2) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("Update(3) {0}".format(e))
        return False, e
    c = conn.cursor()
    c.execute("SELECT symbol, shares, balance FROM folder where symbol != '$'") 
    rows = c.fetchall()
    conn.commit()
    conn.close()
    for row in rows:
        result = Shares(row[0], str(row[1]), verbose)
        if (result['status']):
            if (verbose):
                print ("symbol: {0}, current shares: {1}, previous balance: {2}, current balance: {3}".format(row[0], row[1], row[2], result['balance']))
    if (verbose):
        print ("***\n")
    return True, ""

def Folder(folder, verbose):
    username = getpass.getuser()
    db_file = os.getcwd() + "/"  + "defaults.db"
    if (verbose):
        print ("***")
        print ("Folder(1) folder: {0}".format(folder))
        print ("Folder(2) dbase: {0}".format(db_file))
    result = CreateDefaults(verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("Folder(3) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("Folder(4) {0}".format(e))
            return False
        c = conn.cursor()
        c.execute("UPDATE defaults SET folder_db = (?) WHERE username = (?)", (folder, username,))
        conn.commit()
        conn.close()
    if (verbose):
        print ("***\n")
    return True

def GetFolderCash(verbose):
    defaults = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/"  + defaults['folder db']
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

def GetFolderStockValue(verbose):
    defaults = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/"  + defaults['folder db']
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
    c.execute("SELECT * FROM folder WHERE symbol != '$'")
    rows = c.fetchall()
    conn.commit()
    conn.close()
    answer = 0
    for row in rows:
        answer += row[2]
    if (verbose):
        print ("***\n")
    return answer

def PrintFolder(verbose):
    defaults = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/"  + defaults['folder db']
    if (verbose):
        print ("***")
        print ("PrintFolder(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("PrintFolder(2) {0} file is missing, cannot print".format(db_file))
            print ("***\n")
        return ""
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("PrintFolder(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("PrintFolder(4) {0}".format(e))
        return ""
    c = conn.cursor()
    c.execute("SELECT * FROM folder")
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
    for row in rows:
        json_string = json.loads(row[1])
        col_list = []
        for i in range(len(keys)):
            if (i == 1):
                col_list.append(json_string['companyName'])
            else:
                if (i == 2 or i == 6):
                    col_list.append(as_currency(row[i]))
                else:
                    col_list.append(row[i])
        answer = dict(zip(keys, col_list))
        items.append(answer)
    table = TableCls(items, html_attrs = {'width':'100%','border-spacing':0})
    if (verbose):
        print ("***\n")
    return table.__html__()

def PrintPercent(verbose):
    defaults = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/"  + defaults['folder db']
    if (verbose):
        print ("***")
        print ("PrintPercent(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("PrintPercent(2) {0} file is missing, cannot print".format(db_file))
            print ("***\n")
        return ""
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("PrintPercent(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("PrintPercent(4) {0}".format(e))
        return ""
    c = conn.cursor()
    c.execute("SELECT * FROM folder where symbol != '$'")
    rows = c.fetchall()
    conn.commit()
    conn.close()
    total = 0
    for row in rows:
        total = total + row[2]
    total = math.ceil(total -.4)
    answer = ""
    for row in rows:
        pst = int(row[2] / total * 100.+.4)
        answer = answer + "<li>{0} {1}%</li>".format(row[0], pst)
        
    return answer
#endregion folder

#region aim
def AIM(aim, verbose):
    username = getpass.getuser()
    db_file = os.getcwd() + "/"  + "defaults.db"
    if (verbose):
        print ("***")
        print ("AIM(1) aim: {0}".format(aim))
        print ("AIM(2) dbase: {0}".format(db_file))
    result = CreateDefaults(verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("AIM(3) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("AIM(4) {0}".format(e))
            return False
        c = conn.cursor()
        c.execute("UPDATE defaults SET aim_db = (?) WHERE username = (?)", (aim, username,))
        conn.commit()
        conn.close()
    if (verbose):
        print ("***\n")
    return True

def Directory(location, verbose):
    if (not location.endswith("/")):
        location = location + "/"
    username = getpass.getuser()
    db_file = os.getcwd() + "/"  + "defaults.db"
    if (verbose):
        print ("***")
        print ("Directory(1) location: {0}".format(location))
        print ("Directory(2) dbase: {0}".format(db_file))
    result = CreateDefaults(verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("Directory(3) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("Directory(4) {0}".format(e))
            return False
        c = conn.cursor()
        c.execute("UPDATE defaults SET test_root = (?) WHERE username = (?)", (location, username,))
        conn.commit()
        conn.close()
    if (verbose):
        print ("***\n")
    return True

def AIMCash(cash, verbose):
    username = getpass.getuser()
    db_file = os.getcwd() + "/"  + "defaults.db"
    if (verbose):
        print ("***")
        print ("AIMCash(1) cash: {0}".format(cash))
        print ("AIMCash(2) dbase: {0}".format(db_file))
    result = CreateDefaults(verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("AIMCash(3) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("AIMCash(4) {0}".format(e))
            return False
        c = conn.cursor()
        c.execute("UPDATE defaults SET cash = ? WHERE username = (?)", (cash, username,))
        conn.commit()
        conn.close()
    if (verbose):
        print ("***\n")
    return True

def AIMStock(stock, verbose):
    username = getpass.getuser()
    db_file = os.getcwd() + "/"  + "defaults.db"
    if (verbose):
        print ("***")
        print ("AIMStock(1) stockvalue: {0}".format(stock))
        print ("AIMStock(2) dbase: {0}".format(db_file))
    result = CreateDefaults(verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("AIMStock(3) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("AIMStock(4) {0}".format(e))
            return False
        c = conn.cursor()
        c.execute("UPDATE defaults SET stocks = ? WHERE username = (?)", (stock, username,))
        conn.commit()
        conn.close()
    if (verbose):
        print ("***\n")
    return True

def AIMDate(verbose):
    username = getpass.getuser()
    db_file = os.getcwd() + "/"  + "defaults.db"
    if (verbose):
        print ("***")
        print ("AIMDate(1) dbase: {0}".format(db_file))
    result = CreateDefaults(verbose)
    if (result):
        defaults = GetDefaults(verbose)
        if myFloat(defaults['cash']) == 0:
            log = "AIMDate(2) an AIM cash balance is required"
            if (verbose):
                print (log)
            return False, log 
        if myFloat(defaults['stocks']) == 0:
            log = "AIMDate(2) an AIM stock value balance is required"
            if (verbose):
                print (log)
            return False, log 
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("AIMDate(4) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("AIMDate(5) {0}".format(e))
            return False, e
        c = conn.cursor()
        cd = datetime.datetime.now()
        c.execute("UPDATE defaults SET start = (?) WHERE username = (?)", (cd.strftime("%Y/%m/%d"), username,))
        conn.commit()
        conn.close()
        resultCreate = CreateAIM(verbose)
        if (not resultCreate):
            if (verbose):
                print ("Error when creating aim database/table")
            return False
    if (verbose):
        print ("***\n")
    return True, ""

def CreateAIM(verbose):
    defaults = GetDefaults(verbose)
    pv = defaults['stocks'] + defaults['cash']
    username = getpass.getuser()
    db_file = username + "/"  + defaults['aim db']
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
        return False
    c = conn.cursor()
    c.execute("CREATE TABLE if not exists `aim` ( `post_date` TEXT NOT NULL UNIQUE, `stock_value` REAL, `cash` REAL, `portfolio_control` REAL, `buy_sell_advice` REAL, `market_order` REAL, `portfolio_value` REAL )")
    c.execute("DELETE FROM aim")
    c.execute( "INSERT INTO aim VALUES((?),?,?,?,?,?,?)", ("1970/01/01", defaults['stocks'], defaults['cash'], defaults['stocks'], 0, 0, pv,))
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    return True

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

def GetLastAIM(verbose):
    defaults = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/"  + defaults['aim db']
    if (verbose):
        print ("***")
        print ("GetLastAIM(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("GetLastAIM(2) {0} file is missing, cannot return the last row".format(db_file))
            print ("***\n")
        return {}
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("GetLastAIM(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("GetLastAIM(4) {0}".format(e))
        return {}
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
    defaults = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/"  + defaults['aim db']
    if (verbose):
        print ("***")
        print ("GetAIMNotes(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("GetAIMNotes(2) {0} file is missing, cannot return the notes".format(db_file))
            print ("***\n")
        return {}
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("GetAIMNotes(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("GetAIMNotes(4) {0}".format(e))
        return {}
    c = conn.cursor()
    c.execute("SELECT * FROM aim ORDER BY post_date DESC LIMIT ?", (count,))
    keys = list(map(lambda x: x[0].replace("_"," "), c.description))
    rows = c.fetchall()
    conn.close()
    notes = []
    for row in rows:
        note = {}
        answer = dict(zip(keys, row))
        if (answer['post date'] == "1970/01/01"):
            note['date'] = defaults['start']
            note['content'] = "A.I.M. was initialized with {0}".format(as_currency(defaults['cash'] + defaults['stocks']))            
        else:
            note['date'] = answer['post date']
            if (answer['market order'] == 0):
                note['content'] = "holds current position."
            elif (answer['market order'] < 0):
                note['content'] = "sold {0} of folder".format(as_currency(answer['market order']))
            else:
                note['content'] = "purchased {0} for folder".format(as_currency(answer['market order']))
        notes.append(note)
    if (verbose):
        print ("***\n")
    return notes

def GetFirstAIM(verbose):
    defaults = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/"  + defaults['aim db']
    if (verbose):
        print ("***")
        print ("GetFirstAIM(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("GetFirstAIM(2) {0} file is missing, cannot return the first row".format(db_file))
            print ("***\n")
        return {}
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("GetFirstAIM(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("GetFirstAIM(4) {0}".format(e))
        return {}
    c = conn.cursor()
    c.execute("SELECT * FROM aim where post_date = '1970/01/01'")
    keys = list(map(lambda x: x[0].replace("_"," "), c.description))
    values = c.fetchone()
    answer = dict(zip(keys, values))
    conn.close()
    if (verbose):
        print ("***\n")
    return answer

def as_currency(amount):
    if amount >= 0:
        return '${:,.2f}'.format(amount)
    else:
        return '(${:,.2f})'.format(-amount)

def as_percent(amount):
    if amount >= 0:
        return "{0:.0f}%".format(amount)
    else:
        return '({0:.0f}%)'.format(-amount)

def Look(verbose):
    first = GetFirstAIM(verbose)
    prev = GetLastAIM(verbose)
    prev_pc = math.ceil(prev['portfolio control'] -.4)
    db_keys = prev.keys()
    keys = []
    for key in db_keys:
        if (key == 'cash'):
            keys.append("safe") # safe is not in the aim db (want to see it though)
        keys.append(key)
    cd = datetime.datetime.now()
    stock = math.ceil(GetFolderStockValue(verbose) -.4)
    cash = math.ceil(GetFolderCash(verbose) -.4)
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
    pretty = dict(zip(keys, values))
    answer_db = dict(zip(keys, values_db))
    TableCls = create_table('TableCls')
    for key in keys:
        TableCls.add_column(key, Col(key))
    items = []
    items.append(pretty)
    table = TableCls(items, html_attrs = {'width':'100%','border-spacing':0})
    pct_cash = int(cash / pv * 100. +.4)
    pct_stock = int(stock / pv * 100. +.4)
    pretty['initial value'] = as_currency(first['portfolio value'])
    pretty['profit value'] = as_currency(pv - first['portfolio value'])
    pretty['profit percent'] = as_percent(int((pv - first['portfolio value']) / pv * 100. +.4))
    pretty['percent list'] = "<li> Cash {0}%</li><li> Stock {1}%</li>".format(pct_cash, pct_stock)
    return pretty, table.__html__(), answer_db

def Post(verbose):
    defaults = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/"  + defaults['aim db']
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
    look, table, db_values = Look(verbose)
    if (verbose):
        print("Post(5) {0}".format(look))
    c = conn.cursor()
    c.execute( "INSERT OR IGNORE INTO aim(post_date) VALUES((?))", (db_values['post date'],))
    c.execute("UPDATE aim SET stock_value = ? WHERE post_date = (?)", (db_values['stock value'], db_values['post date'],))
    c.execute("UPDATE aim SET cash = ? WHERE post_date = (?)", (db_values['cash'], db_values['post date'],))
    c.execute("UPDATE aim SET portfolio_control = ? WHERE post_date = (?)", (db_values['portfolio control'], db_values['post date'],))
    c.execute("UPDATE aim SET buy_sell_advice = ? WHERE post_date = (?)", (db_values['buy sell advice'], db_values['post date'],))
    c.execute("UPDATE aim SET market_order = ? WHERE post_date = (?)", (db_values['market order'], db_values['post date'],))
    c.execute("UPDATE aim SET portfolio_value = ? WHERE post_date = (?)", (db_values['portfolio value'], db_values['post date'],))
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    return True

def PrintAIM(printyear, verbose):
    if (printyear[0] == 'a'):
        intyear = 1970
    else:
        intyear = int(printyear)
        if (intyear < 100):
            intyear = 2000 + intyear
        printyear = str(intyear)
    defaults = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/"  + defaults['aim db']
    if (verbose):
        print ("***")
        print ("PrintAIM(1) dbase: {0}".format(db_file))
        print ("PrintAIM(2) year: {0}".format(printyear))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("PrintAIM(3) {0} file is missing, cannot print".format(db_file))
            print ("***\n")
        return ""
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("PrintAIM(4) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("PrintAIM(5) {0}".format(e))
        return ""
    c = conn.cursor()
    c.execute("SELECT * FROM aim")
    keys_db = list(map(lambda x: x[0].replace("_"," "), c.description))
    rows = c.fetchall()
    conn.commit()
    conn.close()
    keys = []
    for key in keys_db:
        if (key == 'cash'):
            keys.append("safe") # safe is not in the aim db (want to see it though)
        keys.append(key)
    TableCls = create_table('TableCls')
    for key in keys:
        TableCls.add_column(key, Col(key))
    items = []
    answer = {}
    for row in rows:
        dt = datetime.datetime.strptime(row[0], '%Y/%m/%d')
        if (intyear == 1970 or dt.year == intyear):
            col_list = []
            for i in range(len(keys)):
                if (i == 0):
                    if (intyear == 1970):
                        col_list.append(dt.strftime("%b, %d %Y"))
                    else:
                        col_list.append(dt.strftime("%b, %d"))
                elif (i == 1):
                    col_list.append(as_currency(row[i]))
                elif (i == 2):
                    stock = math.ceil(GetFolderStockValue(verbose) -.4)
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
    defaults =  GetDefaults(False)
    if (verbose):
        print ("***")
        print ("\tRunning tests will preserve your API key")
        print ("\tbut will reset everything else back to default settings.")
        print ("***\n")
        print ("Test #1 - Company('AAPL', verbose)")
    result = Company("AAPL", verbose)
    if (result['companyName'] == "Apple Inc."):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #2 - Key('TEST', verbose)")
    result = Key("TEST", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #3 - Interval(15, False)")
    result = Interval(15, False)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #4 - Daemon(1200, False)")
    result = Daemon(1200, False)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #5 - Begin('8:30AM', False)")
    result = Begin("8:30AM", False)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #6 - End('03:00PM', False)")
    result = End("03:00PM", False)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #7 - Folder('folder.db', False)")
    result = Folder("folder.db", False)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #8 - AIM('aim.db', False)")
    result = AIM("aim.db", False)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #9 - Directory('test/', False)")
    result = Directory("test/", False)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #10 - Quote('AAPL', verbose)")
    result = Quote("AAPL", verbose)
    if (result['status'] and result['symbol'] == "AAPL"):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #11 - GetDefaults(False)")
    result = GetDefaults(False)
    if (result['api key'] == "TEST"
        and result['interval'] == 15
        and result['daemon seconds'] == 1200
        and result['open'] == "8:30AM"
        and result['close'] == "03:00PM"
        and result['folder db'] == "folder.db"
        and result['aim db'] == "aim.db"
        and result['test root'] == "test/"):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #12 - Key(<reset key back>, False)")
    result = Key(defaults['api key'], False)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (count == 12):
        return True
    return False

def TestFolder(verbose):
    count = 0
    defaults = GetDefaults(verbose)
    if (verbose):
        print ("Test #1 - Folder('test.db', verbose)")
    result = Folder("test.db", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #2 - Cash(5000, verbose)")
    result = Cash(5000, verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #3 - Balance('AAPL', 5000, verbose)")
    result = Balance("AAPL", 5000, verbose)
    if (result['status']):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #4 - Shares('AAPL', 50, verbose)")
    result = Shares("AAPL", 50, verbose)
    if (result['status']):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #5 - Update(verbose)")
    result = Update(verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #6 - Remove('AAPL', verbose)")
    result = Remove("AAPL", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    username = getpass.getuser()
    db_file = username + "/" + "test.db"
    if (os.path.exists(db_file)):
        os.unlink(db_file)
        if (verbose):
            print ("Cleanup, remove {0}".format(db_file))
    if (verbose):
        print ("Test #7 - Folder(<reset back db name>, verbose)")
    result = Folder(defaults['folder db'], verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (count == 7):
        return True
    return False

def TestAIM(location, verbose):
    count = 0
    defaults = GetDefaults(False)
    status, keys, rows = LoadTest(location, verbose)
    if (status and (defaults is not None)):
        if (verbose):
            print ("Test #{0} - AIM('test.db', verbose)".format(count + 1))
        result = AIM("test.db", verbose)
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
        db_file = username + "/" + "test.db"
        if (os.path.exists(db_file)):
            os.unlink(db_file)
            if (verbose):
                print ("Cleanup, remove {0}".format(db_file))
        if (verbose):
            print ("Test #{0} - AIM(<reset back db name>, verbose)".format(count + 1))
        result = AIM(defaults['aim db'], verbose)
        if (result):
            if (verbose):
                print ("\tpass.")
            count += 1
        else:
            if (verbose):
                print ("\tfail.")
        if (count == 452):
            return True
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
    defaults = GetDefaults(False)
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
