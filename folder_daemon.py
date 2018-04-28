#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import daemon
import time
import os
import getpass

import plumb

def do_something():
    while True:
        plumb.Update("folder.db", False)
        with open("/tmp/folder_daemon.txt", "w") as f:
            f.write("pid: {0}, folder.db updated on: {1} for user: {2}.".format(os.getpid(), time.ctime(), getpass.getuser()))
        time.sleep(1200)        # 20 minutes (1200 seconds)

def run():
    with daemon.DaemonContext(working_directory=os.getcwd()):
        do_something()

if __name__ == "__main__":
    run()

