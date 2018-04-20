#!/usr/bin/env python3

import pdb
from bs4 import BeautifulSoup
import html5lib
import contextlib
from urllib.request import urlopen
import os
import json

import settings

def Test(verbose):
    return False

def Quote(ticker, dbase, verbose):
    print (ticker)
    return {}

def Company(ticker, verbose):
    url = "https://api.iextrading.com/1.0/stock/{0}/company".format(ticker)
    if (verbose):
        print ("***")
        print ("Company(1) url: {0}".format(url))
    with contextlib.closing(urlopen(url)) as page:
        soup = BeautifulSoup(page, "html5lib")
    returnCompany = json.loads(str(soup.text))
    if (verbose):
        print ("Company(2) {0} = {1}".format(ticker, returnCompany['companyName']))
        print ("***\n")
    return returnCompany

def Save(key, dbase, verbose):
    print (key)
    return True

def Key(dbase, verbose):
    return "unknown"
