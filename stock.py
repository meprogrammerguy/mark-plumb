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
    savekey = ""
    interval = 15
    update_interval = False
    daemon = 1200
    update_daemon = False
    begin = ""
    end = ""
    try:
        opts, args = getopt.getopt(argv, "b:e:s:i:k:q:hvtc:", ["help", "verbose", "test", "quote=", "key=", "company=", "interval=", "seconds=", "begin=", "end="])
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
        elif o in ("-s", "--seconds"):
            if (a.isnumeric()):
                daemon = int(a)
                if (daemon > 1200):
                    daemon = 1200
                if (daemon < 60):
                    daemon = 60
                update_daemon = True
            else:
                daemon = 1200
        elif o in ("-d", "--directory"):
            test_dir_ = a
        elif o in ("-q", "--quote"):
            quote = a.upper()
        elif o in ("-c", "--company"):
            company = a.upper()
        elif o in ("-k", "--key"):
            savekey = a.upper()
        elif o in ("-b", "--begin"):
            begin = a
            result, begin = timecheck(begin)
            if (not result):
                result, begin = timecheck("8:30AM")
        elif o in ("-e", "--end"):
            end = a
            result, end = timecheck(end)
            if (not result):
                result, end = timecheck("03:00PM")
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
        saveResult = plumb.Key(savekey, verbose)
        if (saveResult):
            print ("saved.")
        else:
            print ("failed.")
        exit()
    if (begin > ""):
        beginResult = plumb.Begin(begin, verbose)
        if (beginResult):
            print ("saved.")
        else:
            print ("failed.")
        exit()
    if (end > ""):
        endResult = plumb.End(end, verbose)
        if (endResult):
            print ("saved.")
        else:
            print ("failed.")
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

def timecheck(theTime):
    timeformat = "%H:%M%p"
    try:
        validtime = datetime.datetime.strptime(theTime, timeformat)
        return True, validtime
    except ValueError:
        return False, "bad"

def usage():
    usage = """
    ******************
    **  Stock Tool  **
    ******************

    -h --help           prints this help
    -v --verbose        increases the information level
    -t --test           tests the stock routines
    -c --company        retrieves company data from ticker symbol
    -q --quote          get stock quote from ticker symbol
    -k --key            saves the stock page API key
    -i --interval       saves the time interval (default is 15 minutes)
    -s --seconds        saves the daemon seconds (default is 1200)
    -b --begin          saves the beginning bell time (defaults to 8:30AM)
    -e --end            saves the ending bell time (defaults to 3:00PM)
    """
    print (usage) 

if __name__ == "__main__":
  main(sys.argv[1:])
