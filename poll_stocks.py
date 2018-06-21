#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import getpass
import pdb

import plumb

def do_something(verbose):
    start = True
    log = {}
    log['status'] = "start"
    log['pid'] = os.getpid()
    log['working directory'] = os.getcwd()
    log['username'] = getpass.getuser()
    log['script'] = os.path.basename(__file__)[:-3]
    plumb.LogDaemon(log, verbose)
    plumb.Holiday(verbose)
    while True:
        defaults, types = plumb.GetDefaults(verbose)
        dm = 0
        if (defaults['poll minutes'] is None):
            dm = 10
        else:
            dm = defaults['poll minutes']
        df = ""
        if (defaults['folder name'] is None):
            log['status'] = 'error'
            log['content'] = "folder name is missing in defaults, cannot continue"
            plumb.LogDaemon(log, verbose)
            break
        else:
            df = plumb.GetDB(False)
        log['poll minutes'] = dm
        log['dbase name'] = df
        if plumb.DayisOpen(False) and (not plumb.DayisClosed(False)):
            log['open'] = defaults['open']
            log['final poll'] = time.ctime()
            log['status'] = 'wake'
            plumb.LogDaemon(log, False)
            result, resultError, exceptionError = price_poll(verbose)
            if not result:
                if resultError > "":
                    log['status'] = 'error'
                    log['content'] = resultError
                    plumb.LogDaemon(log, verbose)
                if exceptionError > "":
                    log['status'] = 'exception'
                    log['content'] = exceptionError
                    plumb.LogDaemon(log, verbose)
            else:
                log['status'] = 'success'
                plumb.LogDaemon(log, verbose)
        else:
            log['status'] = 'closed'
            plumb.LogDaemon(log, verbose)
        log['status'] = 'sleep'
        plumb.LogDaemon(log, verbose)
        time.sleep(dm * 60)

def run():
    do_something(True)

def price_poll(verbose):
    try:
        result, resultError = plumb.Update(verbose)
        if not result:
            return False, resultError, ""
    except Exception as e:
        return False, "", e
    return True, "", ""

if __name__ == "__main__":
    run()

