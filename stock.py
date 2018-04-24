#!/usr/bin/env python3

import sys, getopt
import plumb
import pdb
import os
import pprint

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
        if (saveResult):
            print ("saved.")
        else:
            print ("failed.")
        exit()
    if (getkey):
        keyResult = plumb.Key(dbase, verbose)
        if (keyResult):
            print ("key = {0}".format(keyResult))
        else:
            print ("key was not returned.")
        exit()
    if (quote > ""):
        quoteResult = plumb.Quote(quote, dbase, verbose)
        count = 0
        close = "?"
        for key, values in quoteResult.items():
            if (key == "Error Message"):
                break
            if (key != "Meta Data"):
                for value in values.values():
                    close = value['4. close']
                    break
        if (verbose):
            pprint.pprint(quoteResult)
        else:
            if (quoteResult):
                print ("close: {0}".format(close))
            else:
                print ("failed.")
        exit()
    if (company > ""):
        companyResult = plumb.Company(company, verbose)
        if (verbose):
            pprint.pprint(companyResult)
        else:
            if (companyResult):
                print ("Company {0} = {1}".format(company, companyResult['companyName']))
            else:
                print ("failed.")
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
