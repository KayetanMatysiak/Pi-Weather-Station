import hashlib
import os

import requests
from PIL import Image, ImageFont, ImageDraw
from datetime import timedelta, datetime
from typing import Optional, Dict, Any, List

import epd7in5b_V2
from calendar_service import CalendarService
from config import load_config
from news_service import NewsService

# Constants
WIDTH = 800
HEIGHT = 480
FONT_PATH_TAHOMA = 'fonts/tahomabd.ttf'
FONT_PATH_METEOCONS = 'fonts/meteocons.ttf'
OWM_URL = 'https://api.openweathermap.org/data/3.0/onecall'
OWM_URL_GEOCODING = 'http://api.openweathermap.org/geo/1.0/reverse'
DISPLAY_STATE_FILE = '.display_state'


class WeatherStation:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize display images, fonts, drawing contexts and services."""
        self.config = config if config is not None else load_config()
        self.calendar_service = CalendarService(self.config)
        self.news_service = NewsService(self.config)
        self.calendar_lines: List[str] = []
        self.news_lines: List[str] = []
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

        # Optional overrides, so that no location or API key has to be edited
        # inside the code (see config.example.json).
        for key in ('lat', 'lon', 'appid', 'units'):
            value = self.config.get('weather', {}).get(key)
            if value:
                self.weather_parameters[key] = value

    @property
    def panels_enabled(self) -> bool:
        """True when at least one optional information panel is active."""
        return self.calendar_service.enabled or self.news_service.enabled

    def fetch_extras(self) -> None:
        """Collect calendar and news lines; failures degrade to empty panels."""
        self.calendar_lines = self.calendar_service.get_lines()
        self.news_lines = self.news_service.get_lines()

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
        # With the optional panels enabled the bottom half of the screen is
        # used for the agenda and the headlines, so only one forecast row fits.
        NUM_FORECASTS = 6 if self.panels_enabled else 12
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

    def draw_panels(self) -> None:
        """Draw the optional calendar and news panels in the bottom half."""
        if not self.panels_enabled:
            return

        panel_font = ImageFont.truetype(FONT_PATH_TAHOMA, 20, encoding='unic')
        title_font = ImageFont.truetype(FONT_PATH_TAHOMA, 24, encoding='unic')

        panel_top = HEIGHT // 2
        self.draw_black.line((0, panel_top, WIDTH, panel_top), fill=0)

        panels = []
        if self.calendar_service.enabled:
            panels.append(('AGENDA', self.calendar_lines or ['No upcoming events']))
        if self.news_service.enabled:
            panels.append(('LOCAL NEWS', self.news_lines or ['No headlines available']))

        panel_width = WIDTH // len(panels)
        for index, (title, lines) in enumerate(panels):
            x = index * panel_width + 10
            if index:
                self.draw_black.line((index * panel_width, panel_top, index * panel_width, HEIGHT), fill=0)
            self.draw_red.text((x, panel_top + 8), title, font=title_font)
            y = panel_top + 44
            for line in lines:
                if y + 24 > HEIGHT:
                    break
                self.draw_black.text((x, y), line, font=panel_font)
                y += 24

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

    def content_changed(self, state_file: str = DISPLAY_STATE_FILE) -> bool:
        """Return True when the rendered content differs from the last refresh.

        E-ink refreshes are slow and wear the panel, so an unchanged image is
        not pushed again.
        """
        digest = hashlib.sha256(
            self.black_image.tobytes() + self.red_image.tobytes()).hexdigest()
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r', encoding='utf-8') as state:
                    if state.read().strip() == digest:
                        return False
            with open(state_file, 'w', encoding='utf-8') as state:
                state.write(digest)
        except OSError as error:
            print(f"Could not read/write {state_file}: {error}")
        return True

    def push_to_display(self) -> None:
        if not self.content_changed():
            print("Display content unchanged, skipping refresh.")
            return
        epd = epd7in5b_V2.EPD()
        epd.init()
        epd.Clear()
        epd.display(epd.getbuffer(self.black_image), epd.getbuffer(self.red_image))

if __name__ == "__main__":
    forecast = WeatherStation()
    forecast.owm_weather()
    forecast.city_name()
    forecast.current_time()
    forecast.fetch_extras()
    forecast.draw_hourly_forecast_grids()
    forecast.draw_panels()
    forecast.display_image()
    # forecast.push_to_display()