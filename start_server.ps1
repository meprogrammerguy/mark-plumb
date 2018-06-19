# starts the scoreboard web page server
#
cd $env:userprofile/git/mark-plumb/
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_APP=scoreboard.py
flask run
