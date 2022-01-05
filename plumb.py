#!/usr/bin/env python3

import sys
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
import pytz
from dateutil import tz
import subprocess
import signal
from tkinter import *
from tkinter import filedialog
import http.client
from dateutil.tz import tzlocal
from tzlocal import get_localzone
from io import StringIO
import itertools
import ast

#region defaults
def QuoteTradier(quotes, verbose):
    answers = []
    defaults, types = GetDefaults(verbose)
    url = "/v1/markets/quotes?symbols={0}".format(quotes)
    if (verbose):
        print ("***")
        print ("QuoteTradier(1) URL: {0}".format(url))
        print ("QuoteTradier(2) token: {0}".format(defaults["tradier key"]))
    connection = http.client.HTTPSConnection('sandbox.tradier.com', 443, timeout = 30)

    headers = {}
    headers["Accept"] = "application/json"
    headers["Authorization"] = "Bearer {0}".format(defaults["tradier key"])
    headers["connection"] = "close"

    connection.request('GET', url, None, headers)
    try:
        response = connection.getresponse()
        content = response.read()
        content = content.decode("utf-8")
    except http.client.HTTPException as e:
        answer = {}
        answer['url'] = url
        answer["Error Message"] = e
        return answer
    if (verbose):
        pprint.pprint(content)
        print ("***\n")
    if ("Invalid Access Token" in content):
        answer = {}
        answer['url'] = url
        answer["Error Message"] = "Invalid Access Token"
        return answer
    content = json.loads(content)
    if "quote" in content['quotes']:
        for itm in content['quotes']['quote']:
            answer = {}
            if (itm == "symbol"):
                row = content['quotes']['quote']
            else:
                row = itm
            answer['symbol'] = row['symbol']
            if row['close'] is None:
                answer['quote'] = "last"
                answer['price'] = row['last']
            else:
                answer['quote'] = "close"
                answer['price'] = row['close']
            answer['url'] = url
            answer['description'] = row['description']
            answers.append(answer)
            if (itm == "symbol"):
                break
    else:
        answers.append(content)
    return answers

def QuoteCrypto(quotes, verbose):
    answers = []
    defaults, types = GetDefaults(verbose)
    url = "/v1/cryptocurrency/quotes/latest?symbol={0}&convert=USD".format(quotes)
    if (verbose):
        print ("***")
        print ("QuoteCrypto(1) URL: {0}".format(url))
        print ("QuoteCrypto(2) token: {0}".format(defaults["coin key"]))
    connection = http.client.HTTPSConnection('pro-api.coinmarketcap.com', 443, timeout = 30)

    headers = {}
    headers["Accepts"] = "application/json"
    headers["X-CMC_PRO_API_KEY"] = defaults["coin key"]
    headers["connection"] = "close"

    connection.request('GET', url, None, headers)
    try:
        response = connection.getresponse()
        content = response.read()
        content = content.decode("utf-8")
        content = json.loads(content)
    except http.client.HTTPException as e:
        answer = {}
        answer['url'] = url
        answer["Error Message"] = e
        return answer
    if (verbose):
        pprint.pprint(content)
        print ("***\n")
    if (content['status']['error_code'] != 0):
        answer = {}
        answer['url'] = url
        answer["Error Message"] = content['status']['error_message']
        return answer
    for itm in  quotes.upper().split(","):
        if itm in content['data']:
            row = content['data'][itm]["quote"]["USD"]
            answer = {}
            answer['symbol'] = content['data'][itm]["symbol"]
            answer['quote'] = "open"
            answer['price'] = row['price']
            answer['url'] = url
            answer['description'] = content['data'][itm]["name"]
            answers.append(answer)
        else:
            answer = {}
            answer['url'] = url
            answer['content'] = content
            answers.append(answer)
    return answers

def Holiday(verbose):
    url = "/v1/markets/calendar"
    if (verbose):
        print ("***")
        print ("Holiday(1) URL: {0}".format(url))
    dt = datetime.datetime.now()
    today = dt.strftime('%Y-%m-%d')
    defaults, types = GetDefaults(verbose)
    if defaults == {}:
        result = ResetDefaults(verbose)
        if (result):
            defaults, types =  GetDefaults(verbose)
    if ("market status" in defaults):
        js = defaults['market status']
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
        if (b"Invalid Access Token" in content):
            answer = {}
            answer['url'] = url
            answer["Error Message"] = "Invalid Access Token"
            return answer
        returnContent = json.loads(content.decode('utf-8'))
    except http.client.HTTPException as e:
        answer = {}
        answer['url'] = url
        answer["Error Message"] = e
        return answer
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
    defaults, types = GetDefaults(verbose)
    url = "https://cloud.iexapis.com/stable/stock/{0}/company?token={1}".format(ticker,defaults["IEX key"])
    if (verbose):
        print ("***")
        print ("Company(1) ticker: {0}".format(ticker))
        print ("Company(2) URL: {0}".format(url))
        print ("Company(3) token: {0}".format(defaults["IEX key"]))
    try:
        with contextlib.closing(urllib.request.urlopen(url)) as page:
            soup = BeautifulSoup(page, "html5lib")
    except urllib.error.HTTPError as err:
        if err.code == 404:
            if (verbose):
                print ("Company(4) page not found for {0}".format(ticker))
                print ("***\n")
            answer = {}
            answer['url'] = url
            answer["companyName"] = "page not found"
            return answer
        if err.code == 403:
            if (verbose):
                print ("Company(4) forbidden {0}".format(ticker))
                print ("***\n")
            answer = {}
            answer['url'] = url
            answer["companyName"] = "forbidden"
            return answer
        else:
            raise
    returnCompany = json.loads(str(soup.text))
    if (verbose):
        print (returnCompany)
        print ("***\n")
    return returnCompany

def CryptoCompany(ticker, verbose):
    defaults, types = GetDefaults(verbose)
    url = "/v1/cryptocurrency/info?symbol={0}".format(ticker)
    headers = {}
    headers["Accepts"] = "application/json"
    headers["X-CMC_PRO_API_KEY"] = defaults["coin key"]
    headers["connection"] = "close"
    connection = http.client.HTTPSConnection('pro-api.coinmarketcap.com', 443, timeout = 30)
    connection.request('GET', url, None, headers)
    if (verbose):
        print ("***")
        print ("CryptoCompany(1) ticker: {0}".format(ticker))
        print ("CryptoCompany(2) URL: {0}".format(url))
        print ("CryptoCompany(3) token: {0}".format(defaults["coin key"]))
    try:
        response = connection.getresponse()
        page = response.read()
        soup = BeautifulSoup(page, "html5lib")
    except urllib.error.HTTPError as err:
        if err.code == 404:
            if (verbose):
                print ("CryptoCompany(4) page not found for {0}".format(ticker))
                print ("***\n")
            answer = {}
            answer['url'] = url
            answer["companyName"] = "page not found"
            return answer
        if err.code == 403:
            if (verbose):
                print ("CryptoCompany(4) forbidden {0}".format(ticker))
                print ("***\n")
            answer = {}
            answer['url'] = url
            answer["companyName"] = "forbidden"
            return answer
        else:
            raise
    returnCompany = json.loads(str(soup.text))
    if (returnCompany['status']['error_code'] != 0):
        answer = {}
        answer['symbol'] = ticker
        answer['url'] = url
        answer["companyName"] = returnCompany['status']['error_message']
        answer['error_code'] = returnCompany['status']['error_code']
        return answer
    returnCompany['description'] =  returnCompany['data'][ticker.upper()]['description']
    returnCompany['symbol'] =  returnCompany['data'][ticker.upper()]['symbol']
    returnCompany['companyName'] =  returnCompany['data'][ticker.upper()]['name']
    returnCompany['website'] =  returnCompany['data'][ticker.upper()]['urls']['website']
    returnCompany['exchange'] =  "coinbase"
    if (verbose):
        print (returnCompany)
        print ("***\n")
    return returnCompany

