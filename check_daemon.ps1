# script to check if daemon is running
echo "*****************\n"
echo "folder_daemon PID"
tasklist /fi "imagename eq folder_daemon.py"
echo "\n*****************\n"
