#!/usr/bin/env python3

import pdb
from bs4 import BeautifulSoup
import html5lib
import contextlib
import urllib.request
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
    try:
        with contextlib.closing(urllib.request.urlopen(url)) as page:
            soup = BeautifulSoup(page, "html5lib")
    except urllib.error.HTTPError as err:
        if err.code == 404:
            if (verbose):
                print ("Company(2) page not found for {0}".format(ticker))
                print ("***\n")
            return {}
        else:
            raise
    returnCompany = json.loads(str(soup.text))
    if (verbose):
        print ("Company(3) {0} = {1}".format(ticker, returnCompany['companyName']))
        print ("***\n")
    return returnCompany

def Save(key, dbase, verbose):
    print (key)
    return True

def Key(dbase, verbose):
    return "unknown"
