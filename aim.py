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
    try:
        opts, args = getopt.getopt(argv, "d:a::hvt:", ["help", "verbose", "test=", "aim=", "directory="])
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
    defaults = plumb.GetDefaults(verbose)
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
    usage()

def usage():
    usage = """
    ****************
    **  AIM Tool  **
    ****************

    -h --help           prints this help
    -v --verbose        increases the information level
    -t --test           runs test routine to check calculations
    -a --aim            save the database name
    -d --directory      save the test directory (default is test)
    """
    print (usage) 

if __name__ == "__main__":
  main(sys.argv[1:])
