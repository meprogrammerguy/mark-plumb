#!/usr/bin/env python3

import sys, getopt
import plumb
import pdb
import os
import pprint

def main(argv):
    verbose = False
    test = ""
    aim = ""
    test_dir = ""
    cash = ""
    stock = ""
    now = False
    look = False
    post = False
    try:
        opts, args = getopt.getopt(argv, "lpc:s:nd:a::hvt:", ["help", "verbose", "test=", "aim=", "directory=", "now", "cash=", "stock=", "look", "post"])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-t", "--test"):
            test = a
        elif o in ("-h", "--help"):
            usage()
            exit()
        elif o in ("-a", "--aim"):
            aim = a
        elif o in ("-d", "--directory"):
            test_dir = a
        elif o in ("-c", "--cash"):
            cash = a
        elif o in ("-s", "--stock"):
            stock = a
        elif o in ("-n", "--now"):
            now = True
        elif o in ("-l", "--look"):
            look = True
        elif o in ("-p", "--post"):
            post = True
        else:
            assert False, "unhandled option"
    if (test_dir > ""):
        testResult = plumb.Directory(test_dir, verbose)
        if (testResult):
            print ("updated.")
        else:
            print ("failed.")
        exit()
    if (aim > ""):
        aimResult = plumb.AIM(aim, verbose)
        if (aimResult):
            print ("updated.")
        else:
            print ("failed.")
        exit()
    defaults = plumb.GetDefaults(False)
    if defaults['aim_dbase'] is None:
        print ("\tWarning, please use --aim switch to set the AIM database name")
        exit()
    if defaults['test_directory'] is None:
        print ("\tWarning, please use --directory switch to set the test directory")
        exit()
    if (test > ""):
        testResult = plumb.TestAIM(test, verbose)
        if (testResult):
            print ("Test result - pass")
        else:
            print ("Test result - fail")
        exit()
    if (cash > ""):
        cashResult = plumb.AIMCash(float(cash), verbose)
        if (cashResult):
            print ("updated.")
        else:
            print ("failed.")
        exit()
    if (stock > ""):
        stockResult = plumb.AIMStock(float(stock), verbose)
        if (stockResult):
            print ("updated.")
        else:
            print ("failed.")
        exit()
    if (now):
        nowResult, nowError = plumb.AIMDate(verbose)
        if (nowResult):
             print ("updated.")
        else:
            print ("failed. {0}".format(nowError))
        exit()
    if (look):
        lookResult = plumb.Look(verbose)
        print (lookResult)
        exit()
    if (post):
        postResult = plumb.Post(verbose)
        if (postResult):
             print ("updated.")
        else:
            print ("failed.")
        exit()
    usage()

def usage():
    usage = """
    ****************
    **  AIM Tool  **
    ****************

    -h --help           prints this help
    -v --verbose        increases the information level
    -a --aim            save the database name

    -d --directory      save the test directory (default is test)
    -t --test           runs test routine to check calculations

    -c --cash           save starting cash
    -b --balance        save starting stock value
    -n --now            begin tracking AIM now
                            (warning, this will clear out the db)

    -l --look           looks at today's AIM position
    -p --post           posts today's AIM position to database
    """
    print (usage) 

if __name__ == "__main__":
  main(sys.argv[1:])
