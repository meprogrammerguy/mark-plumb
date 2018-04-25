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

#region stock
def TestStock(verbose):
    count = 0
    if (verbose):
        print ("Test #1 - Company(AAPL, verbose)")
    result = Company("AAPL", verbose)
    if (result['companyName'] == "Apple Inc."):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #2 - Save(TEST, test.db, verbose)")
    result = Save("TEST","test.db", verbose)
    if (result):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #3 - Key(test.db, verbose)")
    result = Key("test.db", verbose)
    if (result == "TEST"):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    if (verbose):
        print ("Test #4 - Quote(AAPL, test.db, verbose)")
    result = Quote("AAPL", "test.db", verbose)
    if (result['Meta Data']['2. Symbol'] == "AAPL"):
        if (verbose):
            print ("\tpass.")
        count += 1
    else:
        if (verbose):
            print ("\tfail.")
    username = getpass.getuser()
    db_file = username + "/" + "test.db"
    os.unlink(db_file)
    if (verbose):
        print ("Test #3 - Cleanup, remove {0}".format(db_file))
    if (count == 4):
        return True
    return False

def Quote(ticker, dbase, verbose):
    key = Key(dbase, verbose)
    url = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={0}&interval=15min&apikey={1}".format(ticker, key)
    if (verbose):
        print ("***")
        print ("Quote(1) key: {0}".format(key))
        print ("Quote(2) ticker: {0}".format(ticker))
        print ("Quote(3) url: {0}".format(url))
    try:
        with contextlib.closing(urllib.request.urlopen(url)) as page:
            soup = BeautifulSoup(page, "html5lib")
    except urllib.error.HTTPError as err:
        if err.code == 404:
            if (verbose):
                print ("Quote(4) page not found for {0}".format(ticker))
                print ("***\n")
            return {}
        else:
            raise
    returnQuote = json.loads(str(soup.text))
    if (verbose):
        print ("***\n")
    return returnQuote

def Company(ticker, verbose):
    url = "https://api.iextrading.com/1.0/stock/{0}/company".format(ticker)
    if (verbose):
        print ("***")
        print ("Company(1) ticker: {0}".format(ticker))
        print ("Company(2) url: {0}".format(url))
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

def Save(key, dbase, verbose):
    username = getpass.getuser()
    db_file = username + "/"  + dbase
    Path(username + "/").mkdir(parents=True, exist_ok=True) 
    if (verbose):
        print ("***")
        print ("Save(1) key: {0}".format(key))
        print ("Save(2) dbase: {0}".format(db_file))
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("Save(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("Save(4) {0}".format(e))
        return False
    c = conn.cursor()
    toCreate = "CREATE TABLE if not exists 'defaults' ( `username` TEXT NOT NULL UNIQUE, `api_key` TEXT, PRIMARY KEY(`username`) )"
    c.execute(toCreate)
    toExecute = "INSERT OR IGNORE INTO defaults(username) VALUES('{0}')".format(username)
    c.execute(toExecute)
    toUpdate = "UPDATE defaults SET api_key = '{0}' WHERE username = '{1}'".format(key, username)
    c.execute(toUpdate)
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    return True

def Key(dbase, verbose):
    username = getpass.getuser()
    db_file = username + "/" + dbase
    if (verbose):
        print ("***")
        print ("Key(1) dbase: {0}".format(db_file))
    if (not os.path.exists(db_file)):
        if (verbose):
            print ("Key(2) {0} file is missing, cannot return the key".format(db_file))
            print ("***\n")
        return ""
    try:
        conn = sqlite3.connect(db_file)
        if (verbose):
            print("Key(3) sqlite3: {0}".format(sqlite3.version))
    except Error as e:
        print("Key(4) {0}".format(e))
        return False
    c = conn.cursor()
    toExecute = "SELECT api_key FROM defaults WHERE username = '{0}'".format(username)
    c.execute(toExecute)
    answer = c.fetchone()
    conn.close()
    if (verbose):
        print ("***\n")
    return answer[0]
#endregion stock

#region folder
def TestFolder(verbose):
    return False

def Add(symbol, dbase, verbose):
    return True

def Remove(symbol, dbase, verbose):
    return True

def Cash(balance, dbase, verbose):
    username = getpass.getuser()
    db_file = username + "/"  + dbase
    if (verbose):
        print ("***")
        print ("Cash(1) balance: {0}".format(balance))
        print ("Cash(2) dbase: {0}".format(db_file))
    result = CreateFolder("$", dbase, verbose)
    if (result):
        try:
            conn = sqlite3.connect(db_file)
            if (verbose):
                print("Cash(3) sqlite3: {0}".format(sqlite3.version))
        except Error as e:
            print("Cash(4) {0}".format(e))
            return False
        c = conn.cursor()
        toUpdate = "UPDATE folder SET balance = {0} WHERE symbol = '$'".format(float(balance))
        c.execute(toUpdate)
        dict_string = {'companyName': 'CASH', 'description': 'Cash Account'}
        json_string = json.dumps(dict_string)
        toUpdate = "UPDATE folder SET json_string = '{0}' WHERE symbol = '$'".format(json_string)
        c.execute(toUpdate)
        toUpdate = "UPDATE folder SET shares = {0} WHERE symbol = '$'".format(float(balance))
        c.execute(toUpdate)
        conn.commit()
        conn.close()
    if (verbose):
        print ("***\n")
    return True

def CreateFolder(key, dbase, verbose):
    username = getpass.getuser()
    db_file = username + "/"  + dbase
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
    toCreate = "CREATE TABLE if not exists `folder` ( `symbol` TEXT NOT NULL UNIQUE, `json_string` TEXT, `balance` REAL, `shares` REAL, PRIMARY KEY(`symbol`) )"
    c.execute(toCreate)
    toExecute = "INSERT OR IGNORE INTO folder(symbol) VALUES('{0}')".format(key)
    c.execute(toExecute)
    conn.commit()
    conn.close()
    if (verbose):
        print ("***\n")
    return True
#endregion folder
