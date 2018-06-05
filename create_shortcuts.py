#!/usr/bin/env python3

import sys, getopt
import pdb
import os
import pprint
import datetime
import subprocess
from pathlib import Path
import ast
from shutil import copyfile

def main(argv):
    verbose = False
    both = False
    desktop = False
    favorites = False
    remove = False
    try:
        opts, args = getopt.getopt(argv, "rdbfhv", ["help", "verbose", "both", "desktop", "favorites", "remove"])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-t", "--test"):
            test = True
        elif o in ("-b", "--both"):
            both = True
        elif o in ("-d", "--desktop"):
            desktop = True
        elif o in ("-f", "--favorites"):
            favorites = True
        elif o in ("-r", "--remove"):
            remove = True
        else:
            assert False, "unhandled option"
    if (both):
        bothResult = CreateShortcuts("both", verbose)
        if (bothResult):
             print ("updated.")
        else:
            print ("failed.")
        exit()
    if (favorites):
        favoritesResult = CreateShortcuts("favorites", verbose)
        if (favoritesResult):
             print ("updated.")
        else:
            print ("failed.")
        exit()
    if (desktop):
        desktopResult = CreateShortcuts("desktop", verbose)
        if (desktopResult):
             print ("updated.")
        else:
            print ("failed.")
        exit()
    if (remove):
        removeResult = RemoveShortcuts(verbose)
        if (removeResult):
             print ("shortcuts are gone.")
        else:
            print ("failed.")
        exit()
    usage()

def CreateShortcuts(what, verbose):
    if (verbose):
        print ("***")
        print ("CreateShortcuts(1) where: {0}".format(what))
    home = str(Path.home())
    desktop_path = "{0}/Desktop/".format(home)
    favorites_path = "{0}/.local/share/applications/".format(home)
    paths = []
    f_apps = []
    if (what == "both"):
        paths.append(favorites_path)
        paths.append(desktop_path)
        f_apps =  get_favorites()
    elif (what == "favorites"):
        paths.append(favorites_path)
        f_apps = get_favorites()
    elif (what == "desktop"):
        paths.append(desktop_path)
    else:
        if (verbose):
            print ("CreateShortcuts(2) - unknown shortcut option - exiting.")
        return False
    current_dir = os.getcwd()
    heading = "[Desktop Entry]\n"
    shortcut_dict = {}
    shortcut_dict['Version'] = 1.0
    shortcut_dict['Type'] = "Application"
    shortcut_dict['Terminal'] = "true"
    shortcut_dict['Exec'] = "{0}/start_server.sh".format(current_dir)
    shortcut_dict['Name'] = "PlumbMark"
    shortcut_dict['Comment'] = "Plumb the Market Server"
    shortcut_dict['Icon'] = "{0}/static/Shortcut.png".format(current_dir)
    shortcut_dict['GenericName[en_US.UTF-8]'] = "Server for Plumb the Market Page"
    for path in paths:
        full_filename = "{0}PlumbMark.desktop".format(path)
        fh = open(full_filename, 'w', newline='')
        fh.write(heading)
        for k,v in shortcut_dict.items():
            item = "{0} = {1}\n".format(k, v)
            fh.write(item)
        fh.close()
    if f_apps != []:
        if ("PlumbMark.desktop" not in f_apps):
            f_apps.append("PlumbMark.desktop")
            f_apps_set = 'gsettings set org.gnome.shell favorite-apps "{0}"'.format(f_apps)
            os.system(f_apps_set)
    if (verbose):
        print ("***\n")
    return True

def RemoveShortcuts(verbose):
    home = str(Path.home())
    desktop = "{0}/Desktop/PlumbMark.desktop".format(home)
    favorites = "{0}/.local/share/applications/PlumbMark.desktop".format(home)
    f_apps = get_favorites()
    if (os.path.exists(desktop)):
        os.unlink(desktop)
    if (os.path.exists(favorites)):
        os.unlink(favorites)
    if f_apps != []:
        if ("PlumbMark.desktop" in f_apps):
            f_apps.remove("PlumbMark.desktop")
            f_apps_set = 'gsettings set org.gnome.shell favorite-apps "{0}"'.format(f_apps)
            os.system(f_apps_set)
    return True

def get_favorites():
    child = subprocess.Popen(['gsettings', 'get', 'org.gnome.shell', 'favorite-apps'], stdout=subprocess.PIPE, shell=False)
    response = child.communicate()[0].decode("utf-8")
    return ast.literal_eval(response)

def usage():
    usage = """
    *****************************
    **  Create Shortcuts Tool  **
    *****************************

    -h --help           prints this help
    -v --verbose        increases the information level

    -d --desktop        creates a desktop shortcut
    -b --both           creates a desktop and a favorites shortcut
    -f --favorites      creates a shortcut in your favorites

    -r --remove         removes the shortcuts
    """
    print (usage) 

if __name__ == "__main__":
    main(sys.argv[1:])
