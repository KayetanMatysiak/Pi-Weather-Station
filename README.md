# Raspberry Pi Weather Station
> A simple weather station written using Python.

## Table of Contents
* [General Info](#general-information)
* [Technologies Used](#technologies-used)
* [Features](#features)
* [Screenshots](#screenshots)
* [Setup](#setup)
* [Usage](#usage)
* [Autostart](#autostart)
* [Room for Improvement](#room-for-improvement)
<!-- * [License](#license) -->


## General Information
- I decided to create my own weather station using Python, Raspberry Pi and Waveshare's eink 7.5inch display (red/black).<br>
- Waveshare's documentation was confusing and it was hard for me to understand how the screen works.
- I will try to explain here, step by step how to get it up and running on your Pi!
- I used this tutorial how to add battery to the Pi (<a href="https://www.youtube.com/watch?v=opYVS0EXZIg">https://www.youtube.com/watch?v=opYVS0EXZIg</a>


## Technologies Used
- Raspberry Pi Zero W
- Waveshare Eink Display 7.5inch e-Paper HAT (HD, red & black colour)
- Python
- 3.7V 1000mAh battery
- 2A Lithium Li-ion 18650 3.7V Battery Charger Module DC 5V Converter
- USB Micro board (for battery charging)

## Prerequisites
- PIL
- Requests
- Datetime
- API key for Openweathermap

## Features
- Current forecast
- Forecast for the next 12 hours
- Location
- Refresh time

## Screenshots
<img src='https://github.com/KayetanMatysiak/Pi-Weather-Station/blob/master/weather_station.jpg' width="640" height="548">


## Setup
Make sure to enable GPIO by using command:<br>
>sudo raspi-config<br>


However I strongly suggest to use Raspberry Pi Imager for the initial setup of your SD card - you can enable GPIO, SSH and configure WiFi<br>
Following the instructions from Waveshare<br>
- Install BCM2835 libraries<br>
>wget http://www.airspayce.com/mikem/bcm2835/bcm2835-1.71.tar.gz<br>
>tar zxvf bcm2835-1.71.tar.gz<br>
>cd bcm2835-1.71/<br>
>sudo ./configure && sudo make && sudo make check && sudo make install<br>

- Install WiringPi libraries<br>
>sudo apt-get install wiringpi<br>
#For Raspberry Pi systems after May 2019 (earlier than before, you may not need to execute), you may need to upgrade:<br>
>wget https://project-downloads.drogon.net/wiringpi-latest.deb<br>
>sudo dpkg -i wiringpi-latest.deb<br>
>gpio -v<br>
#Run gpio -v and version 2.52 will appear. If it does not appear, the installation is wrong<br>
#Bullseye branch system use the following command:<br>
>git clone https://github.com/WiringPi/WiringPi<br>
>cd WiringPi<br>
>./build<br>
>gpio -v<br>
#Run gpio -v and version 2.60 will appear. If it does not appear, it means that there is an installation error<br>
- Install Python3<br>
>sudo apt-get update<br>
>sudo apt-get install python3-pip<br>
>sudo apt-get install python3-pil<br>
>sudo apt-get install python3-numpy<br>
>sudo pip3 install RPi.GPIO<br>
>sudo pip3 install spidev<br>
>sudo pip3 install requests<br>

## Usage
You only need to provide latitude and longitude (lines 36 and 37), I suggest using:<br>
<a href='https://www.latlong.net/'>https://www.latlong.net/</a><br><br>
You also need to use your own API key from Openweathermap (line 38)<br><br>

Remember to unhash line 4 & 142 and hash 143. It's to import Waveshare's code, push it to the display and avoid generating image in the jpg file.

## Autostart
I tried using rc.local and crontab - for some reason the first one was causing glitches on the screen and crontab had a problem with auto shutdown.<br>
The best to accomplish the goal is to use systemd.<br><br>

In order to do that, we need to create a new service:<br>
>sudo nano /etc/systemd/system/my_script.service<br>


Paste the code below:<br>
>[Unit]<br>
>Description=My_Script Service<br>
>After=multi-user.target<br><br>

>[Service]<br>
>Type=idle<br>
>User=pi<br>
>ExecStart=/usr/bin/python3 /home/pi/weather_station/launcher.sh<br><br>

>[Install]<br>
>WantedBy=multi-user.target<br>

Change the file permissions:<br>
>sudo chmod 644 /etc/systemd/system/name-of-your-service.service<br>

Reload and enable the system:<br>
>sudo systemctl daemon-reload<br>
>sudo systemctl enable /etc/systemd/system/my_script.service<br><br>

You may also need to change the permissions for the shutdown service as well as the Python code (including fonts)!

