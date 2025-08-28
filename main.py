import requests
from PIL import Image, ImageFont, ImageDraw
from datetime import timedelta, datetime
from typing import Optional, Dict, Any

import epd7in5b_V2

# Constants
WIDTH = 800
HEIGHT = 480
FONT_PATH_TAHOMA = 'fonts/tahomabd.ttf'
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

    @staticmethod
    def degrees_to_cardinal(d: int) -> str:
        """Converts wind direction from degrees to a cardinal direction string."""
        dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        ix = round(d / (360. / len(dirs)))
        return dirs[ix % len(dirs)]

    def draw_hourly_forecast_grids(self):
        """Draws the two rows of hourly forecasts, maximizing the forecast display."""
        if not self.weather or not self.current_time_one_hour:
            return

        # --- Layout Constants (Adjusted for Maximized Display) ---
        NUM_FORECASTS = 12  # Display 12 hours
        COLUMNS_PER_ROW = 6
        COLUMN_WIDTH = WIDTH // COLUMNS_PER_ROW  # Dynamic column width
        START_X = 0  # Start from the left edge

        # Adjusted Y positions to use available height
        ROW_HEIGHT = HEIGHT // 2
        Y_POS = {
            'time': [10, HEIGHT // 2 + 10],
            'icon': [60, HEIGHT // 2 + 60],
            'temp': [120, HEIGHT // 2 + 120],
            'details': [170, HEIGHT // 2 + 170],
            'wind': [210, HEIGHT // 2 + 210]
        }

        # --- Font Sizes (Adjusted for Maximized Display) ---
        time_font_size = 36
        icon_font_size = 65  # Reduced icon font size
        temp_font_size = 34
        details_font_size = 22
        wind_font_size = 14  # Smaller wind direction font

        time_grid = ImageFont.truetype(FONT_PATH_TAHOMA, time_font_size, encoding='unic')
        small_weather_icons = ImageFont.truetype(FONT_PATH_METEOCONS, icon_font_size, encoding='unic')
        temp_grid = ImageFont.truetype(FONT_PATH_TAHOMA, temp_font_size, encoding='unic')
        details_font = ImageFont.truetype(FONT_PATH_TAHOMA, details_font_size, encoding='unic')
        wind_font = ImageFont.truetype(FONT_PATH_TAHOMA, wind_font_size, encoding='unic')

        time_pointer = self.now

        for i in range(NUM_FORECASTS):
            row_index = i // COLUMNS_PER_ROW
            col_index = i % COLUMNS_PER_ROW
            column_center_x = START_X + (col_index * COLUMN_WIDTH) + (COLUMN_WIDTH / 2)
            hour_data = self.weather["hourly"][i + 1]

            # --- 1. Draw Time ---
            time_text = f'{time_pointer.strftime("%H")}:00'
            time_bbox = self.draw_black.textbbox((0, 0), time_text, font=time_grid)
            time_x = column_center_x - ((time_bbox[2] - time_bbox[0]) / 2)
            self.draw_black.text((time_x, Y_POS['time'][row_index]), time_text, font=time_grid)

            # --- 2. Draw Weather Icon ---
            icon_char = self.search_for_forecast_icons(hour_data["weather"][0]["icon"])
            icon_bbox = self.draw_red.textbbox((0, 0), icon_char, font=small_weather_icons)
            icon_x = column_center_x - ((icon_bbox[2] - icon_bbox[0]) / 2)
            self.draw_red.text((icon_x, Y_POS['icon'][row_index]), icon_char, font=small_weather_icons)

            # --- 3. Draw Temperature ---
            temp_text = f'{round(hour_data["temp"])}°C'
            temp_bbox = self.draw_black.textbbox((0, 0), temp_text, font=temp_grid)
            temp_x = column_center_x - ((time_bbox[2] - time_bbox[0]) / 2)
            self.draw_black.text((time_x, Y_POS['temp'][row_index]), temp_text, font=temp_grid)

            # --- 4. Draw Details (Humidity & Feels Like) ---
            details_text = f"{hour_data['humidity']}% | {round(hour_data['feels_like'])}°"
            details_bbox = self.draw_black.textbbox((0, 0), details_text, font=details_font)
            details_x = column_center_x - ((details_bbox[2] - details_bbox[0]) / 2)
            self.draw_black.text((details_x, Y_POS['details'][row_index]), details_text, font=details_font)

            # --- 5. Draw Wind Info ---
            wind_speed_kmh = round(hour_data['wind_speed'] * 3.6)  # Convert m/s to km/h
            wind_direction = self.degrees_to_cardinal(hour_data['wind_deg'])

            # Split wind info into speed and direction
            wind_speed_text = f"{wind_speed_kmh} km/h "
            wind_direction_text = f"{wind_direction}"

            wind_speed_bbox = self.draw_black.textbbox((0, 0), wind_speed_text, font=details_font)
            wind_direction_bbox = self.draw_red.textbbox((0, 0), wind_direction_text, font=wind_font)

            # Calculate total width for centering
            total_wind_width = wind_speed_bbox[2] - wind_speed_bbox[0] + wind_direction_bbox[2] - wind_direction_bbox[0]
            wind_x = column_center_x - (total_wind_width / 2)

            # Draw wind speed in black
            self.draw_black.text((wind_x, Y_POS['wind'][row_index]), wind_speed_text, font=details_font)

            # Draw wind direction in red, after the speed
            self.draw_red.text((wind_x + (wind_speed_bbox[2] - wind_speed_bbox[0]), Y_POS['wind'][row_index]), wind_direction_text, font=wind_font)

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
        epd = epd7in5b_V2.EPD()
        epd.init()
        epd.Clear()
        epd.display(epd.getbuffer(self.black_image), epd.getbuffer(self.red_image))

if __name__ == "__main__":
    forecast = WeatherStation()
    forecast.owm_weather()
    forecast.city_name()
    forecast.current_time()
    forecast.draw_hourly_forecast_grids()
    forecast.display_image()
    # forecast.push_to_display()