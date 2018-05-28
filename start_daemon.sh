# starts the folder daemon
#
cd $HOME/git/mark-plumb/
if [ ! -n "${PIPENV_ACTIVE+1}" ]; then
    if [ -f "Pipfile" ] ; then
        activate_file=$(pipenv --venv)/bin/activate
        if [ -e "$activate_file" ]; then
            . $activate_file
        fi
    fi
fi
./folder_daemon.py