def UpdateDefaultItem(key, item, verbose):
    key_db = key.replace(" ", "_")
    d, t = GetDefaults(verbose)
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
        pprint.pprint("UpdateDefaultItem(3) item: {0}".format(item))
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
        if key == "market status":
            item = json.dumps(item)
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
        snap = GetNextSnap(verbose)
        snap -= 1
        if snap < 1:
            snap = None
        opentime = MarketToTime("09:30", "US/Eastern", verbose)
        closetime = MarketToTime("16:00", "US/Eastern", verbose)
        desktop = "/home/{0}/Desktop".format(getpass.getuser())
        c = conn.cursor()
        c.execute("UPDATE defaults SET tradier_key = (?) WHERE username = (?)", ("demo", username,))
        c.execute("UPDATE defaults SET IEX_key = (?) WHERE username = (?)", ("demo", username,))
        c.execute("UPDATE defaults SET coin_key = (?) WHERE username = (?)", ("demo", username,))
        c.execute("UPDATE defaults SET poll_minutes = ? WHERE username = (?)", (10, username,))
        c.execute("UPDATE defaults SET open = (?) WHERE username = (?)", (opentime, username,))
        c.execute("UPDATE defaults SET close = (?) WHERE username = (?)", (closetime, username,))
        c.execute("UPDATE defaults SET test_root = (?) WHERE username = (?)", ("test/", username,))
        c.execute("UPDATE defaults SET export_dir = (?) WHERE username = (?)", (desktop, username,))
        c.execute("UPDATE defaults SET folder_name = (?) WHERE username = (?)", ("Practice Portfolio", username,))
        c.execute("UPDATE defaults SET market_status = (?) WHERE username = (?)", ("{}", username,))
        c.execute("UPDATE defaults SET snap_shot = ? WHERE username = (?)", (snap, username,))
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
    date = datetime.datetime.strptime(datestring,"%m/%d/%Y %H:%M:%S")
    utc = pytz.utc
    zone = pytz.timezone(theZone)
    local_tz = get_localzone() 
    date_est = zone.localize(date,is_dst=None)
    date_utc = date_est.astimezone(utc)
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
        return {}, {}
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("GetDefaults(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("GetDefaults(4) {0}".format(e))
        return {}, {}
    c = conn.cursor()
    c.execute("SELECT * FROM defaults WHERE username = (?) order by username", (username,))
    keys = list(map(lambda x: x[0].replace("_"," "), c.description))
    values = c.fetchone()
    c.execute('PRAGMA TABLE_INFO(defaults)')
    types = [tup[2] for tup in c.fetchall()]
    conn.close()
    answer = dict(zip(keys, values))
    answer['market status'] = json.loads(answer['market status']) 
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
    c.execute("CREATE TABLE if not exists 'defaults' ( `username` TEXT NOT NULL UNIQUE, `folder_name` NUMERIC, `snap_shot` INTEGER, `open` TEXT, `close` TEXT, `poll_minutes` INTEGER, `test_root` TEXT, `export_dir` TEXT, `tradier_key` TEXT, `IEX_key` TEXT, `coin_key` TEXT, `market_status` TEXT, PRIMARY KEY(`username`) )")
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
        return "", "", "", ""
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("PrintDefaults(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("PrintDefaults(4) {0}".format(e))
        return "", "", "", ""
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
            if (keys[i] == "tradier key"):
                if row[i] == "demo" or row[i] == "" or row[i] == "TEST":
                    col_list.append(row[i])
                else:
                    col_list.append("[key]")
            elif (keys[i] == "IEX key"):
                if row[i] == "demo" or row[i] == "" or row[i] == "TEST":
                    col_list.append(row[i])
                else:
                    col_list.append("[key]")
            elif (keys[i] == "coin key"):
                if row[i] == "demo" or row[i] == "" or row[i] == "TEST":
                    col_list.append(row[i])
                else:
                    col_list.append("[key]")
            elif (keys[i] == "export dir"):
                if row[i] == "/home/jsmith/Desktop":
                    col_list.append("[desktop]")
            elif (keys[i] == "market status"):
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
#endregion defaults
#region folder
def Add(symbol, exchange, verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
        print ("Add(1) symbol: {0}".format(symbol))
        print ("Add(2) exchange: {0}".format(exchange))
        print ("Add(3) dbase: {0}".format(db_file))

    crypto = 0
    if (exchange =="coinbase"):
        crypto = 1
        
    result = CreateFolder(symbol, crypto, verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("Add(4) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("Add(5) {0}".format(e))
            return False
        crypto = 0
        if (exchange =="coinbase"):
            json_data = CryptoCompany(symbol, verbose)
            crypto = 1
        else:
            json_data = Company(symbol, verbose)
        json_string = json.dumps(json_data)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO folder (symbol, crypto) VALUES ((?),?)", (symbol, crypto,))
        c.execute("UPDATE folder SET json_string = (?) WHERE symbol = (?) and crypto = ?", (json_string, symbol, crypto,))
        dt = datetime.datetime.now()
        c.execute("UPDATE folder SET update_time = (?) WHERE symbol = (?) and crypto = ?", (dt.strftime("%m/%d/%y %H:%M"), symbol, crypto,))
        conn.commit()
        conn.close()
        if (exchange =="coinbase"):
            quote = QuoteCrypto(symbol, verbose)
        else:
            quote = QuoteTradier(symbol, verbose)
        errors = []
        errors.append(symbol)
        errors.append(exchange)
        if ("Error Message" in quote):
            errors.append(quote["url"])
            errors.append(quote["Error Message"])
        else:
            quote = quote[0]
            errors.append(quote["url"])
            errors.append(quote['description'])
            errors.append("Success")
            if (exchange =="coinbase"):
                Quote(symbol, 1, None, verbose)
                Price(symbol, 1, quote["price"], verbose)
                Shares(symbol, 1, None, verbose)
            else:
                Quote(symbol, 0, None, verbose)
                Price(symbol, 0, quote["price"], verbose)
                Shares(symbol, 0, None, verbose)
    if (verbose):
        print (errors)
        print ("***\n")
    return errors

def Remove(symbol, exchange, verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
        print ("Remove(1) symbol: {0}".format(symbol))
        print ("Remove(2) exchange: {0}".format(exchange))
        print ("Remove(3) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("Remove(4) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("Remove(5) {0}".format(e))
        return False
    c = conn.cursor()
    if (exchange == "coinbase"):
        c.execute("DELETE FROM folder WHERE symbol=(?) and crypto = 1", (symbol,))
    else:
        c.execute("DELETE FROM folder WHERE symbol=(?) and crypto = 0", (symbol,))
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    return True

def Quote(symbol, crypto, quote, verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
        print ("Quote(1) symbol: {0}".format(symbol))
        print ("Quote(2) crypto: {0}".format(crypto))
        print ("Quote(3) quote: {0}".format(quote))
        print ("Quote(4) dbase: {0}".format(db_file))
    result = CreateFolder(symbol, crypto, verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("Quote(5) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("Quote(6) {0}".format(e))
            return False
        c = conn.cursor()
        c.execute("UPDATE folder SET quote = (?) WHERE symbol = (?) and crypto = ?", (quote, symbol, crypto, ))
        conn.commit()
        conn.close()
    if (verbose):
        print ("***\n")
    return True

def Price(symbol, crypto, price, verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
        print ("Price(1) symbol: {0}".format(symbol))
        print ("Price(2) crypto: {0}".format(crypto))
        print ("Price(3) price: {0}".format(price))
        print ("Price(4) dbase: {0}".format(db_file))
    result = CreateFolder(symbol, crypto, verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("Price(5) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("Price(6) {0}".format(e))
            return False
        c = conn.cursor()
        c.execute("UPDATE folder SET price = ? WHERE symbol = (?) and crypto = ?", (price, symbol, crypto, ))
        dt = datetime.datetime.now()
        c.execute("UPDATE folder SET update_time = (?) WHERE symbol = (?) and crypto = ?", (dt.strftime("%m/%d/%y %H:%M"), symbol ,crypto, ))
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
    result = CreateFolder("$", 0, verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("Cash(3) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("Cash(4) {0}".format(e))
            return False
        c = conn.cursor()
        c.execute("UPDATE folder SET balance = ? WHERE symbol = '$' and crypto = 0", (round(float(balance), 2),))
        dict_string = {'companyName': 'CASH', 'description': 'Cash Account', 'symbol': '$'}
        json_string = json.dumps(dict_string)
        c.execute("UPDATE folder SET json_string = (?) WHERE symbol = '$' and crypto = 0", (json_string,))
        c.execute("UPDATE folder SET shares = ? WHERE symbol = '$' and crypto = 0", (round(float(balance), 2),))
        dt = datetime.datetime.now()
        c.execute("UPDATE folder SET update_time = (?) WHERE symbol = '$' and crypto = 0", (dt.strftime("%m/%d/%y %H:%M"),))
        c.execute("UPDATE folder SET price = 1.00 WHERE symbol = '$' and crypto = 0")
        c.execute("UPDATE folder SET crypto = 0 WHERE symbol = '$' and crypto = 0")
        conn.commit()
        conn.close()
    if (verbose):
        print ("***\n")
    return True

def GetFolderCount(verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
    if db_file == "":
        if (verbose):
            print ("GetFolderCount(1) could not get dbase name, make sure that the defaults dbase is set up")
        return 0
    if (verbose):
        print ("GetFolderCount(2) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("GetFolderCount(3) {0} file is missing, cannot return the row count".format(db_file))
            print ("***\n")
        return 0
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("GetFolderCount(4) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("GetFolderCount(5) {0}".format(e))
        return 0
    if (checkTableExists(conn, "folder")):
        c = conn.cursor()
        c.execute("select * from folder")
        results = c.fetchall()
    else:
        results = ""
    conn.close()
    if (verbose):
        print ("***\n")
    return len(results)

def CreateFolder(symbol, crypto, verbose):
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
    c.execute("CREATE TABLE if not exists 'folder' ( `symbol` TEXT NOT NULL, `balance` REAL, `shares` REAL, `price` NUMERIC, `crypto` INTEGER, `quote` TEXT, `update_time` TEXT, `json_string` TEXT, PRIMARY KEY(`crypto`,`symbol`) )")
    c.execute( "INSERT OR IGNORE INTO folder(symbol, crypto) VALUES((?),?)", (symbol,crypto,))
    conn.commit()
    conn.close()
    count = GetFolderCount(verbose)
    if (count == 1 and symbol != "$"):
        Cash("0", verbose)
    if (verbose):
        print ("***\n")
    return True

def Shares(symbol, crypto, shares, verbose):
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
        print ("Shares(2) crypto: {0}".format(crypto))
        print ("Shares(3) shares: {0}".format(shares))
        print ("Shares(4) dbase: {0}".format(db_file))
    if (symbol == ""):
        e = "Error: symbol cannot be blank"
        print (e)
        result['status'] = False
        result['balance'] = 0
        result['exception'] = e
        return result
    folder = GetFolder(verbose)
    price = GetFolderValue(symbol, crypto, "price", folder)
    balance = 0
    if (price is None):
        price = 0
    if price > 0:
        balance = shares * price
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("Shares(5) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("Shares(6) {0}".format(e))
        result['status'] = False
        result['balance'] = 0
        result['exception'] = e
        return result
    c = conn.cursor()
    c.execute("UPDATE folder SET shares = ? WHERE symbol = (?) and crypto = ?", (shares, symbol, crypto,))
    balance = shares * price
    c.execute("UPDATE folder SET balance = ? WHERE symbol = (?) and crypto = ?", (balance, symbol, crypto,))
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    result['status'] = True
    result['balance'] = balance
    result['shares'] = shares
    result['price'] = price
    return result

def Balance(symbol, crypto, balance, verbose):
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
        print ("Balance(2) crypto: {0}".format(crypto))
        print ("Balance(3) balance: {0}".format(balance))
        print ("Balance(4) dbase: {0}".format(db_file))
    if (symbol == ""):
        e = "Error: symbol cannot be blank"
        print (e)
        result['status'] = False
        result['shares'] = 0
        result['exception'] = e
        return result
    folder = GetFolder(verbose)
    price = GetFolderValue(symbol, crypto, "price", folder)
    shares = 0
    if (price is None):
        price = 0
    if price > 0:
        shares = balance / price
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("Balance(5) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("Balance(6) {0}".format(e))
        result['status'] = False
        result['shares'] = 0
        result['exception'] = e
        return result
    c = conn.cursor()
    c.execute("UPDATE folder SET shares = ? WHERE symbol = (?) and crypto = ?", (shares, symbol,crypto,))
    c.execute("UPDATE folder SET balance = ? WHERE symbol = (?) and crypto = ?", (balance, symbol,crypto,))
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    result['status'] = True
    result['shares'] = shares
    result['balance'] = balance
    result['price'] = price
    return result

def Update(market_open, verbose):
    db_file = GetDB(verbose)
    username = getpass.getuser()
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (verbose):
        print ("***")
        print ("Update(1) Is the stock market open? : {0}".format(market_open))
        print ("Update(2) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("Update(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("Update(4) dbase: {0}, {1}".format(db_file, e))
        return False, e
    c = conn.cursor()
    try:
        c.execute("SELECT symbol, crypto, shares, balance FROM folder where symbol != '$' order by crypto,symbol")
    except Error as e:
        print("Update(5) dbase: {0}, {1}".format(db_file, e))
        return False, e
    rows = c.fetchall()
    conn.commit()
    conn.close()
    quote1_list = ""
    quote0_list = ""
    quote1 = []
    quote0 = []
    quotes0 = []
    quotes1 = []
    for row in rows:
        if (row[1] == 1):
            quote1_list += row[0] + ","
        if (row[1] == 0):
            quote0_list += row[0] + ","
    quote1_list = quote1_list[:-1]
    quote0_list = quote0_list[:-1]
    if (market_open == True) and (quote0_list != ""):
        quotes0 = QuoteTradier(quote0_list, verbose)
    if (quote1_list != ""):
        quotes1 = QuoteCrypto(quote1_list, verbose)
    errors = []
    if (quotes1 != []) and ("Error Message" in quotes1):
        errors.append(quotes1)
    if (quotes0 != []) and ("Error Message" in quotes0):
        errors.append(quotes0)
    if errors == []:
        for row in rows:
            for quote in quotes1:
                if (row[0] == quote["symbol"] and row[1] == 1):
                    result = Quote(row[0], row[1], quote["quote"], verbose)
                    result = Price(row[0], row[1], quote["price"], verbose)
                    result = Shares(row[0], row[1], str(row[2]), verbose)
                    if (result['status'] == True):
                        if (verbose):
                            print ("crypto symbol: {0}, current shares: {1}, previous balance: {2}, current balance: {3}".format(row[0], row[2], row[3], result['balance']))
            for quote in quotes0:
                if (row[0] == quote["symbol"] and row[1] == 0):
                    result = Quote(row[0], row[1], quote["quote"], verbose)
                    result = Price(row[0], row[1], quote["price"], verbose)
                    result = Shares(row[0], row[1], str(row[2]), verbose)
                    if (result['status'] == True):
                        if (verbose):
                            print ("stock symbol: {0}, current shares: {1}, previous balance: {2}, current balance: {3}".format(row[0], row[2], row[3], result['balance']))
    if (verbose):
        if (errors):
            pprint.pprint(errors)
        print ("***\n")
    return True, ""

def DayisOpen(verbose):
    answer = False
    d, t = GetDefaults(verbose)
    begin = d['open']
    weekno = datetime.datetime.today().weekday()
    ct = datetime.datetime.now().time()
    bt = ct
    if (begin is not None):
        if "AM" in begin or "PM" in begin:
            bt = datetime.datetime.strptime(begin, '%I:%M%p').time()
        else:
            bt = datetime.datetime.strptime(begin, '%H:%M').time()
    if weekno < 5 and ct > bt:
        answer = True
    return answer

def DayisClosed(verbose):
    answer = False
    d, t = GetDefaults(verbose)
    ct = datetime.datetime.now().time()
    if "close" in d:
        end = d['close']
    et = ct
    if (end is not None):
        if "AM" in end or "PM" in end:
            et = datetime.datetime.strptime(end, '%I:%M%p').time()
        else:
            et = datetime.datetime.strptime(end, '%H:%M').time()
    if ct > et:
        folder = GetFolder(verbose)
        if folder != []:
            answer = True
            for item in folder:
                if item['symbol'] != "$":
                    if (item['quote'] != "close"):
                        answer = False
                        break
    return answer

def GetFolderCash(verbose):
    folder = GetFolder(verbose)
    answer = 0
    for item in folder:
        if item['symbol'] == "$":
            answer = item['balance']
    return answer

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
    keys = {}
    values = []
    if (checkTableExists(conn, "folder")):
        c = conn.cursor()
        c.execute("SELECT * FROM folder order by balance DESC")
        keys = list(map(lambda x: x[0].replace("_"," "), c.description))
        values = c.fetchall()
    conn.close()
    if (verbose):
        print ("***\n")
    answer = []
    for row in values:
        answer.append(dict(zip(keys, row)))
    answers = []
    for js in answer:
        if 'json string' in js:
            if js['json string'] != None:
                js['json string'] = json.loads(js['json string'])
                answers.append(js)
    return answers

def GetFolderValue(symbol, crypto, key, folder_list):
    value = None
    if folder_list != []:
        for row in folder_list:
            if (row['symbol'] == symbol) and (row['crypto'] == int(crypto)):
                if row[key] == None:
                    return 0
                else:
                    return row[key]
    if value is None:
        value = 0
    return value

def GetFolderStockValue(verbose):
    folder = GetFolder(verbose)
    answer = 0
    for item in folder:
        if item['symbol'] != "$":
            if (item['balance'] != None):
                answer += item['balance']
    return answer

def PrintFolder(verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
        print ("PrintFolder(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("PrintFolder(2) {0} file is missing, cannot return the key".format(db_file))
            print ("***\n")
        return "", "", "", ""
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("PrintFolder(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("PrintFolder(4) {0}".format(e))
        return "", "", "", ""
    if (not checkTableExists(conn, "folder")):
        Cash("0", verbose)
    conn.close()
    folder = GetFolder(verbose)
    if (folder == []):
        return "", "", "", ""
    keys_dict = folder[0].keys()
    keys_raw = []
    for key in keys_dict:
        keys_raw.append(key)
    keys = keys_raw[:1] + ['company name'] + keys_raw[1:-1]
    TableCls = create_table('TableCls')
    for key in keys:
        TableCls.add_column(key, Col(key))
    market, worksheet = GetWorksheet("latest", verbose)
    post_worksheet = False
    if market != {}:
        dt = datetime.datetime.now()
        today = dt.strftime('%Y/%m/%d')
        if (market['post date'] == today):
            if (market['posted'] != "yes"):
                post_worksheet = True

    items = []
    answer = {}
    symbol_options = ""
    balance_options = ""
    if (post_worksheet):
        symbol_options += '<option value="worksheet">worksheet</option>'
        balance_options += '<option value="calculations">calculations</option>'

    balance_options += '<option value="balance">balance</option>'
    balance_options += '<option value="shares">shares</option>'
    balance_options += '<option value="amount">amount</option>'
    amount_options = []
    for f in folder:
        row = []
        for value in f.values():
            row.append(value)
        row = row[:1] + [''] + row[1:-1]
        symbol_options += '<option value="{0},{1}">{2}</option>'.format(row[keys.index("symbol")], row[keys.index("crypto")], row[keys.index("symbol")])
        json_string = f['json string']
        col_list = []
        for i in range(len(keys)):
            if (keys[i] == "company name"):
                col_list.append(json_string['companyName'])
            elif (keys[i] == "shares"):
                if (row[0] == "$"):
                    col_list.append("")
                else:
                    if row[i] is None:
                        col_list.append(as_shares(0))
                    else:
                        col_list.append(as_shares(row[i]))
            elif (keys[i] == "price"):
                if row[0] == "$":
                    col_list.append("$1.00")
                else:
                    col_list.append(as_big(row[i]))
            elif (keys[i] == "crypto"):
                if row[i] == 0:
                    col_list.append("no")
                else:
                    col_list.append("yes")
            else:
                if (keys[i] == "balance"):
                    col_list.append(as_currency(row[i]))
                    if (keys[i] == "balance"):
                        amount_option = []
                        amount_option.append(row[keys.index("symbol")])
                        amount_option.append(row[keys.index("crypto")])
                        amount_option.append(row[i])
                        amount_option.append(row[keys.index("shares")])
                        amount_options.append(amount_option)
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
        matches = re.finditer("<td>", table)
        matches_positions = [match.start() for match in matches]
        match_index = matches_positions.index(start + 4)
        symbol = table[start + 8 :table.find("</td>", start + 8)]
        crypto = table[matches_positions[match_index + 5] + 4 :table.find("</td>", matches_positions[match_index + 5] + 4)]
        if (symbol != "$"):
            exchange = ""
            if (crypto == "1"):
                    exchange = "coinbase"
            r_button = '<tr><td><form action="#" method="post"><input class="submit" type="submit" name="action" value="remove"/><input hidden type="text" name="remove_symbol" value="{0}"/><input hidden type="text" name="remove_type" value="{1}"/></form></td><td>'.format(symbol, exchange)
            table = table[0 : start] + table[start:].replace(pattern, r_button, 1)
        else:
            table = table[0 : start] + table[start:].replace(pattern, "<tr><td></td><td>", 1)
        index = start + 1
    return table

def AllocationTrends(verbose): 
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
            print ("AllocationTrends(2) could not get previous prices, make sure you have initialized AIM system")
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
            print ("AllocationTrends(3) could not get initial prices, make sure you have initialized AIM system")
        return "", "", ""
    js = json.loads(first['json string'])
    first_list = []
    for col in js:
        if ("symbol" in col):
            first_list.append(col)
    if (verbose):
        print ("AllocationTrends(4) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("AllocationTrends(5) {0} file is missing, cannot print".format(db_file))
            print ("***\n")
        return "", "", ""
    rows = GetFolder(verbose)
    total = 0
    for row in rows:
        if (row['symbol'] != "$"):
            if (row['balance'] is not None):
                total = total + row['balance']
    allocation = ""
    for row in rows:
        pst = 0
        if (row['symbol'] != "$"):
            if (row['balance'] is not None) and (total != 0):
                pst = row['balance'] / total * 100.
            allocation = allocation + "<li>{0} {1}</li>".format(row['symbol'], as_percent(pst))
    trends = []
    for row in rows:
        for col in last_list:
            if (row['symbol'] != "$"):
                if (row['symbol'] == col['symbol'] and row['crypto'] == col['crypto']):
                    pst = 0
                    test = 0
                    trend = {}
                    if (col['price'] is not None) and (col['price'] != 0):
                        pst = (row['price'] - col['price']) / col['price'] * 100.
                        if pst == 0:
                            trend['arrow'] = "flat"
                            trend['percent'] = "{0} {1}".format(row['symbol'], as_percent(pst))
                        elif pst > 0:
                            trend['arrow'] = "up"
                            trend['percent'] = "{0} {1}".format(row['symbol'], as_percent(pst))
                        else:
                            trend['arrow'] = "down"
                            trend['percent'] = "{0} {1}".format(row['symbol'], as_percent(pst))
                    trends.append(trend)
    life_trends = []
    for row in rows:
        for col in first_list:
            if (row['symbol'] == col['symbol'] and row['crypto'] == col['crypto']):
                pst = 0
                test = 0
                trend = {}
                if (col['balance'] is not None) and (col['balance'] != 0):
                    pst = (row['balance'] - col['balance']) / col['balance'] * 100.
                    if pst == 0:
                        trend['arrow'] = "flat"
                        trend['percent'] = "{0} {1}".format(row['symbol'], as_percent(pst))
                    elif pst > 0:
                        trend['arrow'] = "up"
                        trend['percent'] = "{0} {1}".format(row['symbol'], as_percent(pst))
                    else:
                        trend['arrow'] = "down"
                        trend['percent'] = "{0} {1}".format(row['symbol'], as_percent(pst))
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
    keys = {}
    values = []
    if (checkTableExists(conn, "aim")):
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
    answers = []
    for js in answer:
        js['json string'] = json.loads(js['json string'])
        answers.append(js)
    return answers

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
    dl = GetCurrentStockList(amount_options, verbose)
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
    dt = datetime.datetime.now()
    today = dt.strftime('%Y/%m/%d')
    answer = {}
    if (checkTableExists(conn, "aim")):
        c = conn.cursor()
        c.execute("SELECT * FROM aim WHERE post_date != (?) ORDER BY post_date DESC LIMIT 1", (today,))
        keys = list(map(lambda x: x[0].replace("_"," "), c.description))
        values = c.fetchone()
        if values is not None:
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
    if (count > 5):
        count = 5   # show just the last 5 transactions
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
        js = json.loads(answer['json string'])
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
        if (values is not None):
            answer = dict(zip(keys, values))
        conn.close()
    if (verbose):
        print ("***\n")
    return answer

def Look(verbose):
    first = GetFirstAIM(verbose)
    if not first:
        if (verbose):
            print ("Look(1) could not get defaults, make sure that the defaults dbase is set up")
        return {}, "", {}
    prev = GetLastAIM(verbose)
    cd = datetime.datetime.now()
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
    return pretty, table.__html__(), answer_db

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
    look, table, db_values = Look(verbose)
    if (verbose):
        print("Post(5) {0}".format(look))
    table, symbol_options, balance_options, amount_options = PrintFolder(False)
    dl = GetCurrentStockList(amount_options, verbose)
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
        BeginWorksheet(db_values['market order'], verbose)
    if (verbose):
        print ("***\n")
    return True

def GetCurrentStockList(stock_list, verbose):
    folder = GetFolder(verbose)
    dl = []
    for item in stock_list:
        ds = {}
        ds['symbol'] = item[0]
        ds['crypto'] = item[1]
        ds['balance'] = round(item[2], 2)
        ds['shares'] = round(item[3], 8)
        if folder != []:
            for f in folder:
                if (item[0] == f['symbol']) and (f['crypto'] == int(item[1])):
                    ds['price'] = f['price']
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
        return "", ""
    if (verbose):
        print ("PrintAIM(2) dbase: {0}".format(db_file))
        print ("PrintAIM(3) year: {0}".format(printyear))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("PrintAIM(4) {0} file is missing, cannot print".format(db_file))
            print ("***\n")
        return "", ""
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("PrintAIM(5) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("PrintAIM(6) {0}".format(e))
        return "", ""
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
        js = json.loads(row[keys_db.index("json string")])
        dt = datetime.datetime.strptime(row[keys_db.index("post date")], '%Y/%m/%d')
        if (intyear == 1970 or dt.year == intyear):
            if (js is not {}):
                if ("start date" in js[0]):
                    dt = datetime.datetime.strptime(js[0]['start date'], '%Y/%m/%d')
            col_list = []
            for i in range(len(keys)):
                if (keys[i] == "post date"):
                    col_list.append(dt.strftime("%b, %d"))
                elif (keys[i] == "stock value"):
                    col_list.append(as_currency(row[i]))
                    stock = math.ceil(row[keys.index("stock value")] -.4)
                    safe = Safe(stock, verbose)
                    col_list.append(safe)
                else:
                    if (keys_db.index("json string") != i):
                        col_list.append(as_currency(row[i]))
            answer = dict(zip(keys, col_list))
            items.append(answer)
    table = TableCls(items, html_attrs = {'width':'100%','border-spacing':0})
    if (verbose):
        print ("***\n")
    defaults, types =  GetDefaults(False)
    export_options = ""
    if "snap shot" in defaults:
        export_options += '<option value="AIM activity">AIM activity</option>'
        export_options += '<option value="Archive snapshot {0}">Archive snapshot {0}</option>'.format(defaults['snap shot'], defaults['snap shot'])
        export_options += '<option value="Current portfolio">Current portfolio</option>'
        export_options += '<option value="Latest worksheet">Latest worksheet</option>'
    return table.__html__(), export_options
#endregion aim
#region tests
def TestDefaults(saved, verbose):
    if (saved):
        old_stdout = sys.stdout
        print_out = StringIO()
        sys.stdout = print_out
    count = 0
    fails = 0
    total_tests = 26
    defaults, types =  GetDefaults(False)
    if defaults == {}:
        result = ResetDefaults(verbose)
        if (result):
            defaults, types =  GetDefaults(False)
    if (verbose):
        print ("***")
        print ("\tRunning tests will preserve your original defaults (if they exist)")
        print ("***\n")
    if (verbose):
        print ("Test #{0} - UpdateDefaultItem('folder name', 'Test Folder', False)".format(count + 1))
    result = UpdateDefaultItem("folder name", "Test Folder", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Company('AAPL', verbose)".format(count + 1))
    result = Company("AAPL", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - MarketToTime('06:15', verbose)".format(count + 1))
    result = MarketToTime("06:15", "US/Eastern", verbose)
    if (result == "05:15AM"):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
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
        fails += 1
    if (verbose):
        print ("Test #{0} - UpdateDefaultItem('IEX key', 'TEST', verbose)".format(count + 1))
    result = UpdateDefaultItem("IEX key", "TEST", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - UpdateDefaultItem('coin key', 'TEST', verbose)".format(count + 1))
    result = UpdateDefaultItem("coin key", "TEST", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - UpdateDefaultItem('poll minutes', 10, False)".format(count + 1))
    result = UpdateDefaultItem('poll minutes', 10, verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
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
        fails += 1
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
        fails += 1
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
        fails += 1
    if (verbose):
        print ("Test #{0} - Add('AAPL', 'NASDAQ', verbose)".format(count + 1))
    result = Add( "AAPL", "NASDAQ", verbose)
    if ("Invalid Access Token" in result):
        if (verbose):
            print ("\tpass.")
        count += 1
    elif ("Success" in result) and (result[3] == "Apple Inc"):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - QuoteTradier('AAPL', verbose)".format(count + 1))
    result = QuoteTradier("AAPL", verbose)
    if (result['Error Message'] == "Invalid Access Token"):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Price('AAPL', 0, 50.55, verbose)".format(count + 1))
    result = Price("AAPL", 0, 50.55, verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - GetFolder(verbose)".format(count + 1))
    result = GetFolder(verbose)
    if result != []:
        for item in result:
            if item['symbol'] == "AAPL" and item['crypto'] == 0:
                if item['price'] == 50.55 and item['quote'] == None:
                    if (verbose):
                        print ("\tpass.")
                    count += 1
                    break
                else:
                    if (verbose):
                        print ("\tfail.")
                    fails += 1
                    break
    else:
        if (verbose):
            print ("\tpass.")
        count += 1
    if (verbose):
        print ("Test #{0} - Holiday(verbose)".format(count + 1))
    result = Holiday(verbose)
    if ("Error Message" in result or 'status' in result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
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
                fails += 1
    testResults = False
    if (fails == 0 and count == total_tests):
        print ("ran {0} tests, all pass".format(total_tests))
        testResults = True
    else:
        print ("test count expected {0} passes, received {1}, failures {2}".format(total_tests, count, fails))
        testResults =  False
    result_string = ""
    if (saved):
        sys.stdout = old_stdout
        result_string = print_out.getvalue()
    results = {}
    results['status'] = testResults
    results['total'] = total_tests
    results['pass'] = count
    results['fails'] = fails
    results['output'] = result_string
    return results

def TestCrypto(saved, verbose):
    if (saved):
        old_stdout = sys.stdout
        print_out = StringIO()
        sys.stdout = print_out
    count = 0
    fails = 0
    total_tests = 16
    defaults, types = GetDefaults(verbose)
    if (verbose):
        print ("Test #{0} - UpdateDefaultItem('folder name', 'Test Crypto', verbose)".format(count + 1))
    result = UpdateDefaultItem("folder name", "Test Crypto", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Balance('$', 0, '5000', verbose)".format(count + 1))
    result = Balance( "$", 0, "5000", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Add('MMM', 'NASDAQ', verbose)".format(count + 1))
    result = Add( "MMM", "NASDAQ", verbose)
    if ("Invalid Access Token" in result):
        if (verbose):
            print ("\tpass.")
        count += 1
    elif ("Success" in result) and (result[3] == "3M Co"):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Balance('MMM', 0, '2500', verbose)".format(count + 1))
    result = Balance( "MMM", 0, "2500", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Add('MMM', 'coinbase', verbose)".format(count + 1))
    result = Add( "MMM", "coinbase", verbose)
    if ("This API Key is invalid." in result):
        if (verbose):
            print ("\tpass.")
        count += 1
    elif ("Success" in result) and (result[3] == "MultiMillion"):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Balance('MMM', 1, '2500', verbose)".format(count + 1))
    result = Balance( "MMM", 1, "2500", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - GetFolderCount(verbose)".format(count + 1))
    result = GetFolderCount(verbose)
    if (result == 3):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Shares('MMM', 0, '50', verbose)".format(count + 1))
    result = Shares("MMM", 0, "50", verbose)
    if (result['status']):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Shares('MMM', 1, '50', verbose)".format(count + 1))
    result = Shares("MMM", 1, "50", verbose)
    if (result['status']):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Update(True, verbose)".format(count + 1))
    result = Update(True, verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    folder = GetFolder(verbose)
    if (verbose):
        print ("Test #{0} - GetFolderValue('MMM', 0, 'price', folder)".format(count + 1))
    result0 = GetFolderValue("MMM", 0, "price", folder)
    if (result0 >= 0):
        if (verbose):
            print ("*** Price is: {0} ***".format(result0))
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - GetFolderValue('MMM', 1, 'price', folder)".format(count + 1))
    result1 = GetFolderValue("MMM", 1, "price", folder)
    if (result1 >= 0):
        if (verbose):
            print ("*** Price is: {0} ***".format(result1))
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Remove('MMM', 'NASDAQ', verbose)".format(count + 1))
    result = Remove("MMM", "NASDAQ", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Remove('MMM', 'coinbase', verbose)".format(count + 1))
    result = Remove("MMM", "coinbase", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - GetFolderCount(verbose)".format(count + 1))
    result = GetFolderCount(verbose)
    if (result == 1):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - DeleteName('Test Crypto', verbose)".format(count + 1))
    result = DeleteName("Test Crypto", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    testResults = False
    if (fails == 0 and count == total_tests):
        print ("ran {0} tests, all pass".format(total_tests))
        testResults = True
    else:
        print ("test count expected {0} passes, received {1}, failures {2}".format(total_tests, count, fails))
        testResults =  False
    result_string = ""
    if (saved):
        sys.stdout = old_stdout
        result_string = print_out.getvalue()
    results = {}
    results['status'] = testResults
    results['total'] = total_tests
    results['pass'] = count
    results['fails'] = fails
    results['output'] = result_string
    return results

def TestFolder(saved, verbose):
    if (saved):
        old_stdout = sys.stdout
        print_out = StringIO()
        sys.stdout = print_out
    count = 0
    fails = 0
    total_tests = 13
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
        fails += 1
    if (verbose):
        print ("Test #{0} - Add('AAPL', 'NASDAQ', verbose)".format(count + 1))
    result = Add( "AAPL", "NASDAQ", verbose)
    if ("Invalid Access Token" in result):
        if (verbose):
            print ("\tpass.")
        count += 1
    elif ("Success" in result) and (result[3] == "Apple Inc"):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Balance('$', 0, '5000', verbose)".format(count + 1))
    result = Balance( "$", 0, "5000", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - GetFolderCount(verbose)".format(count + 1))
    result = GetFolderCount(verbose)
    if (result > 0):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - GetFolderCash(verbose)".format(count + 1))
    result = GetFolderCash(verbose)
    if (result == 5000):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Balance('AAPL', 0, '5000', verbose)".format(count + 1))
    result = Balance("AAPL", 0, "5000", verbose)
    if (result['status']):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Shares('AAPL', 0, '50', verbose)".format(count + 1))
    result = Shares("AAPL", 0, "50", verbose)
    if (result['status']):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    folder = GetFolder(verbose)
    if (verbose):
        print ("Test #{0} - GetFolderValue('AAPL', 0, 'price', folder)".format(count + 1))
    result = GetFolderValue("AAPL", 0, "price", folder)
    if (result >= 0):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - GetFolderStockValue(verbose)".format(count + 1))
    result = GetFolderStockValue(verbose)
    if (result >= 0):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Update(True, verbose)".format(count + 1))
    result = Update(True, verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Remove('AAPL', 'NASDAQ', verbose)".format(count + 1))
    result = Remove("AAPL", "NASDAQ", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
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
        fails += 1
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
        fails += 1
    testResults = False
    if (fails == 0 and count == total_tests):
        print ("ran {0} tests, all pass".format(total_tests))
        testResults = True
    else:
        print ("test count expected {0} passes, received {1}, failures {2}".format(total_tests, count, fails))
        testResults =  False
    result_string = ""
    if (saved):
        sys.stdout = old_stdout
        result_string = print_out.getvalue()
    results = {}
    results['status'] = testResults
    results['total'] = total_tests
    results['pass'] = count
    results['fails'] = fails
    results['output'] = result_string
    return results

def TestAIM(location, saved, verbose):
    if (saved):
        old_stdout = sys.stdout
        print_out = StringIO()
        sys.stdout = print_out
    count = 0
    fails = 0
    total_tests = 455
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
            fails += 1
        if (verbose):
            print ("Test #{0} - Balance('$', 0, '5000', verbose)".format(count + 1))
        result = Balance( "$", 0, "5000", verbose)
        if (result):
            if (verbose):
                print ("\tpass.")
            count += 1
        else:
            if (verbose):
                print ("\tfail.")
            fails += 1
        if (verbose):
            print ("Test #{0} - PrintDefaults(verbose)".format(count + 1))
        r1, r2, r3, r4 = PrintDefaults(verbose)
        if (r1 > "" and r2 > "" and r3 > "" and r4 > ""):
            if (verbose):
                print ("\tpass.")
            count += 1
        else:
            if (verbose):
                print ("\tfail.")
            fails += 1
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
                fails += 1
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
                fails += 1
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
                fails += 1
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
                fails += 1
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
                fails += 1
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
            fails += 1
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
            fails += 1
    testResults = False
    if (fails == 0 and count == total_tests):
        print ("ran {0} tests, all pass".format(total_tests))
        testResults = True
    else:
        print ("test count expected {0} passes, received {1}, failures {2}".format(total_tests, count, fails))
        testResults =  False
    result_string = ""
    if (saved):
        sys.stdout = old_stdout
        result_string = print_out.getvalue()
    results = {}
    results['status'] = testResults
    results['total'] = total_tests
    results['pass'] = count
    results['fails'] = fails
    results['output'] = result_string
    return results

def TestHistory(saved, verbose):
    results = {}
    db_file = GetDB(verbose)
    username = getpass.getuser()
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (saved):
        old_stdout = sys.stdout
        print_out = StringIO()
        sys.stdout = print_out
    count = 0
    fails = 0
    total_tests = 31
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("TestHistory(1) sqlite3: {0}".format(sqlite3.version))
            print("TestHistory(2) db_file: {0}".format(db_file))
    except Error as e:
        print("TestHistory(3) {0}".format(e))
        sys.stdout = old_stdout
        result_string = print_out.getvalue()
        results['output'] = result_string
        return results
    defaults, types = GetDefaults(verbose)
    if (verbose):
        print ("Test #{0} - GetDB(verbose)".format(count + 1))
    result = GetDB(verbose)
    if (result > ""):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - UpdateDefaultItem('folder name', 'Test History', verbose)".format(count + 1))
    result = UpdateDefaultItem("folder name", "Test History", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Balance('$', 0, '5000', verbose)".format(count + 1))
    result = Balance( "$", 0, "5000", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Add('AAPL', 'NASDAQ', verbose)".format(count + 1))
    result = Add( "AAPL", "NASDAQ", verbose)
    if ("Invalid Access Token" in result):
        if (verbose):
            print ("\tpass.")
        count += 1
    elif ("Success" in result) and (result[3] == "Apple Inc"):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Balance('AAPL', 0, '5000', verbose)".format(count + 1))
    result = Balance("AAPL", 0, "5000", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - CreateAIM(verbose)".format(count + 1))
    result, text = CreateAIM(verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    elif (text == "You must go to the History Tab and archive your AIM data first"):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - GetAIM(verbose)".format(count + 1))
    result = GetAIM(verbose)
    if (result != []):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - GetAIMCount(verbose)".format(count + 1))
    result = GetAIMCount(verbose)
    if (result > 0):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - GetLastAIM(verbose)".format(count + 1))
    result = GetLastAIM(verbose)
    if (result != {}):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - GetFirstAIM(verbose)".format(count + 1))
    result = GetFirstAIM(verbose)
    if (result != {}):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Look(verbose)".format(count + 1))
    r1, r2, r3 = Look(verbose)
    if (r1 != {} and r2 > "" and r3 != {}):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - Post(verbose)".format(count + 1))
    result = Post(verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    table, symbol_options, balance_options, amount_options = PrintFolder(verbose)
    if (verbose):
        print ("Test #{0} - GetCurrentStockList(<amount options>, verbose)".format(count + 1))
    dl = GetCurrentStockList(amount_options, verbose)
    if (dl != []):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - BeginWorksheet(-500, verbose)".format(count + 1))
    filename = "{0}worksheet_test.csv".format(defaults['test root'])
    result = BeginWorksheet(-500, verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - Archive(verbose)".format(count + 1))
    result = Archive(verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - GetNextSnap(verbose)".format(count + 1))
    snap = GetNextSnap(verbose)
    if (snap > 0):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - GetDetail(snap, verbose)".format(count + 1))
    ac, sc, wc = GetDetail((snap - 1), verbose)
    if (ac != []):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - GetSummary(verbose)".format(count + 1))
    result = GetSummary(verbose)
    if (ac != []):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - PrintSummary(verbose)".format(count + 1))
    result = PrintSummary(verbose)
    if (result > ""):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - GetNames(verbose)".format(count + 1))
    result = GetNames(verbose)
    if (result != []):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - PrintAIM('all', verbose)".format(count + 1))
    result, export_options = PrintAIM("all", verbose)
    if (result > ""):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - ActivitySheet('test/activity_test.csv', verbose)".format(count + 1))
    filename = "{0}activity_test.csv".format(defaults['test root'])
    result = ActivitySheet(filename, verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - FolderSheet('test/folder_test.csv', verbose)".format(count + 1))
    filename = "{0}folder_test.csv".format(defaults['test root'])
    result = FolderSheet(filename, verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - BeginWorksheet(0, verbose)".format(count + 1))
    filename = "{0}worksheet_test.csv".format(defaults['test root'])
    result = BeginWorksheet(0, verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - WorkSheet('test/worksheet_test.csv', verbose)".format(count + 1))
    filename = "{0}worksheet_test.csv".format(defaults['test root'])
    result = WorkSheet(filename, verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - ArchiveSheet('test/activity_test.csv', verbose)".format(count + 1))
    filename = "{0}archive_test.csv".format(defaults['test root'])
    result = ArchiveSheet(filename, verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - Remove('AAPL', 'NASDAQ', verbose)".format(count + 1))
    result = Remove("AAPL", "NASDAQ", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
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
        fails += 1
    if (verbose):
        print ("Test #{0} - UpdateDefaultItem('snap shot', '<reset back to what it was>', verbose)".format(count + 1))
    result = UpdateDefaultItem("snap shot", defaults['snap shot'], verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - DeleteSnapshot(last snapshot, verbose)".format(count + 1))
    result = DeleteSnapshot((snap - 1), verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    if (verbose):
        print ("Test #{0} - DeleteName('Test History', verbose)".format(count + 1))
    result = DeleteName("Test History", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
        fails += 1
    testResults = False
    if (fails == 0 and count == total_tests):
        print ("ran {0} tests, all pass".format(total_tests))
        testResults = True
    else:
        print ("test count expected {0} passes, received {1}, failures {2}".format(total_tests, count, fails))
        testResults =  False
    result_string = ""
    if (saved):
        sys.stdout = old_stdout
        result_string = print_out.getvalue()
    results['status'] = testResults
    results['total'] = total_tests
    results['pass'] = count
    results['fails'] = fails
    results['output'] = result_string
    return results

def TestLow(saved, verbose):
    results = {}
    if (saved):
        old_stdout = sys.stdout
        print_out = StringIO()
        sys.stdout = print_out
    count = 0
    fails = 0
    total_tests = 10
    if (verbose):
        print ("Test #{0} - noteDate('2017/09/29')".format(count + 1))
    result  = noteDate('2017/09/29')
    if (result == "September 29th, 2017"):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - to_number('(24.45%)', verbose)".format(count + 1))
    result  = to_number('(24.45%)', verbose)
    if (result == -.2445):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - as_big(-80000.5)".format(count + 1))
    result  = as_big(-80000.5)
    if (result == "($80,000.50000000)"):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - as_currency(-80000.5)".format(count + 1))
    result  = as_currency(-80000.5)
    if (result == "($80,000.50)"):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - as_shares(23.4)".format(count + 1))
    result  = as_shares(23.4)
    if (result == "\r23.40000000"):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - as_percent(-23.4)".format(count + 1))
    result  = as_percent(-23.4)
    if (result == "(23.40%)"):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - CheckPretty('fred%&*')".format(count + 1))
    result  = CheckPretty("fred%&*")
    if (not result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - myFloat('fred%&*')".format(count + 1))
    result  = myFloat("fred%&*")
    if (result == 0):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - LogDaemon('test', verbose)".format(count + 1))
    log = {}
    log['status'] = "test"
    log['pid'] = None
    result  = LogDaemon(log, verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    if (verbose):
        print ("Test #{0} - PrintDaemon('test', verbose)".format(count + 1))
    result, status  = PrintDaemon("test", verbose)
    if (result > ""):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
            fails += 1
    testResults = False
    if (fails == 0 and count == total_tests):
        print ("ran {0} tests, all pass".format(total_tests))
        testResults = True
    else:
        print ("test count expected {0} passes, received {1}, failures {2}".format(total_tests, count, fails))
        testResults =  False
    result_string = ""
    if (saved):
        sys.stdout = old_stdout
        result_string = print_out.getvalue()
    results['status'] = testResults
    results['total'] = total_tests
    results['pass'] = count
    results['fails'] = fails
    results['output'] = result_string
    return results

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
    index = 0
    loop = -1
    for key in keys:
        loop += 1
        if (key != "json string"):
            TableCls.add_column(key, Col(key))
        else:
            TableCls.add_column('pid', Col('pid'))
            index = loop
    keys[index] = 'pid'
    items = []
    answer = {}
    status = ""
    for row in rows:
        if row[0] != "sleep" and status == "":
            status = row[0]
        col_list = []
        for i in range(len(keys)):
            if (keys[i] == "timestamp"):
                dt = datetime.datetime.strptime(row[i], '%Y/%m/%d %H:%M:%S.%f')
                col_list.append(dt.strftime("%b %d %I:%M %p"))
            elif (keys[i] == "pid"):
                js = json.loads(row[i])
                col_list.append(js['pid'])
            else:
                col_list.append(row[i])
        answer = dict(zip(keys, col_list))
        items.append(answer)
    table = TableCls(items, html_attrs = {'width':'100%','border-spacing':0})
    if (verbose):
        print ("***\n")
    return table.__html__(), status
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
        row['stock value'] = as_currency(row['stock value'])
        row['cash'] = as_currency(row['cash'])
        row['portfolio control'] = as_currency(row['portfolio control'])
        row['buy sell advice'] = as_currency(row['buy sell advice'])
        row['market order'] = as_currency(row['market order'])
        row['portfolio value'] = as_currency(row['portfolio value'])
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
        row['balance'] = as_currency(row['balance'])
        row['shares'] = as_shares(row['shares'])
        row['price'] = as_big(row['price'])
        values = row.values()
        csvwriter.writerow(values)
    sheet.close()  
    return True

def WorkSheet(filename, verbose):
    market, worksheet = GetWorksheet("latest", verbose)
    if (market == {} or worksheet == []):
        return False
    header = True
    sheet = open(filename, 'w', newline='')
    csvwriter = csv.writer(sheet)
    for row in worksheet:
        if (header):
            keys = row.keys()
            header = False
            csvwriter.writerow(keys)
        row['adjust amount'] = as_big(row['adjust amount'])
        if (row['symbol'] == "$"):
            row['shares'] = ""
        else:
            row['shares'] = as_shares(row['shares'])
        values = row.values()
        csvwriter.writerow(values)
    sheet.close()  
    return True

def ArchiveSheet(filename, verbose):
    d, t = GetDefaults(verbose)
    if (verbose):
        print ("***")
        print ("ArchiveSheet(2) filename: {0}".format(filename))
    snap = 0
    if ("snap shot" in d):
        snap = d['snap shot']
    if (snap is None) or (snap < 1):
        if (verbose):
            print ("ArchiveSheet(2) no snapshots to export")
        return False
    summary = GetSummary(verbose)
    aim, shares, worksheet = GetDetail(snap, verbose)
    sheet = open(filename, 'w', newline='')
    csvwriter = csv.writer(sheet)
    if summary != []:
        header = True
        for row in summary:
            if row['snapshot'] == snap:
                if (header):
                    keys = row.keys()
                    header = False
                    csvwriter.writerow(keys)
                row['initial'] = as_big(row['initial'])
                row['profit percent'] = as_percent(row['profit percent'])
                values = row.values()
                csvwriter.writerow(values)
    csvwriter.writerow(" ")
    if aim != []:
        header = True
        for row in aim:
            if (header):
                keys = row.keys()
                header = False
                csvwriter.writerow(keys)
            row['stock value'] = as_currency(row['stock value'])
            row['cash'] = as_currency(row['cash'])
            row['portfolio control'] = as_currency(row['portfolio control'])
            row['buy sell advice'] = as_currency(row['buy sell advice'])
            row['market order'] = as_currency(row['market order'])
            row['portfolio value'] = as_currency(row['portfolio value'])
            values = row.values()
            csvwriter.writerow(values)
    csvwriter.writerow(" ")
    if shares != []:
        header = True
        for row in shares:
            if (header):
                keys = row.keys()
                header = False
                csvwriter.writerow(keys)
            row['balance'] = as_currency(row['balance'])
            row['shares'] = as_shares(row['shares'])
            values = row.values()
            csvwriter.writerow(values)
    csvwriter.writerow(" ")
    if worksheet != []:
        header = True
        for row in worksheet:
            if (header):
                keys = row.keys()
                header = False
                csvwriter.writerow(keys)
            row['adjust amount'] = as_big(row['adjust amount'])
            if row['symbol'] == "$":
                row['shares'] = ""
            else:
                row['shares'] = as_shares(row['shares'])
            values = row.values()
            csvwriter.writerow(values)
    sheet.close()  
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
        etype = etype.lower()
        log = "Now saving under {0}".format(filename)
        if (etype == "activity" or etype == "aim activity"):
            result = ActivitySheet(filename, verbose)
        elif (etype == "portfolio" or etype == "current portfolio"):
            result = FolderSheet(filename, verbose)
        elif (etype == "worksheet" or etype == "latest worksheet"):
            result = WorkSheet(filename, verbose)
        else:
            result = ArchiveSheet(filename, verbose)
        if (result):
            log = "file saved."
        else:
            if ("archive" in etype):
                log = "file not saved, please set snap shot in defaults correctly and try again."
            else:
                log = "file not saved, do you have your {0} set up?".format(etype)
    else:
        log = "save was cancelled."
    return log

def Archive(verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
    if db_file == "":
        if (verbose):
            print ("Archive(1) could not get dbase name, make sure that the defaults folder name is set up")
        return False
    snap = 0
    result = CreateArchive(verbose)
    if result:
        snap = GetNextSnap(verbose)
        resultTables = SnapTables(verbose)
        if (resultTables):
            resultSummary = SnapSummary(verbose)
            if (resultSummary):
                BumpSnap(verbose)
    test = GetNextSnap(verbose)
    if (verbose):
        print ("***\n")
    if snap > 0 and test == (snap + 1):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("Archive(2) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("Archive(3) {0}".format(e))
            return False
        c = conn.cursor()
        worksheet_count = 0
        if (checkTableExists(conn, "worksheet")):
            c.execute("select * from worksheet where snapshot = ?", (snap,))
            worksheet_count = c.fetchall()
        if (worksheet_count > 0):
            c.execute("DELETE FROM worksheet")
        c.execute("DELETE FROM aim where post_date != '1970/01/01'")
        conn.commit()
        conn.close()
        UpdateDefaultItem("snap shot", snap, verbose)
        return True
    return False

def GetNextSnap(verbose):
    username = getpass.getuser()
    db_file = username + "/archive.db"
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (verbose):
        print ("***")
        print ("GetNextSnap(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("GetNextSnap(2) {0} file is missing, cannot return the next snapshot".format(db_file))
            print ("***\n")
        return 0
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("GetNextSnap(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("GetNextSnap(4) {0}".format(e))
        return 0
    c = conn.cursor()
    c.execute("SELECT last_snap FROM key where key = ?", (1,))
    value = c.fetchone()
    conn.close()
    if (verbose):
        print ("***\n")
    answer = 0
    return (value[0] + 1)

def BumpSnap(verbose):
    if (verbose):
        print ("***")
    d, t = GetDefaults(verbose)
    username = getpass.getuser()
    db_file = username + "/archive.db"
    if (verbose):
        print ("BumpSnap(1) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("BumpSnap(2) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("BumpSnap(3) {0}".format(e))
        return False
    snap = GetNextSnap(verbose)
    c = conn.cursor()
    if (snap != 0):
        c.execute("UPDATE key SET last_snap = (?) WHERE key = ?", (snap, 1,))
        if ("tradier key" in d):
            c.execute("UPDATE key SET tradier_key = (?) WHERE key = ?", (d['tradier key'], 1,))
        if ("IEX key" in d):
            c.execute("UPDATE key SET IEX_key = (?) WHERE key = ?", (d['IEX key'], 1,))
        if ("coin key" in d):
            c.execute("UPDATE key SET coin_key = (?) WHERE key = ?", (d['coin key'], 1,))
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    return True

def SnapTables(verbose):
    if (verbose):
        print ("***")
    aim = GetAIM(verbose)
    if aim == []:
        if (verbose):
            print ("SnapTables(1) error: aim dbase is empty - cannot archive")
        return False
    folder = GetFolder(verbose)
    if folder == []:
        if (verbose):
            print ("SnapTables(2) error: folder dbase is empty - cannot archive")
        return False
    market, worksheet = GetWorksheet("", verbose)
    if worksheet == []:
        if (verbose):
            print ("SnapTables(3) error: worksheet dbase is empty - continuing")
    snap = GetNextSnap(verbose)
    if (snap == 0):
        if (verbose):
            print ("SnapTables(3) error: next snapshot is zero - cannot archive")
        return False
    username = getpass.getuser()
    db_file = username + "/archive.db"
    if (verbose):
        print ("SnapTables(4) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("SnapTables(5) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("SnapTables(6) {0}".format(e))
        return False
    c = conn.cursor()
    for i in aim:
        c.execute( "INSERT OR IGNORE INTO aim VALUES(?, (?), ?, ?, ?, ?, ?, ?)", (snap, i['post date'], i['stock value'], i['cash'], i['portfolio control'], i['buy sell advice'], i['market order'], i['portfolio value'],))
        for j in i['json string']:
            if ("symbol" in j):
                if ("shares" in j):
                    c.execute( "INSERT OR IGNORE INTO shares VALUES(?, (?), (?), ?, ?, ?)", (snap, i['post date'], j['symbol'], j['crypto'], j['balance'], j['shares'],))
                else:
                    c.execute( "INSERT OR IGNORE INTO shares VALUES(?, (?), (?), ?, ?, ?)", (snap, i['post date'], j['symbol'], j['crypto'], j['balance'], 0,))
    dt = datetime.datetime.now()
    for f in folder:
        if ("symbol" in f):
            if ("shares" in f):
                c.execute( "INSERT OR IGNORE INTO shares VALUES(?, (?), (?), ?, ?, ?)", (snap, dt.strftime('%Y/%m/%d'), f['symbol'], f['crypto'], f['balance'], f['shares'],))
            else:
                c.execute( "INSERT OR IGNORE INTO shares VALUES(?, (?), (?), ?, ?, ?)", (snap, dt.strftime('%Y/%m/%d'), f['symbol'], f['crypto'], f['balance'], 0,))
    if worksheet != []:
        for w in worksheet:
            c.execute( "INSERT OR IGNORE INTO worksheet VALUES(?, (?), (?), ?, ?, ?)", (snap, w['plan date'], w['symbol'], f['crypto'], w['shares'], w['adjust amount'],))
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    return True

def SummaryCounts(verbose):
    username = getpass.getuser()
    db_file = username + "/archive.db"
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (verbose):
        print ("***")
    snap = GetNextSnap(verbose)
    if (snap == 0):
        if (verbose):
            print ("SummaryCounts(1) error: next snapshot is zero - cannot archive")
        return 0, 0, 0
    if (verbose):
        print ("SummaryCounts(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("SummaryCounts(2) {0} file is missing, cannot return the row counts".format(db_file))
            print ("***\n")
        return 0, 0, 0
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("SummaryCounts(2) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("SummaryCounts(3) {0}".format(e))
        return 0, 0
    c = conn.cursor()
    aim_count = ""
    if (checkTableExists(conn, "aim")):
        c.execute("select * from aim where snapshot = ?", (snap,))
        aim_count = c.fetchall()
    shares_count = ""
    if (checkTableExists(conn, "shares")):
        c.execute("select * from shares where snapshot = ?", (snap,))
        shares_count = c.fetchall()
    worksheet_count = ""
    if (checkTableExists(conn, "worksheet")):
        c.execute("select * from worksheet where snapshot = ?", (snap,))
        worksheet_count = c.fetchall()
    conn.close()
    if (verbose):
        print ("***\n")
    return len(aim_count), len(shares_count), len(worksheet_count)

def SnapSummary(verbose):
    if (verbose):
        print ("***")
    defaults, t = GetDefaults(verbose)
    folder_name = ""
    if "folder name" in defaults:
        folder_name = defaults['folder name']
    if (folder_name == ""):
        if (verbose):
            print ("SnapSummary(1) error: folder name is blank - cannot archive")
        return False
    snap = GetNextSnap(verbose)
    if (snap == 0):
        if (verbose):
            print ("SnapSummary(2) error: next snapshot is zero - cannot archive")
        return False
    first = GetFirstAIM(verbose)
    initial = 0
    if ("portfolio value" not in first):
        if (verbose):
            print ("SnapSummary(3) could not get initial balance - strange issue, continuing")
    else:
        initial = first['portfolio value']
    aim_count, shares_count, worksheet_count = SummaryCounts(verbose)
    if (aim_count == 0):
        if (verbose):
            print ("SnapSummary(4) warning: aim table has no records - strange issue, continuing")
    if (shares_count == 0):
        if (verbose):
            print ("SnapSummary(5) warning: shares table has no records - strange issue, continuing")
    if (worksheet_count == 0):
        if (verbose):
            print ("SnapSummary(5) warning: worksheet table has no records, continuing")
    look, table, db_values = Look(verbose)
    profit_percent = "0"
    if "profit percent" in look:
        profit_percent = look['profit percent'] 
    username = getpass.getuser()
    db_file = username + "/archive.db"
    if (verbose):
        print ("SnapSummary(6) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("SnapSummary(7) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("SnapSummary(8) {0}".format(e))
        return False
    dt = datetime.datetime.now()
    c = conn.cursor()
    c.execute( "INSERT OR IGNORE INTO summary VALUES((?), (?), ?, ?, ?, ?, ?, ?)", (dt.strftime('%Y/%m/%d'), folder_name, snap, aim_count, shares_count, worksheet_count, initial,
        to_number(profit_percent, verbose) * 100,))
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    return True

def CreateArchive(verbose):
    username = getpass.getuser()
    db_file = username + "/archive.db"
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (verbose):
        print ("***")
        print ("CreateArchive(1) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("CreateArchive(2) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("CreateArchive(3) {0}".format(e))
        return False
    c = conn.cursor()
    c.execute("CREATE TABLE if not exists `key` ( `key` INTEGER NOT NULL UNIQUE, `last_snap` INTEGER, `tradier_key` TEXT, `IEX_key` TEXT, `coin_key` TEXT )")
    c.execute( "INSERT OR IGNORE INTO key(key, last_snap, tradier_key, IEX_key, coin_key) VALUES(?, ?, ?, ?, ?)", (1,0,"","","",))
    c.execute("CREATE TABLE if not exists 'summary' ( `snap_date` TEXT NOT NULL, `folder_name` TEXT NOT NULL, `snapshot` INTEGER NOT NULL, `aim_rows` INTEGER, `shares_rows` INTEGER, `worksheet_rows` INTEGER, `initial` REAL, `profit_percent` INTEGER, PRIMARY KEY(`snap_date`,`folder_name`,`snapshot`) )")
    c.execute("CREATE TABLE if not exists 'aim' ( `snapshot` INTEGER NOT NULL, `post_date` TEXT NOT NULL, `stock_value` REAL, `cash` REAL, `portfolio_control` REAL, `buy_sell_advice` REAL, `market_order` REAL, `portfolio_value` REAL, PRIMARY KEY(`snapshot`,`post_date`) )")
    c.execute("CREATE TABLE if not exists 'shares' ( `snapshot` INTEGER NOT NULL, `post_date` TEXT NOT NULL, `symbol` TEXT NOT NULL, `crypto` INTEGER, `balance` REAL, `shares` REAL, PRIMARY KEY(`snapshot`,`post_date`,`crypto`,`symbol`) )")
    c.execute("CREATE TABLE if not exists `worksheet` ( `snapshot` INTEGER NOT NULL, `plan_date` TEXT NOT NULL, `symbol` TEXT NOT NULL, `crypto` INTEGER, `shares` REAL, `adjust_amount` REAL, PRIMARY KEY(`snapshot`,`plan_date`,`crypto`,`symbol`) )")
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    return True

def GetDetail(snapshot, verbose):
    username = getpass.getuser()
    db_file = username + "/archive.db"
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (verbose):
        print ("***")
        print ("GetDetail(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("GetDetail(2) {0} file is missing, cannot return the rows".format(db_file))
            print ("***\n")
        return [], [], []
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("GetDetail(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("GetDetail(4) {0}".format(e))
        return [], [], []
    c = conn.cursor()
    c.execute("SELECT * FROM aim where snapshot = ? order by post_date", (snapshot,))
    keys_aim = list(map(lambda x: x[0].replace("_"," "), c.description))
    values_aim = c.fetchall()
    c.execute("SELECT * FROM shares where snapshot = ? order by post_date", (snapshot,))
    keys_share = list(map(lambda x: x[0].replace("_"," "), c.description))
    values_share = c.fetchall()
    c.execute("SELECT * FROM worksheet where snapshot = ? order by plan_date", (snapshot,))
    keys_worksheet = list(map(lambda x: x[0].replace("_"," "), c.description))
    values_worksheet = c.fetchall()
    conn.close()
    if (verbose):
        print ("***\n")
    answer_aim = []
    for row in values_aim:
        answer_aim.append(dict(zip(keys_aim, row)))
    answer_share = []
    for row in values_share:
        answer_share.append(dict(zip(keys_share, row)))
    answer_worksheet = []
    for row in values_worksheet:
        answer_worksheet.append(dict(zip(keys_worksheet, row)))
    return answer_aim, answer_share, answer_worksheet

def GetSummary(verbose):
    username = getpass.getuser()
    db_file = username + "/archive.db"
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (verbose):
        print ("***")
        print ("GetSummary(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("GetSummary(2) {0} file is missing, cannot return the rows".format(db_file))
            print ("***\n")
        return []
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("GetSummary(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("GetSummary(4) {0}".format(e))
        return []
    c = conn.cursor()
    c.execute("SELECT * FROM summary order by snap_date,snapshot")
    keys = list(map(lambda x: x[0].replace("_"," "), c.description))
    values = c.fetchall()
    conn.close()
    if (verbose):
        print ("***\n")
    answer = []
    for row in values:
        answer.append(dict(zip(keys, row)))
    return answer

def PrintSummary(verbose):
    username = getpass.getuser()
    db_file = username + "/archive.db"
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (verbose):
        print ("***")
        print ("PrintSummary(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("PrintSummary(2) {0} file is missing, cannot display".format(db_file))
            print ("***\n")
        return ""
    summary = GetSummary(verbose)
    if (summary == []):
        return ""
    keys_dict = summary[0].keys()
    keys = []
    for key in keys_dict:
        keys.append(key)
    TableCls = create_table('TableCls')
    for key in keys:
        TableCls.add_column(key, Col(key))
    items = []
    answer = {}
    for s in summary:
        row = []
        for value in s.values():
            row.append(value)
        col_list = []
        for i in range(len(keys)):
            if keys[i] == "initial":
                col_list.append(as_currency(row[i]))
            elif keys[i] == "profit percent":
                col_list.append(as_percent(row[i]))
            else:
                col_list.append(row[i])
        answer = dict(zip(keys, col_list))
        items.append(answer)
    table = TableCls(items, html_attrs = {'width':'100%','border-spacing':0})
    if (verbose):
        print ("***\n")
    button_table = AddSummaryButton(table.__html__())
    return button_table

def AddSummaryButton(table):
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
        find = table.find("</td>", start + 8)
        snap_date = table[start + 8 : find]
        next_field = find + 9
        find = table.find("</td>", next_field)
        folder_name =  table[next_field: find]
        next_field = find + 9
        find = table.find("</td>", next_field)
        snapshot =  table[next_field: find]
        row += 1
        r_button = '<tr><td><form action="#" method="post"><input class="submit" type="submit" name="action" value="remove"/><input hidden type="text" name="remove_snapshot" value="{0}"/></form></td><td>'.format(snapshot)
        table = table[0 : start] + table[start:].replace(pattern, r_button, 1)
        index = start + 1
    return table

def DeleteSnapshot(snapshot, verbose):
    username = getpass.getuser()
    db_file = username + "/archive.db"
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (verbose):
        print ("***")
        print ("DeleteSnapshot(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("DeleteSnapshot(2) {0} file is missing, cannot continue".format(db_file))
            print ("***\n")
        return False
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("DeleteSnapshot(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("DeleteSnapshot(4) {0}".format(e))
        return False
    c = conn.cursor()
    c.execute("DELETE FROM summary where snapshot = ?", (int(snapshot),))
    c.execute("DELETE FROM aim where snapshot = ?", (int(snapshot),))
    c.execute("DELETE FROM shares where snapshot = ?", (int(snapshot),))
    c.execute("DELETE FROM worksheet where snapshot = ?", (int(snapshot),))
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    return True
#endregion history
#region names
def GetNames(verbose):
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
        print ("CreateNames(2) db_name: {0}".format(db_name))
        print ("CreateNames(3) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("CreateNames(4) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("CreateNames(5) {0}".format(e))
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
#region utils
def noteDate(value):
    if (value == ""):
        return ""
    dt = datetime.datetime.strptime(value, '%Y/%m/%d') 
    return custom_strftime('%B {S}, %Y', dt)

def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

def to_number(string, verbose):
    negative = False
    percent = False
    if ('(' in string):
        negative = True
    if ('%' in string):
        percent = True
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
    clean_number = myFloat(string)
    if (percent):
        clean_number = clean_number / 100.
    if (negative):
        clean_number = - clean_number
    if (verbose):
        print ("to_number(9) clean_number: {0}".format(clean_number))
        print ("***\n")
    return clean_number

def as_big(amount):
    if (amount is None):
        amount = 0
    if amount >= 0:
        return '${:,.8f}'.format(amount)
    else:
        return '(${:,.8f})'.format(-amount)

def as_currency(amount):
    if (amount is None):
        amount = 0
    if amount >= 0:
        return '${:,.2f}'.format(amount)
    else:
        return '(${:,.2f})'.format(-amount)

def as_shares(amount):
    return '\r{:.8f}'.format(amount)

def as_percent(amount):
    if amount >= 0:
        return "{:.2f}%".format(amount)
    else:
        return '({:.2f}%)'.format(-amount)

def checkTableExists(dbcon, tablename):
    dbcur = dbcon.cursor()
    dbcur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=(?);", (tablename,))
    test = dbcur.fetchone()
    if test is None:
        dbcur.close()
        return False
    dbcur.close()
    return True

def CheckPretty(ex):
    ex = ex.rstrip()
    if re.match(r'^[a-zA-Z0-9][ A-Za-z0-9_-]*$', ex):
        return True
    return False

def parse_wmic_output(text):
    result = []
    # remove empty lines
    lines = [s for s in text.splitlines() if s.strip()]
    # No Instance(s) Available
    if len(lines) == 0:
        return result
    header_line = lines[0]
    # Find headers and their positions
    headers = re.findall('\S+\s+|\S$', header_line)
    pos = [0]
    for header in headers:
        pos.append(pos[-1] + len(header))
    for i in range(len(headers)):
        headers[i] = headers[i].strip()
    # Parse each entries
    for r in range(1, len(lines)):
        row = {}
        for i in range(len(pos)-1):
            row[headers[i]] = lines[r][pos[i]:pos[i+1]].strip()
        result.append(row)
    return result

def get_pid(name):
    if os.name == 'nt':
        child = subprocess.Popen('wmic path win32_process get CommandLine, processId', stdout=subprocess.PIPE, shell=False)
        response = parse_wmic_output(child.communicate()[0].decode("utf-8"))
        pid = ""
        for itm in response:
            if (name in itm['CommandLine']):
                pid = itm['ProcessId']
        response = pid
    else:
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
    if os.name == 'nt':
        shell = "start /min {0}".format(name)
        os.system(shell)
    else:
        os.system(name)

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
#endregion utils
#region worksheet
def CreateWorksheet(verbose):
    db_file = GetDB(verbose)
    username = getpass.getuser()
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (verbose):
        print ("***")
        print ("CreateWorksheet(1) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("CreateWorksheet(2) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("CreateWorksheet(3) {0}".format(e))
        return False
    c = conn.cursor()
    c.execute("CREATE TABLE if not exists 'market' ( `key` INTEGER NOT NULL UNIQUE, `market_order` REAL, `post_date` TEXT, `actual_amount` REAL, `posted` TEXT, PRIMARY KEY(`key`) )")
    c.execute("CREATE TABLE if not exists `worksheet` ( `plan_date` TEXT NOT NULL, `symbol` TEXT NOT NULL, `crypto` INTEGER, `shares` REAL, `adjust_amount` REAL, PRIMARY KEY(`plan_date`,`crypto`,`symbol`) )")
    c.execute( "INSERT OR IGNORE INTO market(key) VALUES(?)", (1,))
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    return True

def BeginWorksheet(market_order, verbose):
    db_file = GetDB(verbose)
    username = getpass.getuser()
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (verbose):
        print ("***")
        print ("BeginWorksheet(1) dbase: {0}".format(db_file))
        print ("BeginWorksheet(2) market order: {0}".format(market_order))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("BeginWorksheet(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("BeginWorksheet(4) {0}".format(e))
        return False
    folder = GetFolder(verbose)
    if (folder == []):
        if (verbose):
            print("BeginWorksheet(5) no portfolio is entered, cannot begin a worksheet")
        return False
    status = CreateWorksheet(verbose)
    if (status):
        dt = datetime.datetime.now()
        today = dt.strftime('%Y/%m/%d')
        c = conn.cursor()
        c.execute("UPDATE market SET market_order = ? WHERE key = ?", (market_order, 1,))
        c.execute("UPDATE market SET actual_amount = ? WHERE key = ?", (0, 1,))
        c.execute("UPDATE market SET post_date = ? WHERE key = ?", (today, 1,))
        c.execute("UPDATE market SET posted = (?) WHERE key = ?", ("no", 1,))
        for f in folder:
            c.execute( "INSERT OR IGNORE INTO worksheet VALUES((?),(?),?, ?,?)", (today, f['symbol'], f['crypto'], 0, 0,))
        conn.commit()
        conn.close()
    else:
        if (verbose):
            print("BeginWorksheet(6) could not create a worksheet table")
    if (verbose):
        print ("***\n")
    return True

def GetWorksheet(what, verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
        print ("GetWorksheet(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("GetWorksheet(2) {0} file is missing, cannot return the worksheet".format(db_file))
            print ("***\n")
        return {}, []
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("GetWorksheet(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("GetWorksheet(4) {0}".format(e))
        return {}, []
    market = {}
    worksheet = []
    if (checkTableExists(conn, "worksheet")):
        c = conn.cursor()
        c.execute("SELECT * FROM market where key = 1")
        keys = list(map(lambda x: x[0].replace("_"," "), c.description))
        values = c.fetchone()
        if values is None:
            market = {}
        else:
            market = dict(zip(keys, values))
        if (what == "latest" and market['post date'] is not None):
            dt = datetime.datetime.strptime(market['post date'], "%Y/%m/%d")
            theDate = dt.strftime('%Y/%m/%d')
            c.execute("SELECT * FROM worksheet where plan_date = (?) order by crypto, symbol", (theDate,))
        else:
            c.execute("SELECT * FROM worksheet order by plan_date, crypto, symbol")
        keys = list(map(lambda x: x[0].replace("_"," "), c.description))
        values = c.fetchall()
        conn.close()
        for row in values:
            worksheet.append(dict(zip(keys, row)))
    if (verbose):
        print ("***\n")
    return market, worksheet

def PrintWorksheet(verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
        print ("PrintWorksheet(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("PrintWorksheet(2) {0} file is missing, cannot display".format(db_file))
            print ("***\n")
        return "", ""
    market, worksheet = GetWorksheet("latest", verbose)
    if (market == {} or worksheet == []):
        return "", ""
    dt = datetime.datetime.now()
    today = dt.strftime('%Y/%m/%d')
    if (market['posted'] == "yes" or market["post date"] != today):
        return "", ""
    keys_dict = worksheet[0].keys()
    keys = []
    for key in keys_dict:
        if (key != "plan date"):
            keys.append(key)
    TableCls = create_table('TableCls')
    for key in keys:
        TableCls.add_column(key, Col(key))
    items = []
    answer = {}
    for w in worksheet:
        row = []
        for value in w.values():
            row.append(value)
        col_list = []
        index = -1
        symbol = ""
        for key in keys_dict:
            index += 1
            if (key == "symbol"):
                symbol = row[index]
            if key != "plan date":
                if key == "shares":
                    if (symbol == "$"):
                        col_list.append("")
                    else:
                        col_list.append(as_shares(abs(row[index])))
                elif key == "adjust amount":
                    if (symbol == "$"):
                        col_list.append(as_big(row[index]))
                    else:
                        col_list.append(as_big(abs(row[index])))
                else:
                    col_list.append(row[index])
        answer = dict(zip(keys, col_list))
        items.append(answer)
    table = TableCls(items, html_attrs = {'width':'100%','border-spacing':0})
    input_box_table = AddInputBox(table.__html__(), market)
    worksheet_warning = ""
    allocate = abs(market['market order']) - abs(market['actual amount'])
    if (allocate == 0):
        worksheet_warning = "You are good to go"
    elif (allocate > 0):
        worksheet_warning = "You still have {0} yet to allocate".format(as_currency(abs(allocate)))
    else:
        worksheet_warning = "You have allocated {0} more than {1}".format(as_currency(abs(allocate)), as_currency(abs(market['market order'])))
    if (verbose):
        print ("***\n")
    return input_box_table, worksheet_warning

def AddInputBox(table, market):
    if (market['market order'] < 0):
        table = table.replace("</tr></thead>", "<th>Signal to Sell {0} at Market</th></tr></thead>".format(as_currency(-market['market order'])), 1)
    else:
        table = table.replace("</tr></thead>", "<th>Signal to Buy {0} at Market</th></tr></thead>".format(as_currency(market['market order'])), 1)
    pattern = "<tr><td>"
    index = 0
    done = False
    while (not done):
        start = table.find(pattern, index)
        if start == -1:
            done = True
            continue
        symbol = table[start + 8 :table.find("</td>", start + 8)]
        if (symbol == "$"):
            table = table[0 : start] + table[start:].replace("</td></tr>", "<td></td></td></tr>", 1)
        else:
            r_box = '<td><input class="submit" type="text" name="box_{0}" value=""/></td></tr>'.format(symbol)
            table = table[0 : start] + table[start:].replace("</td></tr>", r_box, 1)
        index = start + 1
    return table

def CalculateWorksheet(adjust, verbose):
    db_file = GetDB(verbose)
    username = getpass.getuser()
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (verbose):
        print ("***")
        print ("CalculateWorksheet(1) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("CalculateWorksheet(2) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("CalculateWorksheet(3) {0}".format(e))
        return False
    folder = GetFolder(verbose)
    if (folder == []):
        if (verbose):
            print("CalculateWorksheet(4) no portfolio is entered, cannot begin a worksheet")
        return False
    market, worksheet = GetWorksheet("latest", verbose)
    if (market == {} or worksheet == []):
        return False
    negative = False
    if (market['market order'] < 0):
        negative = True
    dt = datetime.datetime.now()
    today = dt.strftime('%Y/%m/%d')
    c = conn.cursor()
    for a in adjust:
        for w in worksheet:
            if (w['symbol'] != "$"):
                if (w['symbol'] == a['symbol']) and (w['crypto'] == a['crypto']):
                    a['amount'] = abs(w['adjust amount']) + to_number(a['adjust'], verbose)
                    if (a['amount'] < 0):
                        a['amount'] = 0
                    if (negative):
                        a['amount'] = -a['amount']
                    c.execute("UPDATE worksheet SET adjust_amount = ? WHERE plan_date = (?) and symbol = (?) and crypto = ?", 
                        (a['amount'], today, a['symbol'], a['crypto'],))
    cash = 0
    total = 0
    for a in adjust:
        cash = cash + a['amount']
        total = total + a['amount']
    cash = -cash
    c.execute("UPDATE worksheet SET adjust_amount = ? WHERE plan_date = (?) and symbol = (?) and crypto = 0", (cash, today, "$",))
    c.execute("UPDATE market SET actual_amount = ? WHERE key = ?", (total, 1,))
    for a in adjust:
        for f in folder:
            if (f['symbol'] != "$"):
                if (f['symbol'] == a['symbol']) and (f['crypto'] == a['crypto']):
                    shares = 0.0
                    if (f['price'] > 0):
                        shares = a['amount'] / f['price']
                        c.execute("UPDATE worksheet SET shares = ? WHERE plan_date = (?) and symbol = (?) and crypto = ?", 
                            (shares, today, a['symbol'], a['crypto'],))
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    return True

def PostWorksheet(verbose):
    db_file = GetDB(verbose)
    if (verbose):
        print ("***")
        print ("PostWorksheet(1) dbase: {0}".format(db_file))
    result = CreateFolder("$", 0, verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("PostWorksheet(2) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("PostWorksheet(3) {0}".format(e))
            return False
        market, worksheet = GetWorksheet("latest", verbose)
        if (market == {} or worksheet == []):
            return False
        folder = GetFolder(verbose)
        if folder == []:
            return False
        if (market['posted'] == "yes"):
            if (verbose):
                print("PostWorksheet(4) Already posted, quiting")
            return False
        c = conn.cursor()
        for w in worksheet:
            for f in folder:
                if (w['symbol'] == f['symbol']) and (w['crypto'] == f['crypto']):
                    if (w['symbol'] == "$"):
                        amount = f['balance'] + w['adjust amount']
                        c.execute("UPDATE folder SET balance = ? WHERE symbol = '$' and crypto = 0", (amount,))
                    else:
                        amount = f['shares'] + w['shares']
                        c.execute("UPDATE folder SET shares = ? WHERE symbol = (?) and crypto = ?", (amount, w['symbol'], w['crypto'],))
        c.execute("UPDATE market SET posted = (?) WHERE key = 1", ("yes",))
        c.execute("DELETE from worksheet WHERE adjust_amount = 0")
        conn.commit()
        conn.close()
    if (verbose):
        print ("***\n")
    return True
#endregion worksheet
