#!/bin/bash
#!/usr/bin/env/python
# starts the scoreboard web page server
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
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_APP=scoreboard.py
flask run
