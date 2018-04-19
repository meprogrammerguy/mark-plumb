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
    dbase = __file__
    dbase = dbase.replace(".py", ".db")
    dbase = dbase.replace("./", "")
    try:
        opts, args = getopt.getopt(argv, "d:q:hvt", ["help", "verbose", "test", "quote=", "dbase="])
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
            quote = a
        elif o in ("-d", "--dbase"):
            dbase = a
        else:
            assert False, "unhandled option"
    if (test):
        testResult = plumb.Test(verbose)
        if (testResult):
            print ("Test result - pass")
        else:
            print ("Test result - fail")
        exit()
    if (quote > ""):
        quoteResult = plumb.Quote(quote, verbose)
        print ("Quote")
        print (dbase)
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
    -q --quote          get quote of ticker symbol
    -d --dbase          database name (stock.db is the default)          
    """
    print (usage) 

if __name__ == "__main__":
  main(sys.argv[1:])
