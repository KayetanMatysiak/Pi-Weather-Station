import requests
from PIL import Image, ImageFont, ImageDraw
from datetime import timedelta, datetime
from typing import Optional, Dict, Any
import epd7in5b_V2

# Constants
WIDTH = 800
HEIGHT = 480
FONT_PATH_TAHOMA = 'fonts/tahoma.ttf'
FONT_PATH_METEOCONS = 'fonts/meteocons.ttf'
OWM_URL = 'https://api.openweathermap.org/data/3.0/onecall'
OWM_URL_GEOCODING = 'http://api.openweathermap.org/geo/1.0/reverse'

class WeatherStation:
    def __init__(self):
        """Initialize display images, fonts, and drawing contexts."""
        self.black_image = Image.new('1', (WIDTH, HEIGHT), 255)
        self.red_image = Image.new('1', (WIDTH, HEIGHT), 255)
        self.draw_black = ImageDraw.Draw(self.black_image)
        self.draw_red = ImageDraw.Draw(self.red_image)

        self.big_weather_icon = ImageFont.truetype(FONT_PATH_METEOCONS, 155, encoding='unic')
        self.big_temp = ImageFont.truetype(FONT_PATH_TAHOMA, 155, encoding='unic')
        self.location_font = ImageFont.truetype(FONT_PATH_TAHOMA, 30, encoding='unic')
        self.refreshed_font = ImageFont.truetype(FONT_PATH_TAHOMA, 20, encoding='unic')
        self.small_weather_icons = ImageFont.truetype(FONT_PATH_METEOCONS, 80, encoding='unic')
        self.time_grid = ImageFont.truetype(FONT_PATH_TAHOMA, 35, encoding='unic')
        self.temp_grid = ImageFont.truetype(FONT_PATH_TAHOMA, 30, encoding='unic')

        self.weather: Optional[Dict[str, Any]] = None
        self.geocode_location: Optional[Dict[str, Any]] = None
        self.now: Optional[datetime] = None
        self.current_time_one_hour: Optional[datetime] = None

        # Set your coordinates and API key here
        self.weather_parameters = {
            'lat': '36.692920',
            'lon': '-4.445090',
            'appid': '3238514ac3216a71e1ee266ad6db8fa2',
            'units': 'metric',
            'exclude': 'daily,minutely'
        }

    def owm_weather(self) -> None:
        """Fetch weather data from OpenWeatherMap."""
        try:
            r = requests.get(OWM_URL, params=self.weather_parameters, timeout=10)
            r.raise_for_status()
            self.weather = r.json()
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            self.weather = None

    def city_name(self) -> None:
        """Fetch city name using reverse geocoding."""
        try:
            geocode = requests.get(OWM_URL_GEOCODING, params=self.weather_parameters, timeout=10)
            geocode.raise_for_status()
            self.geocode_location = geocode.json()
        except Exception as e:
            print(f"Error fetching geocode data: {e}")
            self.geocode_location = None

    def current_time(self) -> None:
        """Set current time and time one hour ahead."""
        self.now = datetime.now()
        self.current_time_one_hour = self.now + timedelta(hours=1)

    @staticmethod
    def search_for_forecast_icons(code: str) -> str:
        """Map weather code to icon character."""
        icons_dict = {
            '01d': 'B', '01n': 'C', '02d': 'H', '02n': 'I', '03d': 'N', '03n': 'N',
            '04d': 'Y', '04n': 'Y', '09d': 'R', '09n': 'R', '10d': 'R', '10n': 'R',
            '11d': 'P', '11n': 'P', '13d': 'W', '13n': 'W', '50d': 'M', '50n': 'W'
        }
        return icons_dict.get(code, '?')

    def current_weather(self) -> None:
        """Draw current weather icon and temperature."""
        if not self.weather:
            return
        icon_code = self.weather["current"]["weather"][0]["icon"]
        icon = self.search_for_forecast_icons(icon_code)
        self.draw_black.text((0, 0), text=f'{icon}:', font=self.big_weather_icon)
        self.draw_black.text((620, -25), text='°C', font=self.big_temp)
        temp = round(self.weather["hourly"][0]["temp"])
        self.draw_black.text((620, 130), text=f'{temp}', font=self.big_temp, anchor='rs')

    def location_name(self) -> None:
        """Draw location name."""
        if not self.geocode_location:
            return
        name = self.geocode_location[0].get("name", "")
        country = self.geocode_location[0].get("country", "")
        self.draw_black.text((300, 50), text=f'{name}, {country}', font=self.location_font, anchor='ms')

    def refresh_time_string(self) -> None:
        """Draw refresh time."""
        if not self.now:
            return
        self.draw_black.text((220, 50), text=f'Refreshed at {self.now.strftime("%H:%M")}', font=self.refreshed_font)

    def draw_time_both_grids(self) -> None:
        """Draw time labels for both grids."""
        if not self.current_time_one_hour:
            return
        x_var_time = 20
        time_pointer = self.current_time_one_hour
        for x in range(13):
            y = 150 if x <= 5 else 320
            self.draw_black.text((x_var_time, y), text=f'{time_pointer.strftime("%H")}:00', font=self.time_grid)
            x_var_time += 135
            time_pointer += timedelta(hours=1)
            if x == 5:
                x_var_time = 20

    def draw_weather_icons_both_grids(self) -> None:
        """Draw weather icons for both grids."""
        if not self.weather:
            return
        x_var_icons = 24
        for x in range(13):
            weather_symbol = self.search_for_forecast_icons(self.weather["hourly"][x + 1]["weather"][0]["icon"])
            y = 185 if x <= 5 else 355
            self.draw_red.text((x_var_icons, y), text=weather_symbol, font=self.small_weather_icons)
            x_var_icons += 135
            if x == 5:
                x_var_icons = 24

    def draw_temperature_both_grids(self) -> None:
        """Draw temperature values for both grids."""
        if not self.weather:
            return
        x_var_temp = 28
        for x in range(13):
            temperature = round(self.weather["hourly"][x + 1]["temp"])
            y = 260 if x <= 5 else 430
            self.draw_black.text((x_var_temp, y), text=f'{temperature}°C', font=self.temp_grid)
            x_var_temp += 135
            if x == 5:
                x_var_temp = 28

    def draw_a_line(self) -> None:
        """Draw a horizontal line separating grids."""
        self.draw_red.line((5, 310, WIDTH - 5, 310), fill=0, width=3)

    def push_to_display(self) -> None:
        """Push images to the e-paper display (requires epd7in5b_V2)."""
        epd = epd7in5b_V2.EPD()
        epd.init()
        epd.Clear()
        epd.display(epd.getbuffer(self.black_image), epd.getbuffer(self.red_image))


    def display_image(self) -> None:
        """Show the black image for debugging."""
        self.black_image.show()

if __name__ == "__main__":
    forecast = WeatherStation()
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
    forecast.push_to_display()
    # forecast.display_image()