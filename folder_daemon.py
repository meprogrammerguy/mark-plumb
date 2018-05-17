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
    log = {}
    log['status'] = "start"
    log['pid'] = os.getpid()
    log['working directory'] = os.getcwd()
    log['username'] = getpass.getuser()
    log['script'] = os.path.basename(__file__)[:-3]
    filename = "/tmp/{0}_{1}.txt".format(log['username'], log['script'])
    log['filename'] = filename
    plumb.LogDaemon(log, False)
    while True:
        defaults, types = plumb.GetDefaults(False)
        ds = 0
        if (defaults['daemon seconds'] is None):
            ds = 600        # 20 minutes (1200 seconds)
        else:
            ds = defaults['daemon seconds']
        df = ""
        if (defaults['folder db'] is None):
            df = 'folder.db'
        else:
            df = defaults['folder db']
        log['poll seconds'] = ds
        log['dbase name'] = df
        begin = defaults['open']
        if (begin is None):
            begin = "08:30"
        end = defaults['close']
        if (end is None):
            end = "16:00"
        weekno = datetime.today().weekday()
        ct = datetime.now().time()
        if "AM" in begin or "PM" in begin:
            bt = datetime.strptime(begin, '%I:%M%p').time()
        else:
            bt = datetime.strptime(begin, '%H:%M').time()
        if "AM" in end or "PM" in end:
            et = datetime.strptime(end, '%I:%M%p')
        else:
            et = datetime.strptime(end, '%H:%M')
        log['open'] = bt.strftime('%I:%M%p')
        log['close'] = et.strftime('%I:%M%p')
        et = et + timedelta(minutes = (ds * 2)/60) # a few final polls to get closing prices
        et = et.time()
        log['final poll'] = et.strftime('%I:%M%p')
        if weekno < 5 and ct > bt and ct < et:
            try:
                log['status'] = 'wake'
                plumb.LogDaemon(log, False)
                result, resultError = plumb.Update(False)
                if not result:
                    log['status'] = 'error'
                    plumb.LogDaemon(log, False)
                    with open(filename, "a") as f:
                        f.write("pid: {0}, error: {1}, continuing".format(log['pid'], resultError))
            except Exception as e:
                log['status'] = 'exception'
                plumb.LogDaemon(log, False)
                with open(filename, "a") as f:
                    f.write("pid: {0}, exception: {1}, continuing".format(log['pid'], e))
            log['status'] = 'success'
            plumb.LogDaemon(log, False)
            with open(filename, "w") as f:
                f.write("pid: {0}, {1} updated on: {2}. (sleeping for {3} seconds)".format(log['pid'], df, time.ctime(), ds))
        else:
            log['status'] = 'closed'
            plumb.LogDaemon(log, False)
            with open(filename, "w") as f:
                f.write("pid: {0}, now: {1}, open: {2}, close: {3}".format(log['pid'], time.ctime(), bt, et))
        log['status'] = 'sleep'
        plumb.LogDaemon(log, False)
        time.sleep(ds)

def run():
    with daemon.DaemonContext(working_directory=os.getcwd()):
        do_something()

if __name__ == "__main__":
    run()

