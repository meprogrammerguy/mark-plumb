#!/usr/bin/env python3

import sys, getopt
import pdb
import os
import subprocess
from pathlib import Path
import ast
import stat

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
        if os.name == 'nt':
            bothResult = CreateShortcutWindows("both", verbose)
        else:
            bothResult = CreateShortcutLinux("both", verbose)
        if (bothResult):
             print ("shortcuts created.")
        else:
            print ("failed.")
        exit()
    if (favorites):
        if os.name == 'nt':
            favoritesResult = CreateShortcutWindows("favorites", verbose)
        else:
            favoritesResult = CreateShortcutLinux("favorites", verbose)
        if (favoritesResult):
             print ("shortcut created.")
        else:
            print ("failed.")
        exit()
    if (desktop):
        if os.name == 'nt':
            desktopResult = CreateShortcutWindows("desktop", verbose)
        else:
            desktopResult = CreateShortcutLinux("desktop", verbose)
        if (desktopResult):
             print ("shortcut created.")
        else:
            print ("failed.")
        exit()
    if (remove):
        if os.name == 'nt':
            removeResult = RemoveShortcutWindows(verbose)
        else:
            removeResult = RemoveShortcutLinux(verbose)
        if (removeResult):
             print ("shortcuts are gone.")
        else:
            print ("failed.")
        exit()
    usage()

def CreateShortcutLinux(what, verbose):
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
        filename = "{0}PlumbMark.desktop".format(path)
        fh = open(filename, 'w', newline='')
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
    if (what == "both" or what == "desktop"):
        filename = "{0}PlumbMark.desktop".format(desktop_path)
        st = os.stat(filename)
        os.chmod(filename, st.st_mode | stat.S_IEXEC)
    if (verbose):
        print ("***\n")
    return True

def RemoveShortcutLinux(verbose):
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

def CreateShortcutWindows(what, verbose):
    if (verbose):
        print ("***")
        print ("CreateShortcuts(1) where: {0}".format(what))
    home = str(Path.home())
    current_dir = os.getcwd()
    icondir = "{0}/static/favicon.ico".format(current_dir)
    target = "{0}\AppData\Local\Programs\Python\Python36\Scripts\pipenv.exe".format(home)
    if (what == "both"):
        createWindowsShortcut("PlumbMark.lnk", target=target, wDir=current_dir, icon=icondir, args='run start_server.bat', folder='Desktop')
        createStartMenuShortcut("PlumbMark.lnk", target=target, wDir=current_dir, icon=icondir, args='run start_server.bat')
    elif (what == "favorites"):
        createStartMenuShortcut("PlumbMark.lnk", target=target, wDir=current_dir, icon=icondir, args='run start_server.bat')
    elif (what == "desktop"):
        createWindowsShortcut("PlumbMark.lnk", target=target, wDir=current_dir, icon=icondir, args='run start_server.bat', folder='Desktop')
    else:
        if (verbose):
            print ("CreateShortcuts(2) - unknown shortcut option - exiting.")
        return False
    if (verbose):
        print ("***\n")
    return True

def RemoveShortcutWindows(verbose):
    removeWindowsShortcut("PlumbMark.lnk", folder='Desktop')
    removeStartMenuShortcut("PlumbMark.lnk")
    return True

def usage():
    usage = """
    *****************************
    **  Create Shortcuts Tool  **
    *****************************

    -h --help           prints this help
    -v --verbose        increases the information level

    -d --desktop        creates a desktop shortcut
    -f --favorites      creates a shortcut in your favorites/start menu folder
    -b --both           creates both shortcuts

    -r --remove         removes the shortcuts
    """
    print (usage) 

def pathToWindowsShortcut(filename, folder='Desktop'):
    try:
        from win32com.client import Dispatch
        shell = Dispatch('WScript.Shell')
        desktop = shell.SpecialFolders(folder)
        return os.path.join(desktop, filename)
    except Error as e:
        print("pathToWindowsShortcut(1) {0}".format(e))
        return ''
  
def createWindowsShortcut(filename, target='', wDir='', icon='', args='', folder='Desktop'):
    try:
        from win32com.client import Dispatch
        shell = Dispatch('WScript.Shell')
        desktop = shell.SpecialFolders(folder)
        path = os.path.join(desktop, filename)
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = wDir
        shortcut.Arguments = args
        if icon != '':
            shortcut.IconLocation = icon
        shortcut.save()
    except Error as e:
        print("createWindowsShortcut(1) {0}".format(e))
  
def removeWindowsShortcut(filename, folder='Desktop'):
    path = pathToWindowsShortcut(filename, folder)
    if os.path.isfile(path) and os.access(path, os.W_OK):
        try:
            os.remove(path)
        except Error as e:
            print("removeWindowsShortcut(1) {0}".format(e))
  
def pathToStartMenuShortcut(filename):
    try:
        from win32com.shell import shell, shellcon
        from win32com.client import Dispatch
        shell_ = Dispatch('WScript.Shell')
        csidl = getattr(shellcon, 'CSIDL_PROGRAMS')
        startmenu = shell.SHGetSpecialFolderPath(0, csidl, False)
        return os.path.join(startmenu, filename)
    except Error as e:
        print("pathToStartMenuShortcut(1) {0}".format(e))
        return ''
  
def createStartMenuShortcut(filename, target='', wDir='', icon='', args=''):
    try:
        from win32com.shell import shell, shellcon
        from win32com.client import Dispatch
        shell_ = Dispatch('WScript.Shell')
        csidl = getattr(shellcon, 'CSIDL_PROGRAMS')
        startmenu = shell.SHGetSpecialFolderPath(0, csidl, False)
        path = os.path.join(startmenu, filename)
        shortcut = shell_.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = wDir
        shortcut.Arguments = args
        if icon != '':
            shortcut.IconLocation = icon
        shortcut.save()
    except Error as e:
        print("createStartMenuShortcut(1) {0}".format(e))
  
def removeStartMenuShortcut(filename):
    path = pathToStartMenuShortcut(filename)
    if os.path.isfile(path) and os.access(path, os.W_OK):
        try:
            os.remove(path)
        except Error as e:
            print("removeStartMenuShortcut(1) {0}".format(e))
        return

if __name__ == "__main__":
    main(sys.argv[1:])
