#!/usr/bin/env python3

import sys, getopt
import plumb
import pdb
import os
import pprint
from datetime import datetime

def main(argv):
    verbose = False
    test = False
    quote = ""
    company = ""
    key = ""
    item = ""
    printout = False
    reset = False
    log = ""
    try:
        opts, args = getopt.getopt(argv, "l:rpi:k:q:hvtc:", ["help", "verbose", "test", "quote=", "key=", "company=", "item=", "print", "reset", "log="])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-t", "--test"):
            test = True
        elif o in ("-r", "--reset"):
            reset = True
        elif o in ("-p", "--print"):
            printout = True
        elif o in ("-h", "--help"):
            usage()
            exit()
        elif o in ("-i", "--item"):
            item = a
        elif o in ("-q", "--quote"):
            quote = a.upper()
        elif o in ("-c", "--company"):
            company = a.upper()
        elif o in ("-k", "--key"):
            key = a
        elif o in ("-l", "--log"):
            log = a.lower()
        else:
            assert False, "unhandled option"
    if (test):
        testResult = plumb.TestStock(verbose)
        if (testResult):
            print ("Test result - pass")
        else:
            print ("Test result - fail")
        exit()
    if (key > "" and item > ""):
        if item > "":
            result = plumb.UpdateDefaultItem(key, item, verbose)
            if (result):
                print ("saved.")
            else:
                print ("failed.")
        else:
            print ("you must use --item switch with the --key switch")
        exit()
    if (quote > ""):
        quoteResult = plumb.Quote(quote, verbose)
        pprint.pprint(quoteResult)
        exit()
    if (company > ""):
        companyResult = plumb.Company(company, verbose)
        pprint.pprint(companyResult)
        exit()
    if (printout):
        printResult, column_options, name_options, folder_options = plumb.PrintDefaults(verbose)
        pprint.pprint(printResult)
        pprint.pprint(column_options)
        pprint.pprint(folder_options)
        pprint.pprint(name_options)
        exit()
    if (reset):
        endResult = plumb.ResetDefaults(verbose)
        if (endResult):
            print ("saved.")
        else:
            print ("failed.")
        exit()
    if (log > ""):
        logResult, status = plumb.PrintDaemon(log, verbose)
        if (logResult > ""):
            pprint.pprint(logResult)
        else:
            print ("failed.")
        print("last status: {0}".format(status))
        exit()
    usage()

def usage():
    defaults, types = plumb.GetDefaults(False)
    keys = defaults.keys()
    key_list = ""
    for key in keys:
        if key != "username":
            key_list += "{0}\n\t\t\t\t".format(key)
    usage = """
    ******************
    **  Stock Tool  **
    ******************

    -h --help           prints this help
    -v --verbose        increases the information level
    -t --test           tests the stock routines
    -c --company        retrieves company data from ticker symbol
    -q --quote          get stock quote from ticker symbol

    -k --key            keys in dbase to update (used with --item switch)
                            *** keys currently in dbase ***
                                {0}
    -i --item           item value to update (used with --key switch)

    -p --print          print out the defaults database (in HTML table format)
    -r --reset          reset user back to standard defaults

    -l --log            show daemon log
                            --log='' (entire log), --log='wake' (wake status)
    """.format(key_list)
    print (usage) 

if __name__ == "__main__":
    main(sys.argv[1:])
