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
    symbol = ""
    key = ""
    item = ""
    printout = False
    zap = False
    log = ""
    when = False
    get = False
    run = False
    daemon = False
    kill = False
    crypto = False
    try:
        opts, args = getopt.getopt(argv, "rdkgwl:zcpi:k:hvts:q:", ["help", "verbose", "test", "quote=", "key=", "symbol=", "item=",
            "print", "zap", "log=", "when", "get", "run", "daemon", "kill", "crypto"])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-t", "--test"):
            test = True
        elif o in ("-g", "--get"):
            get = True
        elif o in ("-r", "--run"):
            run = True
        elif o in ("-d", "--daemon"):
            daemon = True
        elif o in ("-c", "--crypto"):
            crypto = True
        elif o in ("-k", "--kill"):
            kill = True            
        elif o in ("-w", "--when"):
            when = True
        elif o in ("-z", "--zap"):
            zap = True
        elif o in ("-p", "--print"):
            printout = True
        elif o in ("-h", "--help"):
            usage()
            exit()
        elif o in ("-i", "--item"):
            item = a
        elif o in ("-q", "--quote"):
            quote = a.upper()
        elif o in ("-s", "--symbol"):
            symbol = a.upper()
        elif o in ("-k", "--key"):
            key = a
        elif o in ("-l", "--log"):
            log = a.lower()
        else:
            assert False, "unhandled option"
    if (test):
        testResult = plumb.TestDefaults(verbose)
        print (testResult['output'])
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
    if (quote > "" and not crypto):
        quoteResult = plumb.QuoteTradier(quote, verbose)
        pprint.pprint(quoteResult)
        exit()
    if (symbol > "" and not crypto):
        companyResult = plumb.Company(symbol, verbose)
        pprint.pprint(companyResult)
        exit()
    if (quote > "" and crypto):
        quoteResult = plumb.QuoteCrypto(quote, verbose)
        pprint.pprint(quoteResult)
        exit()
    if (symbol > "" and crypto):
        companyResult = plumb.CryptoCompany(symbol, verbose)
        pprint.pprint(companyResult)
        exit()
    if (printout):
        printResult, column_options, name_options, folder_options = plumb.PrintDefaults(verbose)
        pprint.pprint(printResult)
        pprint.pprint(column_options)
        pprint.pprint(folder_options)
        pprint.pprint(name_options)
        exit()
    if (zap):
        endResult = plumb.ResetDefaults(verbose)
        if (endResult):
            print ("saved.")
        else:
            print ("failed.")
        exit()
    if (run):
        if os.name == 'nt':
            runResult = plumb.run_script("poll_stocks.py")
        else:
            runResult = plumb.run_script("./folder_daemon.py")
        exit()
    if (daemon):
        if os.name == 'nt':
            checkResult = plumb.get_pid("poll_stocks.py")
        else:
            checkResult = plumb.get_pid("folder_daemon.py")
        if (checkResult != []):
            log = "stock polling app is running at pid: {0}".format(checkResult)
            print (log)
        else:
            print ("stock polling app is not running")
        exit()
    if (kill):
        if os.name == 'nt':
            checkResult = plumb.get_pid("poll_stocks.py")
        else:
            checkResult = plumb.get_pid("folder_daemon.py")
        if (checkResult != []):
            plumb.kill_pid(checkResult[0])
        else:
            print ("stock polling app is not running")
        exit()
    if (log > ""):
        logResult, status = plumb.PrintDaemon(log, verbose)
        if (logResult > ""):
            pprint.pprint(logResult)
        else:
            print ("failed.")
        print("last status: {0}".format(status))
        exit()
    if (when):
        whenResult = plumb.Holiday(verbose)
        if (whenResult):
            pprint.pprint(whenResult)
        else:
            print ("failed.")
        exit()
    if (get):
        getResult, types = plumb.GetDefaults(verbose)
        if (getResult):
            pprint.pprint(getResult)
        else:
            print ("failed.")
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
    *********************
    **  Defaults Tool  **
    *********************

    -h  --help          prints this help
    -v  --verbose       increases the information level
    -t  --test          tests the default routines
    -c  --crypto        use crypto-coin API (used with --symbol or --quote)

    -s  --symbol        retrieves company data from ticker symbol
    -q  --quote         get stock quote from ticker symbol(s)
    -w  --when          retrieves the stock exchange holiday information

    -k  --key           keys in dbase to update (used with --item switch)
                            *** keys currently in dbase ***
                                {0}
    -i  --item          item value to update (used with --key switch)

    -p  --print         print out the defaults database (in HTML table format)
    -z  --zap           zap user back to standard defaults
    -g  --get           Gets/Shows all default fields

    -l  --log           show daemon log
                            --log='' (entire log), --log='wake' (wake status)
    -r  --run           runs stock polling app
    -c  --check         checks if stock polling app is running
    -k  --kill          kills stock polling app
    """.format(key_list)
    print (usage) 

if __name__ == "__main__":
    main(sys.argv[1:])
