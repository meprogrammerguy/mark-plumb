# starts the scoreboard web page server
#
if [ ! -n "${PIPENV_ACTIVE+1}" ]; then
    if [ -f "Pipfile" ] ; then
        activate_pipenv = $(pipenv --venv)/bin/activate
        if [ -e "$activate_pipenv" ]; then
            . $activate_pipenv
        fi
    fi
fi
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_APP=scoreboard.py
flask run
