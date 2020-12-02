#!/usr/bin/env bash

trap "exit" INT TERM ERR
trap "kill 0" EXIT

sudo service bluetooth restart 
python3 BLEHeartRateLogger.py &
python3 plot.py &

wait
