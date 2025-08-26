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

        self.big_weather_icon = ImageFont.truetype(FONT_PATH_METEOCONS, 80, encoding='unic')
        self.big_temp = ImageFont.truetype(FONT_PATH_TAHOMA, 80, encoding='unic')
        self.location_font = ImageFont.truetype(FONT_PATH_TAHOMA, 30, encoding='unic')
        self.refreshed_font = ImageFont.truetype(FONT_PATH_TAHOMA, 20, encoding='unic')
        self.small_weather_icons = ImageFont.truetype(FONT_PATH_METEOCONS, 70, encoding='unic')
        self.time_grid = ImageFont.truetype(FONT_PATH_TAHOMA, 30, encoding='unic')
        self.temp_grid = ImageFont.truetype(FONT_PATH_TAHOMA, 30, encoding='unic')
        self.details_font = ImageFont.truetype(FONT_PATH_TAHOMA, 22, encoding='unic')

        self.weather: Optional[Dict[str, Any]] = None
        self.geocode_location: Optional[Dict[str, Any]] = None
        self.now: Optional[datetime] = None
        self.current_time_one_hour: Optional[datetime] = None

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

    # NEW: Helper function to convert wind degrees to a cardinal direction.
    @staticmethod
    def degrees_to_cardinal(d: int) -> str:
        """Converts wind direction from degrees to a cardinal direction string."""
        dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        # Each direction covers 45 degrees. We find which segment the degree falls into.
        ix = round(d / (360. / len(dirs)))
        return dirs[ix % len(dirs)]

    def current_weather(self) -> None:
        """Draw current weather icon and temperature."""
        if not self.weather:
            return

        small_weather_icon_font = ImageFont.truetype(FONT_PATH_METEOCONS, 30, encoding='unic')
        small_temp_font = ImageFont.truetype(FONT_PATH_TAHOMA, 25, encoding='unic')
        icon_code = self.weather["current"]["weather"][0]["icon"]
        icon = self.search_for_forecast_icons(icon_code)
        vertical_offset = 10
        self.draw_black.text((10, vertical_offset), text=icon, font=small_weather_icon_font)
        temp = round(self.weather["hourly"][0]["temp"])
        temp_feels_like = round(self.weather["hourly"][0]["feels_like"])
        self.draw_black.text((45, vertical_offset), text=f'{temp}°C / ({temp_feels_like}°C)', font=small_temp_font)

    def location_name(self) -> None:
        """Draw location name."""
        if not self.geocode_location:
            return

        small_location_font = ImageFont.truetype(FONT_PATH_TAHOMA, 18, encoding='unic')
        name = self.geocode_location[0].get("name", "")
        country = self.geocode_location[0].get("country", "")
        vertical_offset = 55
        location_text = f'{name}, {country}'
        self.draw_black.text((10, vertical_offset), text=location_text, font=small_location_font)

    def refresh_time_string(self) -> None:
        """Draw refresh time."""
        if not self.now:
            return

        small_refreshed_font = ImageFont.truetype(FONT_PATH_TAHOMA, 14, encoding='unic')
        refresh_text = f'Refreshed at {self.now.strftime("%H:%M")}'
        self.draw_black.text((10, 40), text=refresh_text, font=small_refreshed_font)

    # MODIFIED: This function is updated with new Y-positions and logic to draw wind info.
    def draw_hourly_forecast_grids(self):
        """
        Draw the two rows of hourly forecasts, centering all elements within each column.
        """
        if not self.weather or not self.current_time_one_hour:
            return

        # --- Layout Constants ---
        NUM_FORECASTS = 13
        COLUMNS_PER_ROW = 6
        COLUMN_WIDTH = 130
        START_X = 15

        # MODIFIED: Y positions are adjusted to make space for the new wind line.
        Y_POS = {
            'time': [85, 285],
            'icon': [115, 315],
            'temp': [190, 390],
            'details': [220, 420],
            'wind': [245, 445]  # New Y-position for wind info
        }

        time_pointer = self.current_time_one_hour

        for i in range(NUM_FORECASTS):
            row_index = i // (COLUMNS_PER_ROW + 1)
            col_index = i % (COLUMNS_PER_ROW + 1) if row_index == 0 else i - (COLUMNS_PER_ROW + 1)
            column_center_x = START_X + (col_index * COLUMN_WIDTH) + (COLUMN_WIDTH / 2)
            hour_data = self.weather["hourly"][i + 1]

            # --- 1. Draw Time ---
            time_text = f'{time_pointer.strftime("%H")}:00'
            time_bbox = self.draw_black.textbbox((0, 0), time_text, font=self.time_grid)
            time_x = column_center_x - ((time_bbox[2] - time_bbox[0]) / 2)
            self.draw_black.text((time_x, Y_POS['time'][row_index]), time_text, font=self.time_grid)

            # --- 2. Draw Weather Icon ---
            icon_char = self.search_for_forecast_icons(hour_data["weather"][0]["icon"])
            icon_bbox = self.draw_red.textbbox((0, 0), icon_char, font=self.small_weather_icons)
            icon_x = column_center_x - ((icon_bbox[2] - icon_bbox[0]) / 2)
            self.draw_red.text((icon_x, Y_POS['icon'][row_index]), icon_char, font=self.small_weather_icons)

            # --- 3. Draw Temperature ---
            temp_text = f'{round(hour_data["temp"])}°C'
            temp_bbox = self.draw_black.textbbox((0, 0), temp_text, font=self.temp_grid)
            temp_x = column_center_x - ((temp_bbox[2] - temp_bbox[0]) / 2)
            self.draw_black.text((temp_x, Y_POS['temp'][row_index]), temp_text, font=self.temp_grid)

            # --- 4. Draw Details (Humidity & Feels Like) ---
            details_text = f"{hour_data['humidity']}% | {round(hour_data['feels_like'])}°"
            details_bbox = self.draw_black.textbbox((0, 0), details_text, font=self.details_font)
            details_x = column_center_x - ((details_bbox[2] - details_bbox[0]) / 2)
            self.draw_black.text((details_x, Y_POS['details'][row_index]), details_text, font=self.details_font)

            # --- 5. Draw Wind Info --- (NEW)
            wind_speed_kmh = round(hour_data['wind_speed'] * 3.6)  # Convert m/s to km/h
            wind_direction = self.degrees_to_cardinal(hour_data['wind_deg'])
            wind_text = f"{wind_speed_kmh} km/h {wind_direction}"
            wind_bbox = self.draw_black.textbbox((0, 0), wind_text, font=self.details_font)
            wind_x = column_center_x - ((wind_bbox[2] - wind_bbox[0]) / 2)
            self.draw_black.text((wind_x, Y_POS['wind'][row_index]), wind_text, font=self.details_font)

            time_pointer += timedelta(hours=1)

    def display_image(self) -> None:
        """
        Combines the black and red 1-bit images into a single RGB image
        for display and debugging purposes.
        """
        combined_image = Image.new('RGB', (WIDTH, HEIGHT), (255, 255, 255))
        black_pixels = self.black_image.load()
        red_pixels = self.red_image.load()
        combined_pixels = combined_image.load()
        for x in range(WIDTH):
            for y in range(HEIGHT):
                if red_pixels[x, y] == 0:
                    combined_pixels[x, y] = (255, 0, 0)
                elif black_pixels[x, y] == 0:
                    combined_pixels[x, y] = (0, 0, 0)
        combined_image.show()

    def push_to_display(self) -> None:
        """Push images to the e-paper display (requires epd7in5b_V2)."""
        epd = epd7in5b_V2.EPD()
        epd.init()
        epd.Clear()
        epd.display(epd.getbuffer(self.black_image), epd.getbuffer(self.red_image))

if __name__ == "__main__":
    forecast = WeatherStation()
    forecast.owm_weather()
    forecast.city_name()
    forecast.current_time()
    forecast.current_weather()
    forecast.location_name()
    forecast.refresh_time_string()
    forecast.draw_hourly_forecast_grids()
    forecast.push_to_display()
    # forecast.display_image()