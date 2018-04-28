#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import daemon
import time
import os
import getpass

import plumb

def do_something():
    while True:
        defaults = plumb.GetDefaults(False)
        if (defaults[2] is None):
            plumb.Update("folder.db", False)
        else:
            plumb.Update(defaults[2], False)
        with open("/tmp/folder_daemon.txt", "w") as f:
            f.write("pid: {0}, {1} updated on: {2} for user: {3}. (sleeping for {4} seconds)".format(os.getpid(), defaults[2], time.ctime(), getpass.getuser(), defaults[3]))
        if (defaults[3] is None):
            time.sleep(1200)        # 20 minutes (1200 seconds)
        else:
            time.sleep(defaults[3])

def run():
    with daemon.DaemonContext(working_directory=os.getcwd()):
        do_something()

if __name__ == "__main__":
    run()

