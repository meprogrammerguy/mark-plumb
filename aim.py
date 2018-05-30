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
    allo = False
    export = ""
    save = False
    try:
        opts, args = getopt.getopt(argv, "se:ailun:hvt:", ["help", "verbose", "test=", "notes=", "look", "update", "initialize", "allocation", "export=", "save"])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-a", "--allocation"):
            allo = True
        elif o in ("-t", "--test"):
            test = a
        elif o in ("-h", "--help"):
            usage()
            exit()
        elif o in ("-n", "--notes"):
            notes = a
        elif o in ("-e", "--export"):
            export = a
        elif o in ("-i", "--initialize"):
            initialize = True
        elif o in ("-l", "--look"):
            look = True
        elif o in ("-s", "--save"):
            save = True
        elif o in ("-u", "--update"):
            update = True
        else:
            assert False, "unhandled option"
    defaults, types = plumb.GetDefaults(False)
    if defaults['folder name'] is None:
        print ("\tWarning, the folder name is missing, please correct")
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
        notesResult, initialize_day = plumb.GetAIMNotes(int(notes), verbose)
        print (notesResult)
        if initialize_day:
            print("AIM system was initialized today")
        exit()
    if (initialize):
        nowResult, log = plumb.CreateAIM(verbose)
        print (nowResult, log)
        exit()
    if (look):
        lookResult, lookHTML, lookDB = plumb.Look(verbose)
        pprint.pprint(lookResult)
        pprint.pprint(lookHTML)
        pprint.pprint(lookDB)
        print (pushed)
        exit()
    if (update):
        postResult = plumb.Post(verbose)
        if (postResult):
             print ("updated.")
        else:
            print ("failed.")
        exit()
    if (allo):
        allocation_list, trending_list, life_list = plumb.AllocationTrends(verbose)
        pprint.pprint(allocation_list)
        pprint.pprint(trending_list)
        pprint.pprint(life_list)
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
    ****************
    **  AIM Tool  **
    ****************

    -h --help           prints this help
    -v --verbose        increases the information level
    -t --test           runs test routine to check calculations

    -i --initialize     initialize your AIM database
                        (after an archive you can run this to start over)      

    -l --look           looks at today's AIM position
    -u --update         update today's AIM position to database

    -n --notes          show the last <count> of notes
    -a --allocation     show allocation and trends in your portfolio
 
    -e --export         export "activity", "archive", or "portfolio"
                            to a spreadsheet
    -s --save           saves the current AIM activity to an archive dbase
                            (do this to move over your old AIM activity)
                            (warning, this will clear out the AIM dbase) 
    """
    print (usage) 

if __name__ == "__main__":
  main(sys.argv[1:])
