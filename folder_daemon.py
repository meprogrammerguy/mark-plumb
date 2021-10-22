#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import daemon
import time
import os
import getpass
import pdb

import plumb

def do_something():
    start = True
    log = {}
    log['status'] = "start"
    log['pid'] = os.getpid()
    log['working directory'] = os.getcwd()
    log['username'] = getpass.getuser()
    log['script'] = os.path.basename(__file__)[:-3]
    filename = "/tmp/{0}_{1}.txt".format(log['username'], log['script'])
    log['filename'] = filename
    plumb.LogDaemon(log, False)
    plumb.Holiday(False)
    while True:
        defaults, types = plumb.GetDefaults(False)
        dm = 0
        if (defaults['poll minutes'] is None):
            dm = 10
        else:
            dm = defaults['poll minutes']
        df = ""
        if (defaults['folder name'] is None):
            log['status'] = 'error'
            log['content'] = "folder name is missing in defaults, cannot continue"
            with open(filename, "a") as f:
                f.write("pid: {0}, error: {1}, continuing".format(log['pid'], log['content']))
            plumb.LogDaemon(log, False)
            break
        else:
            df = plumb.GetDB(False)
        log['poll minutes'] = dm
        log['dbase name'] = df
        market_open = False
        if plumb.DayisOpen(False) and (not plumb.DayisClosed(False)):
            log['open'] = defaults['open']
            log['final poll'] = time.ctime()
            log['status'] = 'wake'
            plumb.LogDaemon(log, False)
            market_open = True
        else:
            log['status'] = 'closed'
            plumb.LogDaemon(log, False)
            with open(filename, "w") as f:
                f.write("pid: {0}, now: {1}, open: {2}".format(log['pid'], time.ctime(), defaults['open']))
        log['status'] = 'sleep'
        plumb.LogDaemon(log, False)

        result, resultError, exceptionError = price_poll(market_open) # always poll because crypto is open 24/7
        if not result:
            if resultError > "":
                log['status'] = 'error'
                log['content'] = resultError
                plumb.LogDaemon(log, False)
                with open(filename, "a") as f:
                    f.write("pid: {0}, error: {1}, continuing".format(log['pid'], resultError))
            if exceptionError > "":
                log['status'] = 'exception'
                log['content'] = exceptionError
                plumb.LogDaemon(log, False)
                with open(filename, "a") as f:
                    f.write("pid: {0}, exception: {1}, continuing".format(log['pid'], exceptionError))
        else:
            log['status'] = 'success'
            plumb.LogDaemon(log, False)
            with open(filename, "w") as f:
                f.write("pid: {0}, {1} updated on: {2}. (sleeping for {3} minutes)".format(log['pid'], df, time.ctime(), dm))

        time.sleep(dm * 60)

def run():
    with daemon.DaemonContext(working_directory=os.getcwd()):
        do_something()

def price_poll(market_open):
    try:
        result, resultError = plumb.Update(market_open, False)
        if not result:
            return False, resultError, ""
    except Exception as e:
        return False, "", e
    return True, "", ""

if __name__ == "__main__":
    run()

