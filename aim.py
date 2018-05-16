#!/usr/bin/env python3

import sys, getopt
import plumb
import pdb
import os
import pprint
import datetime

def main(argv):
    verbose = False
    test = ""
    aim = ""
    initialize = False
    notes = ""
    look = False
    update = False
    printyear = ""
    try:
        opts, args = getopt.getopt(argv, "ip:lun:hvt:", ["help", "verbose", "test=", "notes=", "look", "update", "print=", "initialize"])
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
        elif o in ("-n", "--notes"):
            notes = a
        elif o in ("-i", "--initialize"):
            initialize = True
        elif o in ("-l", "--look"):
            look = True
        elif o in ("-u", "--update"):
            update = True
        elif o in ("-p", "--print"):
            if (a[0] == '-'):
                if ("verbose" in a):
                    verbose = True
                printyear = str(datetime.datetime.now().year)
            else:
                printyear = a.lower()
        else:
            assert False, "unhandled option"
    if (test_dir > ""):
        testResult = plumb.Directory(test_dir, verbose)
        if (testResult):
            print ("updated.")
        else:
            print ("failed.")
        exit()
    defaults = plumb.GetDefaults(False)
    if defaults['aim db'] is None:
        print ("\tWarning, the AIM database name is missing, please correct")
        exit()
    if defaults['test root'] is None:
        print ("\tWarning, the test root path is not set, please correct")
        exit()
    if (test > ""):
        testResult = plumb.TestAIM(test, verbose)
        if (testResult):
            print ("Test result - pass")
        else:
            print ("Test result - fail")
        exit()
    if (notes > ""):
        notesResult = plumb.GetAIMNotes(int(notes), verbose)
        print (notesResult)
        exit()
    if (initialize):
        nowResult, nowError = plumb.AIMDate(verbose)
        if (nowResult):
             print ("updated.")
        else:
            print ("failed. {0}".format(nowError))
        exit()
    if (look):
        lookResult, lookHTML, lookDB = plumb.Look(verbose)
        pprint.pprint(lookResult)
        pprint.pprint(lookHTML)
        pprint.pprint(lookDB)
        exit()
    if (update):
        postResult = plumb.Post(verbose)
        if (postResult):
             print ("updated.")
        else:
            print ("failed.")
        exit()
    if (printyear > ""):
        printResult = plumb.PrintAIM(printyear, verbose)
        if (printResult > ""):
            pprint.pprint(printResult)
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
    -t --test           runs test routine to check calculations

    -i --initialize     initialize your AIM database
                            (warning, this will clear out the db)

    -l --look           looks at today's AIM position
    -u --update         update today's AIM position to database

    -p --print          print out the AIM database (in HTML table format)
                            (--print=all, --print=2018)

    -n --notes          show the last <count> of notes  
    """
    print (usage) 

if __name__ == "__main__":
  main(sys.argv[1:])
