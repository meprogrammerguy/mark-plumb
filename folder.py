#!/usr/bin/env python3

import sys, getopt
import plumb
import pdb
import os
import pprint

def main(argv):
    verbose = False
    test = False
    update = False
    folder = ""
    cash = ""
    add = ""
    remove = ""
    symbol = ""
    balance = ""
    shares = ""
    printout = False
    try:
        opts, args = getopt.getopt(argv, "pub:n:s:a:r:f:c:hvt", ["help", "verbose", "test", "folder=", "cash=", "add=", "remove=", "symbol=", "balance=", "number=", "update", "print"])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-t", "--test"):
            test = True
        elif o in ("-u", "--update"):
            update = True
        elif o in ("-p", "--print"):
            printout = True
        elif o in ("-h", "--help"):
            usage()
            exit()
        elif o in ("-f", "--folder"):
            folder = a
        elif o in ("-a", "--add"):
            add = a.upper()
        elif o in ("-c", "--cash"):
            cash = a
        elif o in ("-r", "--remove"):
            remove = a.upper()
        elif o in ("-s", "--symbol"):
            symbol = a.upper()
        elif o in ("-b", "--balance"):
            balance = a
        elif o in ("-n", "--number"):
            shares = a
        else:
            assert False, "unhandled option"
    if (test):
        testResult = plumb.TestFolder(verbose)
        if (testResult):
            print ("Test result - pass")
        else:
            print ("Test result - fail")
        exit()
    if (folder > ""):
        folderResult = plumb.Folder(folder, verbose)
        if (folderResult):
            print ("updated.")
        else:
            print ("failed.")
        exit()
    defaults = plumb.GetDefaults(verbose)
    if defaults['folder db'] is None:
        print ("\tWarning, please use --folder switch to set the folder database name")
        exit()
    if (cash > ""):
        cashResult = plumb.Cash(cash, verbose)
        if (cashResult):
            print ("balance updated.")
        else:
            print ("failed.")
        exit()
    if (add > ""):
        addResult = plumb.Add(add, verbose)
        if (addResult):
            print ("added.")
        else:
            print ("failed.")
        exit()
    if (remove > ""):
        removeResult = plumb.Remove(remove, verbose)
        if (removeResult):
            print ("removed.")
        else:
            print ("failed.")
        exit()
    if (balance > ""):
        if (symbol == ""):
            print ("\tWarning, to update the balance you also need a --symbol switch")
            exit()
        balanceResult = plumb.Balance(symbol, balance, verbose)
        if (balanceResult['status']):
            print ("symbol: {0}, current shares: {1}".format(symbol, balanceResult['shares']))
        else:
            print ("failed.")
        exit()
    if (shares > ""):
        if (symbol == ""):
            print ("\tWarning, to update the shares you also need a --symbol switch")
            exit()
        sharesResult = plumb.Shares(symbol, shares, verbose)
        if (sharesResult['status']):
            print ("symbol: {0}, current balance: {1}".format(symbol, sharesResult['balance']))
        else:
            print ("failed.")
        exit()
    if (update):
        updateResult, updateError = plumb.Update(verbose)
        if (updateResult):
            print ("prices updated.")
        else:
            print ("failed. Error: {0}".format(updateError))
        exit()
    if (printout):
        printResult, symbol_options, balance_options = plumb.PrintFolder(verbose)
        if (printResult > ""):
            pprint.pprint(printResult)
        else:
            print ("failed.")
        if (symbol_options > ""):
            pprint.pprint(symbol_options)
        else:
            print ("failed.")
        if (balance_options > ""):
            pprint.pprint(balance_options)
        else:
            print ("failed.")
        exit()
    usage()

def usage():
    usage = """
    *******************
    **  Folder Tool  **
    *******************

    -h --help           prints this help
    -v --verbose        increases the information level
    -t --test           tests the folder routines
    -f --folder         save database name
    -c --cash           enter your cash balance in dollars
    -a --add            add company by ticker symbol
    -r --remove         remove company by ticker symbol
    -s --symbol         ticker symbol (used with --number or --balance)
    -n --number         number of shares owned (used with --symbol)
    -b --balance        balance in dollars (used with --symbol)
    -u --update         update all prices (to within default interval minutes)
    -p --print          print out the folder database (in HTML table format)
    """
    print (usage) 

if __name__ == "__main__":
  main(sys.argv[1:])
