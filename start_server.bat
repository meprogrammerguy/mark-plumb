rem starts the plumb mark web server
rem create a shortcut like so:
rem pipenv run start_server.bat
rem
set FLASK_ENV=development
set FLASK_DEBUG=1
set FLASK_APP=scoreboard.py
flask run

