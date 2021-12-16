#!/usr/bin/env python3

import sys, getopt
import plumb
import pdb
import os
import pprint

def main(argv):
    verbose = False
    test = False
    info = False
    quote = False
    symbol = ""
    try:
        opts, args = getopt.getopt(argv, 'hvtiq:s', ['help', 'verbose', 'test', 'info', 'quote', 'symbol='])
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
        elif o in ("-i", "--info"):
            info = True
        elif o in ("-q", "--quote"):
            quote = True
        elif o in ("-s", "--symbol"):
            symbol = a.upper()
        else:
            assert False, "unhandled option"
    if (test):
        testResult = plumb.TestCrypto(verbose)
        print(testResult)
        exit()
    if (info):
        if (symbol == ""):
            print ("\tWarning, to get the company info you also need a --symbol switch")
            exit()
        infoResult = plumb.CryptoCompany(symbol, verbose)
        pprint.pprint(infoResult)
        exit()
    if (quote):
        if (symbol == ""):
            print ("\tWarning, to get the crypto quotes you also need a --symbol switch")
            exit()
        quoteResult = plumb.QuoteCrypto(symbol, verbose)
        pprint.pprint(quoteResult)
        exit()
    usage()

def usage():
    usage = """
    *******************
    **  Crypto Tool  **
    *******************

    -h --help           prints this help
    -v --verbose        increases the information level
    -t --test           tests the crypto routines

    -s --symbol         ticker symbol (used with --info or --quote)

    -i --info           show company info by ticker symbol (used with --symbol)
    -q --quote          show company quotes by ticker symbol (used with --symbol)
    """

    print (usage) 

if __name__ == "__main__":
  main(sys.argv[1:])
