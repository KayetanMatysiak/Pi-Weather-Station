#!/usr/bin/bash

cd /home/pi/weather_station

python3 main.py && sleep 60 && shutdown -h now
