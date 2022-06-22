# Raspberry Pi Weather Station
> A simple weather station written using Python.

## Table of Contents
* [General Info](#general-information)
* [Technologies Used](#technologies-used)
* [Features](#features)
* [Screenshots](#screenshots)
* [Setup](#setup)
* [Usage](#usage)
* [Project Status](#project-status)
* [Room for Improvement](#room-for-improvement)
* [Acknowledgements](#acknowledgements)
* [Contact](#contact)
<!-- * [License](#license) -->


## General Information
- I decided to create my own weather station using Python, Raspberry Pi and Waveshare's eink 7.5inch display (red/black).<br>
- Waveshare's documentation was confusing and it was hard for me to understand how the screen works.
- I will try to explain here, step by step how to get it up and running on your Pi!


## Technologies Used
- Raspberry Pi Zero W
- Waveshare Eink Display 7.5inch e-Paper HAT (HD, red & black colour)
- Python
- XXX mAh battery
- Charger

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
![Example screenshot](./img/screenshot.png)
<!-- If you have screenshots you'd like to share, include them here. -->


## Setup
Make sure to enable GPiO by using command:<br>
>sudo raspi-config<br>
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
<a href='https://www.latlong.net/'>https://www.latlong.net/</a><br> 
You also need to provide your own API key from Openweathermap (line 38)

## Project Status
Project is: _in progress_.


## Room for Improvement
<!-- Include areas you believe need improvement / could be improved. Also add TODOs for future development.

Room for improvement:
- Improvement to be done 1
- Improvement to be done 2

To do:
- Feature to be added 1
- Feature to be added 2
 -->

## Acknowledgements
<!-- Give credit here.
- This project was inspired by...
- This project was based on [this tutorial](https://www.example.com).
- Many thanks to... -->

