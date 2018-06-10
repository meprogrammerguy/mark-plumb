#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import daemon
import time
import os
import getpass
from datetime import datetime
from datetime import timedelta
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
        ds = 0
        if (defaults['poll minutes'] is None):
            ds = 10
        else:
            ds = defaults['poll minutes']
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
        log['poll seconds'] = ds
        log['dbase name'] = df
        begin = defaults['open']
        weekno = datetime.today().weekday()
        ct = datetime.now().time()
        bt = ct
        if (begin is not None):
            if "AM" in begin or "PM" in begin:
                bt = datetime.strptime(begin, '%I:%M%p').time()
            else:
                bt = datetime.strptime(begin, '%H:%M').time()
            log['open'] = bt.strftime('%I:%M%p')
            if weekno < 5 and ct > bt and (not plumb.DayisClosed(False)):
                log['final poll'] = time.ctime()
                log['status'] = 'wake'
                plumb.LogDaemon(log, False)
                result, resultError, exceptionError = price_poll()
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
                        f.write("pid: {0}, {1} updated on: {2}. (sleeping for {3} minutes)".format(log['pid'], df, time.ctime(), ds))
            else:
                log['status'] = 'closed'
                plumb.LogDaemon(log, False)
                with open(filename, "w") as f:
                    f.write("pid: {0}, now: {1}, open: {2}".format(log['pid'], time.ctime(), bt))
        else:
            log['status'] = 'closed'
            plumb.LogDaemon(log, False)
            with open(filename, "w") as f:
                f.write("pid: {0}, now: {1}, open: {2}".format(log['pid'], time.ctime(), bt))
        log['status'] = 'sleep'
        plumb.LogDaemon(log, False)
        time.sleep(ds)

def run():
    with daemon.DaemonContext(working_directory=os.getcwd()):
        do_something()

def price_poll():
    try:
        result, resultError = plumb.Update(False)
        if not result:
            return False, resultError, ""
    except Exception as e:
        return False, "", e
    return True, "", ""

if __name__ == "__main__":
    run()

