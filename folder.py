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
    dollars = ""
    add = ""
    remove = ""
    symbol = ""
    balance = ""
    shares = ""
    printout = False
    get = False
    crypto = False
    try:
        opts, args = getopt.getopt(argv, 'cgpub:n:s:a:r:d:hvt', ['help', 'verbose', 'test', 'crypto', 'dollars=', 'add=', 'remove=', 'symbol=', 'balance=', 'number=', 'update', 'print', 'get'])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-t", "--test"):
            test = True
        elif o in ("-g", "--get"):
            get = True
        elif o in ("-c", "--crypto"):
            crypto = True
        elif o in ("-u", "--update"):
            update = True
        elif o in ("-p", "--print"):
            printout = True
        elif o in ("-h", "--help"):
            usage()
            exit()
        elif o in ("-a", "--add"):
            add = a.upper()
        elif o in ("-d", "--dollars"):
            dollars = a
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
        testResult = plumb.TestFolder(False, verbose)
        print(testResult)
        exit()
    defaults, types = plumb.GetDefaults(verbose)
    if defaults['folder name'] is None:
        print ("\tWarning, the database name is not set, please correct this")
        exit()
    if (dollars > ""):
        cashResult = plumb.Balance("$", 0, dollars, verbose)
        if (cashResult):
            print ("balance updated.")
        else:
            print ("failed.")
        exit()
    if (add > "" and not crypto):
        addResult = plumb.Add(add, "", verbose)
        if (addResult):
            print ("added.")
        else:
            print ("failed.")
        exit()
    if (add > "" and crypto):
        addResult = plumb.Add(add, "coinbase", verbose)
        if (addResult):
            print ("added.")
        else:
            print ("failed.")
        exit()
    if (remove > "" and not crypto):
        removeResult = plumb.Remove(remove, "", verbose)
        if (removeResult):
            print ("removed.")
        else:
            print ("failed.")
        exit()
    if (remove > "" and crypto):
        removeResult = plumb.Remove(remove, "coinbase", verbose)
        if (removeResult):
            print ("removed.")
        else:
            print ("failed.")
        exit()
    if (balance > "" and not crypto):
        if (symbol == ""):
            print ("\tWarning, to update the balance you also need a --symbol switch")
            exit()
        balanceResult = plumb.Balance(symbol, 0, balance, verbose)
        if (balanceResult['status']):
            print ("stock symbol: {0}, balance: {1}, new shares: {2}".format(symbol, balanceResult['balance'], balanceResult['shares']))
        else:
            print ("failed.")
        exit()
    if (balance > "" and crypto):
        if (symbol == ""):
            print ("\tWarning, to update the balance you also need a --symbol switch")
            exit()
        balanceResult = plumb.Balance(symbol, 1, balance, verbose)
        if (balanceResult['status']):
            print ("crypto symbol: {0}, balance: {1}, new shares: {2}".format(symbol, balanceResult['balance'], balanceResult['shares']))
        else:
            print ("failed.")
        exit()
    if (shares > "" and not crypto):
        if (symbol == ""):
            print ("\tWarning, to update the shares you also need a --symbol switch")
            exit()
        sharesResult = plumb.Shares(symbol, 0, shares, verbose)
        if (sharesResult['status']):
            print ("stock symbol: {0}, shares: {1}, new balance: {2}".format(symbol, sharesResult['shares'], sharesResult['balance']))
        else:
            print ("failed.")
        exit()
    if (shares > "" and crypto):
        if (symbol == ""):
            print ("\tWarning, to update the shares you also need a --symbol switch")
            exit()
        sharesResult = plumb.Shares(symbol, 1, shares, verbose)
        if (sharesResult['status']):
            print ("crypto symbol: {0}, shares: {1}, new balance: {2}".format(symbol, sharesResult['shares'], sharesResult['balance']))
        else:
            print ("failed.")
        exit()
    if (update):
        updateResult, updateError = plumb.Update(True, verbose)
        if (updateResult):
            print ("prices updated.")
        else:
            print ("failed. Error: {0}".format(updateError))
        exit()
    if (printout):
        printResult, symbol_options, balance_options, amount_options = plumb.PrintFolder(verbose)
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
        if (amount_options is not None):
            pprint.pprint(amount_options)
        else:
            print ("failed.")
        exit()
    if (get):
        getResult = plumb.GetFolder(verbose)
        pprint.pprint(getResult)
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
    -c --crypto         crypto-coin flag (initially is set to False)

    -d --dollars        enter your cash balance in dollars

    -a --add            add company by ticker symbol (use --crypto flag, or not)
    -r --remove         remove company by ticker symbol (use --crypto flag, or not)

    -s --symbol         ticker symbol (used with --number or --balance or --crypto)
    -n --number         number of shares owned (used with --symbol, --crypto)
    -b --balance        balance in dollars (used with --symbol, --crypto)

    -u --update         update all prices (to within default interval minutes)
    -p --print          print out the folder database (in HTML table format)
    -g --get            Get/Show current folder
    """
    print (usage) 

if __name__ == "__main__":
  main(sys.argv[1:])
