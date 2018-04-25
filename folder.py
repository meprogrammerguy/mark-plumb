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
    try:
        opts, args = getopt.getopt(argv, "d:hvt", ["help", "verbose", "test", "dbase="])
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
        else:
            assert False, "unhandled option"
    if (test):
        testResult = plumb.TestFolder(verbose)
        if (testResult):
            print ("Test result - pass")
        else:
            print ("Test result - fail")
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
    """
    print (usage) 

if __name__ == "__main__":
  main(sys.argv[1:])
