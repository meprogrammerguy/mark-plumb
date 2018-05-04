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

#region stock
def Quote(ticker, verbose):
    result = {}
    defaults = GetDefaults(verbose)
    url = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={0}&interval={1}min&apikey={2}".format(ticker, defaults['interval'], defaults['api_key'])
    if (verbose):
        print ("***")
        print ("Quote(1) ticker: {0}".format(ticker))
        print ("Quote(2) interval: {0}".format(defaults['interval']))
        print ("Quote(3) key: {0}".format(defaults['api_key']))
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
                    closing['price_time'] = key
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
    keys = list(map(lambda x: x[0], c.description))
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
    c.execute("CREATE TABLE if not exists 'defaults' ( `username` TEXT NOT NULL UNIQUE, `api_key` TEXT, `interval` INTEGER, `folder_dbase` TEXT, `daemon_seconds` INTEGER, `begin_time` TEXT, `end_time` TEXT, `aim_dbase` TEXT, `test_directory` TEXT, PRIMARY KEY(`username`) )")
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
        c.execute("UPDATE defaults SET begin_time = (?) WHERE username = (?)", (begin, username,))
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
        c.execute("UPDATE defaults SET end_time = (?) WHERE username = (?)", (end, username,))
        conn.commit()
        conn.close()
    if (verbose):
        print ("***\n")
    return True
#endregion stock

#region folder
def Add(symbol, verbose):
    defaults = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/"  + defaults['folder_dbase']
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
        c.execute("UPDATE folder SET update_time = (?) WHERE symbol = (?)", (datetime.datetime.now(), symbol,))
        conn.commit()
        conn.close()
    if (verbose):
        print ("***\n")
    return True

def Remove(symbol, verbose):
    defaults = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/"  + defaults['folder_dbase']
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
    db_file = username + "/"  + defaults['folder_dbase']
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
        c.execute("UPDATE folder SET balance = ? WHERE symbol = '$'", (float(balance),))
        dict_string = {'companyName': 'CASH', 'description': 'Cash Account', 'symbol': '$'}
        json_string = json.dumps(dict_string)
        c.execute("UPDATE folder SET json_string = (?) WHERE symbol = '$'", (json_string,))
        c.execute("UPDATE folder SET shares = ? WHERE symbol = '$'", (float(balance),))
        c.execute("UPDATE folder SET update_time = (?) WHERE symbol = '$'", (datetime.datetime.now(),))
        c.execute("UPDATE folder SET price_time = (?) WHERE symbol = '$'", (datetime.datetime.now(),))
        c.execute("UPDATE folder SET price = 1.00 WHERE symbol = '$'")
        conn.commit()
        conn.close()
    if (verbose):
        print ("***\n")
    return True

def CreateFolder(key, verbose):
    defaults = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/"  + defaults['folder_dbase']
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
    db_file = username + "/"  + defaults['folder_dbase']
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
            c.execute("UPDATE folder SET shares = ? WHERE symbol = (?)", (shares, symbol,))
            c.execute("UPDATE folder SET price_time = (?) WHERE symbol = (?)", (price['price_time'], symbol,))
            c.execute("UPDATE folder SET price = ? WHERE symbol = (?)", (float(price['price']), symbol,))
            balance = float(shares) * float(price['price'])
            c.execute("UPDATE folder SET balance = ? WHERE symbol = (?)", (float(balance), symbol,))
            c.execute("UPDATE folder SET update_time = (?) WHERE symbol = (?)", (datetime.datetime.now(), symbol,))
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
    db_file = username + "/"  + defaults['folder_dbase']
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
            c.execute("UPDATE folder SET shares = ? WHERE symbol = (?)", (shares, symbol,))
            c.execute("UPDATE folder SET price_time = (?) WHERE symbol = (?)", (price['price_time'], symbol,))
            c.execute("UPDATE folder SET price = ? WHERE symbol = (?)", (float(price['price']), symbol,))
            c.execute("UPDATE folder SET balance = ? WHERE symbol = (?)", (float(balance), symbol,))
            c.execute("UPDATE folder SET update_time = (?) WHERE symbol = (?)", (datetime.datetime.now(), symbol,))
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
    db_file = username + "/"  + defaults['folder_dbase']
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
    c.execute('SELECT symbol, shares, balance FROM folder') 
    rows = c.fetchall()
    conn.commit()
    conn.close()
    for row in rows:
        if (row[0] != "$"):
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
        c.execute("UPDATE defaults SET folder_dbase = (?) WHERE username = (?)", (folder, username,))
        conn.commit()
        conn.close()
    if (verbose):
        print ("***\n")
    return True
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
        c.execute("UPDATE defaults SET aim_dbase = (?) WHERE username = (?)", (aim, username,))
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
        c.execute("UPDATE defaults SET test_directory = (?) WHERE username = (?)", (location, username,))
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

def PortfolioValue(cash, stockvalue, verbose):
    if (verbose):
        print ("***")
        print ("PortfolioValue(1) cash: {0}".format(cash))
        print ("PortfolioValue(2) stockvalue: {0}".format(stockvalue))
        print ("***\n")
    return (cash + stockvalue) 
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
    if (result['api_key'] == "TEST"
        and result['interval'] == 15
        and result['daemon_seconds'] == 1200
        and result['begin_time'] == "8:30AM"
        and result['end_time'] == "03:00PM"
        and result['folder_dbase'] == "folder.db"
        and result['aim_dbase'] == "aim.db"
        and result['test_directory'] == "test/"):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #12 - Key(<reset key back>, False)")
    result = Key(defaults['api_key'], False)
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
    result = Folder(defaults['folder_dbase'], verbose)
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
            curr = dict(zip(keys, item[1]))
            prev = GetPrevious(index, keys, rows)
            if (verbose):
                print ("Test #{0} - Safe(<Stock Value>, verbose)".format(count + 1))
            result = Safe(float(curr['Stock Value']), verbose)
            if (result == float(curr['Safe'])):
                if (verbose):
                    print ("\tSafe({0}) - pass.".format(index))
                count += 1
            else:
                if (verbose):
                    print ("\tSafe({0}) - expected: {1}, calculated: {2}, fail.".format(index, curr['Safe'], result))
            if (verbose):
                print ("Test #{0} - PortfolioValue(<Cash>, <Stock Value>, verbose)".format(count + 1))
            result = PortfolioValue(float(curr['Cash']), float(curr['Stock Value']), verbose)
            if (result == float(curr['Portfolio Value'])):
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
        result = AIM(defaults['aim_dbase'], verbose)
        if (result):
            if (verbose):
                print ("\tpass.")
            count += 1
        else:
            if (verbose):
                print ("\tfail.")
        if (count == 184):
            return True
    return False

def GetPrevious(index, keys, rows):
    count = index - 1
    values = []
    if (count < 0):
        return {}
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
    test_dir = defaults['test_directory'] + location
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
