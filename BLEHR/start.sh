#!/usr/bin/env bash

trap "exit" INT TERM ERR
trap "kill 0" EXIT

sudo service bluetooth restart 
python3 BLEHeartRateLogger.py &
python3 plot5.py &
sleep 20
xdg-open "http://127.0.0.1:8050/" &

wait
