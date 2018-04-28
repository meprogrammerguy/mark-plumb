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
        if (defaults['aim_folder'] is None):
            plumb.Update("folder.db", False)
        else:
            plumb.Update(defaults['aim_folder'], False)
        with open("/tmp/folder_daemon.txt", "w") as f:
            f.write("pid: {0}, {1} updated on: {2} for user: {3}. (sleeping for {4} seconds)".format(os.getpid(), defaults['aim_folder'], time.ctime(), getpass.getuser(), defaults['daemon_seconds']))
        if (defaults['daemon_seconds'] is None):
            time.sleep(1200)        # 20 minutes (1200 seconds)
        else:
            time.sleep(defaults['daemon_seconds'])

def run():
    with daemon.DaemonContext(working_directory=os.getcwd()):
        do_something()

if __name__ == "__main__":
    run()

