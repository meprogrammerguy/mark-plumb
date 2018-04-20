#!/usr/bin/env python3

import sys, getopt
import plumb
import pdb
import os

import settings

def main(argv):
    verbose = False
    test = False
    quote = ""
    company = ""
    getkey = False
    savekey = ""
    dbase = __file__
    dbase = dbase.replace(".py", ".db")
    dbase = dbase.replace("./", "")
    try:
        opts, args = getopt.getopt(argv, "s:gq:hvtc:", ["help", "verbose", "test", "quote=", "dbase=", "save_key=", "get_key", "company="])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-t", "--test"):
            test = True
        elif o in ("-h", "--help"):
            usage()
            exit()
        elif o in ("-q", "--quote"):
            quote = a.upper()
        elif o in ("-c", "--company"):
            company = a.upper()
        elif o in ("-d", "--dbase"):
            dbase = a.upper()
        elif o in ("-g", "--get_key"):
            getkey = True
        elif o in ("-s", "--save_key"):
            savekey = a.upper()
        else:
            assert False, "unhandled option"
    if (test):
        testResult = plumb.Test(verbose)
        if (testResult):
            print ("Test result - pass")
        else:
            print ("Test result - fail")
        exit()
    if (savekey > ""):
        saveResult = plumb.Save(savekey, dbase, verbose)
        print ("saved.")
        exit()
    if (getkey):
        keyResult = plumb.Key(dbase, verbose)
        print ("key = {0}".format(keyResult))
        exit()
    if (quote > ""):
        quoteResult = plumb.Quote(quote, dbase, verbose)
        exit()
    if (company > ""):
        quoteResult = plumb.Company(company, verbose)
        exit()
    usage()

def usage():
    usage = """
    ******************
    **  Stock Tool  **
    ******************

    -h --help           Prints this help
    -v --verbose        Increases the information level
    -t --test           runs test routine to check calculations
    -q --quote          get stock quote from ticker symbol
    -d --dbase          database name (stock.db is the default)
    -s --save_key       stores the api key in database
    -g --get_key        retrieves the api key from the database
    -c --company        retrieves company data from ticker symbol        
    """
    print (usage) 

if __name__ == "__main__":
  main(sys.argv[1:])
