#!/usr/bin/env python3

import sys, getopt
import plumb
import pdb
import os
import pprint

def main(argv):
    verbose = False
    test = False
    dbase = "folder.db"
    cash = ""
    try:
        opts, args = getopt.getopt(argv, "d:c:hvt", ["help", "verbose", "test", "dbase=", "cash="])
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
        elif o in ("-d", "--dbase"):
            dbase = a
        elif o in ("-c", "--cash"):
            cash = a
        else:
            assert False, "unhandled option"
    if (test):
        testResult = plumb.TestFolder(verbose)
        if (testResult):
            print ("Test result - pass")
        else:
            print ("Test result - fail")
        exit()
    if (cash > ""):
        cashResult = plumb.Cash(cash, dbase, verbose)
        if (cashResult):
            print ("balance updated.")
        else:
            print ("failed.")
        exit()
    print ("\tdbase: {0}".format(dbase))
    usage()

def usage():
    usage = """
    *******************
    **  Folder Tool  **
    *******************

    -h --help           Prints this help
    -v --verbose        Increases the information level
    -t --test           tests the folder routines
    -d --dbase          override database name (folder.db is the default)
    -c --cash           enter your cash balance in dollars
    -a --add            add company by ticker symbol
    -r --remove         remove company by ticker symbol
    -s --symbol         ticker symbol (used with --number or --balance)
    -n --number         number of shared owned (used with --symbol)
    -b --balance        balance in dollars (used with --symbol)
    """
    print (usage) 

if __name__ == "__main__":
  main(sys.argv[1:])
