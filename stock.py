#!/usr/bin/env python3

import sys, getopt
import plumb
import pdb
import os
import pprint

def main(argv):
    verbose = False
    test = False
    quote = ""
    company = ""
    getkey = False
    savekey = ""
    interval = 15
    update_interval = False
    daemon = 1200
    update_daemon = False
    try:
        opts, args = getopt.getopt(argv, "d:i:s:gq:hvtc:", ["help", "verbose", "test", "quote=", "save_key=", "get_key", "company=", "interval=", "daemon="])
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
        elif o in ("-i", "--interval"):
            if (a.isnumeric()):
                interval = int(a)
                if (interval > 60):
                    interval = 60
                if (interval < 1):
                    interval = 1
                update_interval = True
            else:
                interval = 15
        elif o in ("-d", "--daemon"):
            if (a.isnumeric()):
                daemon = int(a)
                if (daemon > 1200):
                    daemon = 1200
                if (daemon < 60):
                    daemon = 60
                update_daemon = True
            else:
                daemon = 1200
        elif o in ("-q", "--quote"):
            quote = a.upper()
        elif o in ("-c", "--company"):
            company = a.upper()
        elif o in ("-g", "--get_key"):
            getkey = True
        elif o in ("-s", "--save_key"):
            savekey = a.upper()
        else:
            assert False, "unhandled option"
    if (test):
        testResult = plumb.TestStock(verbose)
        if (testResult):
            print ("Test result - pass")
        else:
            print ("Test result - fail")
        exit()
    if (update_interval):
        result = plumb.Interval(interval, verbose)
        if (result):
            print ("saved.")
        else:
            print ("failed.")
        exit()
    if (update_daemon):
        result = plumb.Daemon(daemon, verbose)
        if (result):
            print ("saved.")
        else:
            print ("failed.")
        exit()
    if (savekey > ""):
        saveResult = plumb.Save(savekey, verbose)
        if (saveResult):
            print ("saved.")
        else:
            print ("failed.")
        exit()
    if (getkey):
        keyResult = plumb.Key(verbose)
        if (keyResult):
            print ("key = {0}".format(keyResult))
        else:
            print ("key was not returned.")
        exit()
    if (quote > ""):
        quoteResult = plumb.Quote(quote, verbose)
        pprint.pprint(quoteResult)
        exit()
    if (company > ""):
        companyResult = plumb.Company(company, verbose)
        if (verbose):
            pprint.pprint(companyResult)
        if (companyResult):
            print ("\nCompany {0} = {1}\n".format(company, companyResult['companyName']))
        else:
            print ("\nfailed.\n")
        exit()
    usage()

def usage():
    usage = """
    ******************
    **  Stock Tool  **
    ******************

    -h --help           prints this help
    -v --verbose        increases the information level
    -t --test           tests the stock routines
    -q --quote          get stock quote from ticker symbol
    -s --save_key       stores the api key in database
    -g --get_key        retrieves the api key from the database
    -c --company        retrieves company data from ticker symbol
    -i --interval       saves the time interval (default is 15 minutes)
    -d --daemon         saves the daemon seconds (default is 1200)        
    """
    print (usage) 

if __name__ == "__main__":
  main(sys.argv[1:])
