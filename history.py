#!/usr/bin/env python3

import sys, getopt
import plumb
import pdb
import os
import pprint
import datetime

def main(argv):
    verbose = False
    test = False
    printyear = ""
    export = ""
    save = False
    try:
        opts, args = getopt.getopt(argv, "se:p:hvt", ["help", "verbose", "test", "notes=", "look", "update", "print=", "initialize", "allocation", "export=", "save"])
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
        elif o in ("-e", "--export"):
            export = a
        elif o in ("-s", "--save"):
            save = True
        elif o in ("-p", "--print"):
            if (a[0] == '-'):
                if ("verbose" in a):
                    verbose = True
                printyear = str(datetime.datetime.now().year)
            else:
                printyear = a.lower()
        else:
            assert False, "unhandled option"
    defaults, types = plumb.GetDefaults(False)
    if defaults['folder name'] is None:
        print ("\tWarning, the folder name is missing, please correct")
        exit()
    if defaults['test root'] is None:
        print ("\tWarning, the test root path is not set, please correct")
        exit()
    if (test):
        testResult, testPrint = plumb.TestHistory(verbose)
        print (testPrint)
        exit()
    if (printyear > ""):
        printResult = plumb.PrintAIM(printyear, verbose)
        if (printResult > ""):
            pprint.pprint(printResult)
        else:
            print ("failed.")
        exit()
    if (export > ""):
        exportResult = plumb.Export(export, "", verbose)
        print (exportResult)
        exit()
    if (save):
        saveResult = plumb.Archive(verbose)
        if (saveResult):
             print ("updated.")
        else:
            print ("failed.")
        exit()
    usage()

def usage():
    usage = """
    ********************
    **  History Tool  **
    ********************

    -h --help           prints this help
    -v --verbose        increases the information level
    -t --test           runs test routine to check calculations

    -p --print          print out the AIM actitivy (in HTML table format)
                            (--print=all, --print=2018)

    -e --export         export "activity", "archive", or "portfolio"
                            to a spreadsheet
    -s --save           saves the current AIM activity to an archive dbase
                            (do this to move over your old AIM activity)
                            (warning, this will clear out the AIM dbase) 
    """
    print (usage) 

if __name__ == "__main__":
  main(sys.argv[1:])
