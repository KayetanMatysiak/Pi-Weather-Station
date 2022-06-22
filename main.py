from PIL import Image, ImageFont, ImageDraw
from datetime import timedelta, datetime
import requests
# import epd7in5b_V2

class Weather_Station():
    def __init__(self):
        # RESOLUTION OF THE DISPLAY
        self.WIDTH = 800
        self.HEIGHT = 480

        # GENERATED IMAGES - BLACK AND RED
        self.BLACK_IMAGE = Image.new('1', (self.WIDTH, self.HEIGHT), 255)
        self.RED_IMAGE = Image.new('1', (self.WIDTH, self.HEIGHT), 255)

        # REQUIRED FONTS
        self.big_weather_icon = ImageFont.truetype('fonts/meteocons.ttf', 155, encoding='unic')
        self.big_temp = ImageFont.truetype('fonts/tahoma.ttf', 155, encoding='unic')
        self.location_font = ImageFont.truetype('fonts/tahoma.ttf', 30, encoding='unic')
        self.refreshed_font = ImageFont.truetype('fonts/tahoma.ttf', 20, encoding='unic')
        self.small_weather_icons = ImageFont.truetype('fonts/meteocons.ttf', 80, encoding='unic')
        self.time_grid = ImageFont.truetype('fonts/tahoma.ttf', 35, encoding='unic')
        self.temp_grid = ImageFont.truetype('fonts/tahoma.ttf', 30, encoding='unic')

        # GENERATE IMAGES
        self.draw_black = ImageDraw.Draw(self.BLACK_IMAGE)
        self.draw_red = ImageDraw.Draw(self.RED_IMAGE)

        self.x_var_time = 20
        self.x_var_icons = 24
        self.x_var_temp = 28

    def owm_weather(self):
        OWM_URL = 'https://api.openweathermap.org/data/2.5/onecall'
        self.weather_parameters = {
            'lat': 'XXX',
            'lon': 'XXX',
            'appid': 'XXX',
            'units': 'metric',
            'exclude': 'daily,minutely'
        }
        r = requests.get(OWM_URL, params=self.weather_parameters)
        self.weather = r.json()

    def city_name(self):
        # REVERSE GEOCODING
        OWM_URL_GEOCODING = 'http://api.openweathermap.org/geo/1.0/reverse'
        geocode = requests.get(OWM_URL_GEOCODING, params=self.weather_parameters)
        self.geocode_location = geocode.json()

    def current_time(self):
        self.now = datetime.now()
        self.current_time_one_hour = datetime.now() + timedelta(hours=1)

    def search_for_forecast_icons(self, code):
        icons_dict = {'01d': 'B', '01n': 'C', '02d': 'H', '02n': 'I', '03d': 'N', '03n': 'N', '04d': 'Y',
                      '04n': 'Y', '09d': 'R', '09n': 'R', '10d': 'R', '10n': 'R', '11d': 'P', '11n': 'P',
                      '13d': 'W', '13n': 'W', '50d': 'M', '50n': 'W'}

        if code in icons_dict:
            return (icons_dict[code])

    def current_weather(self):
        self.forecast_icon = self.draw_black.text((0, 0),
                                                  text=f'{self.search_for_forecast_icons(self.weather["current"]["weather"][0]["icon"])}:',
                                                  font=self.big_weather_icon)
        self.draw_black.text((620, -25), text='°C', font=self.big_temp)
        self.draw_black.text((620, 130), text=f'{round(self.weather["hourly"][0]["temp"])}', font=self.big_temp,
                             anchor='rs')

    def location_name(self):
        self.draw_black.text((300, 50),
                             text=f'{self.geocode_location[0]["name"]}, {self.geocode_location[0]["country"]}',
                             font=self.location_font,
                             anchor='ms')

    def refresh_time_string(self):
        self.draw_black.text((220, 50), text=f'Refreshed at {self.now.strftime("%H:%M")}', font=self.refreshed_font)

    def draw_time_both_grids(self):
        for x in range(13):
            if x <= 5:
                self.draw_black.text((self.x_var_time, 150), text=f'{self.current_time_one_hour.strftime("%H")}:00',
                                     font=self.time_grid)
                self.x_var_time += 135
                self.current_time_one_hour += timedelta(hours=1)
            elif x == 6:
                self.x_var_time = 20
            elif x >= 6:
                self.draw_black.text((self.x_var_time, 320), text=f'{self.current_time_one_hour.strftime("%H")}:00',
                                     font=self.time_grid)
                self.x_var_time += 135
                self.current_time_one_hour += timedelta(hours=1)

    def draw_weather_icons_both_grids(self):
        for x in range(13):
            weather_symbol = self.search_for_forecast_icons(self.weather["hourly"][x + 1]["weather"][0]["icon"])
            if x <= 5:
                self.draw_red.text((self.x_var_icons, 185), text=weather_symbol, font=self.small_weather_icons)
                self.x_var_icons += 135
            elif x == 6:
                self.x_var_icons = 24
            elif x >= 6:
                self.draw_red.text((self.x_var_icons, 355), text=weather_symbol, font=self.small_weather_icons)
                self.x_var_icons += 135

    def draw_temperature_both_grids(self):
        for x in range(13):
            temperature = round(self.weather["hourly"][x + 1]["temp"])
            if x <= 5:
                self.draw_black.text((self.x_var_temp, 260), text=f'{temperature}°C', font=self.temp_grid)
                self.x_var_temp += 135
            elif x == 6:
                self.x_var_temp = 28
            elif x >= 6:
                self.draw_black.text((self.x_var_temp, 430), text=f'{temperature}°C', font=self.temp_grid)
                self.x_var_temp += 135

    def draw_a_line(self):
        self.draw_red.line((5, 310, self.WIDTH - 5, 310), fill=0, width=3)

    def push_to_display(self):
        epd = epd7in5b_V2.EPD()
        epd.init()
        epd.Clear()
        epd.display(epd.getbuffer(self.BLACK_IMAGE), epd.getbuffer(self.RED_IMAGE))

    def display_image(self):
        self.BLACK_IMAGE.show()

forecast = Weather_Station()
forecast.owm_weather()
forecast.city_name()
forecast.current_time()
forecast.current_weather()
forecast.location_name()
forecast.refresh_time_string()
forecast.draw_time_both_grids()
forecast.draw_weather_icons_both_grids()
forecast.draw_temperature_both_grids()
forecast.draw_a_line()
# forecast.push_to_display()
forecast.display_image()