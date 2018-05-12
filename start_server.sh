# starts the scoreboard web page server
#
# remember to run pipenv shell first
#
if [ ! -n "${PIPENV_ACTIVE+1}" ]; then
    if [ -f "Pipfile" ] ; then
        echo "********************************************"
        echo "***                                      ***"
        echo "*** warning: pipenv shell is not active  ***"
        echo "*** issue 'pipenv shell' and then re-run ***"
        echo "***                                      ***"
        echo "********************************************"
        exit
    fi
fi
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_APP=scoreboard.py
flask run
