#!/usr/bin/env python3

import sys, getopt
import plumb
import pdb
import os
import pprint
import datetime
import subprocess
import ast

def main(argv):
    verbose = False
    test = False
    both = False
    desktop = False
    favorites = False
    remove = False
    try:
        opts, args = getopt.getopt(argv, "rdbfhvt", ["help", "verbose", "test", "both", "desktop", "favorites", "remove"])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-t", "--test"):
            test = True
        elif o in ("-b", "--both"):
            both = True
        elif o in ("-d", "--desktop"):
            desktop = True
        elif o in ("-f", "--favorites"):
            favorites = True
        elif o in ("-r", "--remove"):
            remove = True
        else:
            assert False, "unhandled option"
    if (test):
        testResult = plumb.TestShortcuts(verbose)
        print (testResult['output'])
        exit()
    if (both):
        bothResult = plumb.CreateShortcuts("both", verbose)
        if (bothResult):
             print ("updated.")
        else:
            print ("failed.")
        exit()
    if (favorites):
        favoritesResult = plumb.CreateShortcuts("favorites", verbose)
        if (favoritesResult):
             print ("updated.")
        else:
            print ("failed.")
        exit()
    if (desktop):
        desktopResult = plumb.CreateShortcuts("desktop", verbose)
        if (desktopResult):
             print ("updated.")
        else:
            print ("failed.")
        exit()
    if (remove):
        removeResult = plumb.RemoveShortcuts(verbose)
        if (removeResult):
             print ("shortcuts are gone.")
        else:
            print ("failed.")
        exit()
    usage()

def usage():
    usage = """
    *****************************
    **  Create Shortcuts Tool  **
    *****************************

    -h --help           prints this help
    -v --verbose        increases the information level
    -t --test           runs test routine to check calculations

    -b --both           creates a desktop and a favorites shortcut
    -f --favorites      creates a shortcut in your favorites
    -d --desktop        creates a desktop shortcut

    -r --remove         removes the shortcuts
    """
    print (usage) 

if __name__ == "__main__":
    main(sys.argv[1:])
