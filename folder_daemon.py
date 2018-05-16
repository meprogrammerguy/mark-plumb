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
    while True:
        defaults, types = plumb.GetDefaults(False)
        ds = 0
        if (defaults['daemon seconds'] is None):
            ds = 600        # 20 minutes (1200 seconds)
        else:
            ds = defaults['daemon seconds']
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
        et = et + timedelta(minutes = (ds * 4)/60) # a few final polls to get closing prices
        et = et.time()
        filename = "/tmp/{0}_folder_daemon.txt".format(getpass.getuser())
        errname = "/tmp/{0}_folder_daemon_error.txt".format(getpass.getuser())
        if weekno < 5 and ct > bt and ct < et:
            try:
                result, resultError = plumb.Update(False)
                if not result:
                    with open(filename, "a") as f:
                        f.write("pid: {0}, error: {1}, continuing".format(os.getpid(), resultError))
            except Exception as e:
                with open(filename, "a") as f:
                    f.write("pid: {0}, exception: {1}, continuing".format(os.getpid(), e))
            with open(filename, "w") as f:
                f.write("pid: {0}, {1} updated on: {2}. (sleeping for {3} seconds)".format(os.getpid(), defaults['folder db'], time.ctime(), defaults['daemon seconds']))
        else:
            with open(filename, "w") as f:
                f.write("pid: {0}, now: {1}, open: {2}, close: {3}".format(os.getpid(), ct, bt, et))
        time.sleep(ds)

def run():
    with daemon.DaemonContext(working_directory=os.getcwd()):
        do_something()

if __name__ == "__main__":
    run()

