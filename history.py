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
    archive = False
    delete = ""
    try:
        opts, args = getopt.getopt(argv, "d:ase:p:hvt", ["help", "verbose", "test", "notes=", "look", "update", "print=", "initialize", "allocation", "export=", "save", "archive", "delete="])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-t", "--test"):
            test = True
        elif o in ("-a", "--archive"):
            archive = True
        elif o in ("-h", "--help"):
            usage()
            exit()
        elif o in ("-e", "--export"):
            export = a
        elif o in ("-d", "--delete"):
            delete = a
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
        testResult = plumb.TestHistory(False, verbose)
        print (testResult)
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
    if (delete > ""):
        deleteResult = plumb.DeleteSnapshot(delete, verbose)
        if (deleteResult):
            print ("deleted.")
        else:
            print ("failed.")
        exit()
    if (save):
        saveResult = plumb.Archive(verbose)
        if (saveResult):
             print ("updated.")
        else:
            print ("failed.")
        exit()
    if (archive):
        archiveResult = plumb.PrintSummary(verbose)
        if (archiveResult > ""):
            pprint.pprint(archiveResult)
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

    -p --print          print out the AIM activity (in HTML table format)
                            (--print=all, --print=2018)
    -a --archive        prints out the archive (in HTML table format)

    -e --export         export "activity", "archive", "portfolio",
                            or "worksheet" to a spreadsheet
    -s --save           saves the current AIM activity to an archive dbase
                            (do this to move over your old AIM activity)
                            (warning, this will clear out the AIM dbase)
    -d --delete         delete archive by snapshot number 
    """
    print (usage) 

if __name__ == "__main__":
  main(sys.argv[1:])
