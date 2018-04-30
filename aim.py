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
    try:
        opts, args = getopt.getopt(argv, "a::hvt:", ["help", "verbose", "test=", "aim="])
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
        else:
            assert False, "unhandled option"
    if (test > ""):
        testResult = plumb.TestAIM(test, verbose)
        if (testResult):
            print ("Test result - pass")
        else:
            print ("Test result - fail")
        exit()
    if (aim > ""):
        aimResult = plumb.AIM(aim, verbose)
        if (aimResult):
            print ("updated.")
        else:
            print ("failed.")
        exit()
    defaults = plumb.GetDefaults(verbose)
    if defaults['aim_dbase'] is None:
        print ("\tWarning, please use --aim switch to set the AIM database name")
        exit()
    usage()

def usage():
    usage = """
    ****************
    **  AIM Tool  **
    ****************

    -h --help           Prints this help
    -v --verbose        Increases the information level
    -t --test           runs test routine to check calculations
    -a --aim            save the database name
    """
    print (usage) 

if __name__ == "__main__":
  main(sys.argv[1:])
