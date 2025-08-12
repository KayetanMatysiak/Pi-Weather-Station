import cairo
import io
from datetime import timedelta, datetime
import requests
# import epd7in5b_V2
from PIL import Image
import freetype

# Display settings
WIDTH = 800
HEIGHT = 480
SCALE = 2  # working at a higher resolution if desired
WORKING_WIDTH = WIDTH * SCALE
WORKING_HEIGHT = HEIGHT * SCALE

# Path to your TrueType fonts.
METEO_FONT_PATH = "fonts/meteocons.ttf"  # for weather icons
TAHOMA_FONT_PATH = "fonts/tahoma.ttf"  # for temperature, location, etc.

# Define nominal sizes (in points) for different text elements.
BIG_WEATHER_SIZE = 155
BIG_TEMP_SIZE = 130
LOCATION_SIZE = 30
REFRESH_SIZE = 20
SMALL_WEATHER_SIZE = 80
TIME_SIZE = 35
TEMP_SIZE = 30

FIRST_GRID_Y_VALUES = [170, 245, 280]
SECOND_GRID_Y_VALUES = [FIRST_GRID_Y_VALUES[0]*2, FIRST_GRID_Y_VALUES[1]*1.69, FIRST_GRID_Y_VALUES[1]*1.85]
DIVIDING_LINE = 300


class Weather_Station():
    def __init__(self):
        # Create two Cairo surfaces (black & red layers) with ARGB32.
        self.surface_black = cairo.ImageSurface(cairo.FORMAT_ARGB32, WORKING_WIDTH, WORKING_HEIGHT)
        self.surface_red = cairo.ImageSurface(cairo.FORMAT_ARGB32, WORKING_WIDTH, WORKING_HEIGHT)

        # Create contexts.
        self.ctx_black = cairo.Context(self.surface_black)
        self.ctx_red = cairo.Context(self.surface_red)

        # Fill surfaces with white.
        self.ctx_black.set_source_rgb(1, 1, 1)
        self.ctx_black.paint()
        self.ctx_red.set_source_rgb(1, 1, 1)
        self.ctx_red.paint()

        # Scale the drawing context to work in the original coordinate space.
        self.ctx_black.scale(SCALE, SCALE)
        self.ctx_red.scale(SCALE, SCALE)

        # Define X positions for grid elements.
        self.x_var_time = 20
        self.x_var_icons = 24
        self.x_var_temp = 28

    def draw_text_freetype(self, ctx, text, font_file, size, x, y):
        # ... (same as before, unchanged) ...
        face = freetype.Face(font_file)
        face.set_char_size(size * 64)

        pen_x = x
        for char in text:
            face.load_char(char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_FORCE_AUTOHINT)
            bitmap = face.glyph.bitmap
            width = bitmap.width
            rows = bitmap.rows

            top = face.glyph.bitmap_top
            left = face.glyph.bitmap_left

            if width == 0 or rows == 0:
                pen_x += face.glyph.advance.x >> 6
                continue

            stride = ((width + 3) // 4) * 4
            buffer_padded = bytearray(stride * rows)
            bitmap_buffer = bitmap.buffer
            for row in range(rows):
                start_src = row * width
                start_dst = row * stride
                buffer_padded[start_dst:start_dst + width] = bitmap_buffer[start_src:start_src + width]

            glyph_surface = cairo.ImageSurface.create_for_data(
                buffer_padded, cairo.FORMAT_A8, width, rows, stride)

            ctx.set_source_rgb(0, 0, 0)
            x_offset = pen_x + left
            y_offset = y - top

            ctx.save()
            ctx.translate(x_offset, y_offset)
            ctx.mask_surface(glyph_surface, 0, 0)
            ctx.restore()

            pen_x += face.glyph.advance.x >> 6

    def owm_weather(self):
        OWM_URL = 'https://api.openweathermap.org/data/3.0/onecall'
        self.weather_parameters = {
            'lat': '',
            'lon': '',
            'appid': '',
            'units': 'metric',
            'exclude': 'daily,minutely'
        }
        r = requests.get(OWM_URL, params=self.weather_parameters)
        self.weather = r.json()

    def city_name(self):
        OWM_URL_GEOCODING = 'http://api.openweathermap.org/geo/1.0/reverse'
        geocode = requests.get(OWM_URL_GEOCODING, params=self.weather_parameters)
        self.geocode_location = geocode.json()

    def current_time(self):
        self.now = datetime.now()
        self.current_time_one_hour = self.now + timedelta(hours=1)

    def search_for_forecast_icons(self, code):
        icons_dict = {
            '01d': 'B', '01n': 'C',
            '02d': 'H', '02n': 'I',
            '03d': 'N', '03n': 'N',
            '04d': 'Y', '04n': 'Y',
            '09d': 'R', '09n': 'R',
            '10d': 'R', '10n': 'R',
            '11d': 'P', '11n': 'P',
            '13d': 'W', '13n': 'W',
            '50d': 'M', '50n': 'W'
        }
        return icons_dict.get(code, '?')

    def current_weather(self):
        icon_code = self.weather["current"]["weather"][0]["icon"]
        icon_char = self.search_for_forecast_icons(icon_code)
        self.draw_text_freetype(self.ctx_black, f'{icon_char}:', METEO_FONT_PATH, BIG_WEATHER_SIZE, 0, 125)

        temp_value = round(self.weather["hourly"][0]["temp"])
        self.draw_text_freetype(self.ctx_black, f'{temp_value}°C', TAHOMA_FONT_PATH, BIG_TEMP_SIZE, 500, 110)

    def location_name(self):
        location_str = f'{self.geocode_location[0]["name"]}, {self.geocode_location[0]["country"]}'
        self.draw_text_freetype(self.ctx_black, location_str, TAHOMA_FONT_PATH, LOCATION_SIZE, 250, 50)

    def refresh_time_string(self):
        refresh_str = f'Actualizado a las {self.now.strftime("%H:%M")}'
        self.draw_text_freetype(self.ctx_black, refresh_str, TAHOMA_FONT_PATH, REFRESH_SIZE, 220, 70)

    def draw_time_both_grids(self):
        x_time = self.x_var_time
        t = self.current_time_one_hour
        for i in range(6):
            time_str = f'{t.strftime("%H")}:00'
            self.draw_text_freetype(self.ctx_black, time_str, TAHOMA_FONT_PATH, TIME_SIZE, x_time, FIRST_GRID_Y_VALUES[0])
            x_time += 135
            t += timedelta(hours=1)

        x_time = self.x_var_time
        for i in range(6, 13):
            time_str = f'{t.strftime("%H")}:00'
            self.draw_text_freetype(self.ctx_black, time_str, TAHOMA_FONT_PATH, TIME_SIZE, x_time, SECOND_GRID_Y_VALUES[0])
            x_time += 135
            t += timedelta(hours=1)

    def draw_weather_icons_both_grids(self):
        x_icon = self.x_var_icons
        for i in range(6):
            weather_symbol = self.search_for_forecast_icons(self.weather["hourly"][i + 1]["weather"][0]["icon"])
            self.draw_text_freetype(self.ctx_red, weather_symbol, METEO_FONT_PATH, SMALL_WEATHER_SIZE, x_icon, FIRST_GRID_Y_VALUES[1])
            x_icon += 135

        x_icon = self.x_var_icons
        for i in range(6, 13):
            weather_symbol = self.search_for_forecast_icons(self.weather["hourly"][i + 1]["weather"][0]["icon"])
            self.draw_text_freetype(self.ctx_red, weather_symbol, METEO_FONT_PATH, SMALL_WEATHER_SIZE, x_icon, SECOND_GRID_Y_VALUES[1])
            x_icon += 135

    def draw_temperature_both_grids(self):
        x_temp = self.x_var_temp
        for i in range(6):
            temp_value = round(self.weather["hourly"][i + 1]["temp"])
            self.draw_text_freetype(self.ctx_black, f'{temp_value}°C', TAHOMA_FONT_PATH, TEMP_SIZE, x_temp, FIRST_GRID_Y_VALUES[2])
            x_temp += 135

        x_temp = self.x_var_temp
        for i in range(6, 13):
            temp_value = round(self.weather["hourly"][i + 1]["temp"])
            self.draw_text_freetype(self.ctx_black, f'{temp_value}°C', TAHOMA_FONT_PATH, TEMP_SIZE, x_temp, SECOND_GRID_Y_VALUES[2])
            x_temp += 135

    def draw_a_line(self):
        self.ctx_red.set_source_rgb(0, 0, 0)
        self.ctx_red.set_line_width(3)
        self.ctx_red.move_to(5, DIVIDING_LINE)
        self.ctx_red.line_to(WIDTH - 5, DIVIDING_LINE)
        self.ctx_red.stroke()

    def push_to_display(self):
        output_black = io.BytesIO()
        output_red = io.BytesIO()
        self.surface_black.write_to_png(output_black)
        self.surface_red.write_to_png(output_red)

        output_black.seek(0)
        output_red.seek(0)

        img_black = Image.open(output_black)
        img_red = Image.open(output_red)

        final_black = img_black.convert('1')
        final_red = img_red.convert('1')

        epd = epd7in5b_V2.EPD()
        epd.init()
        epd.Clear()
        epd.display(epd.getbuffer(final_black), epd.getbuffer(final_red))

    def display_image(self):
        """
        Combine the black and red surfaces into one RGB image and display it.
        This function converts the already rendered black and red layers (mode "1")
        into masks to composite an image with white background, black text, and
        red highlights.
        """
        # Write Cairo surfaces to in‑memory PNG files.
        output_black = io.BytesIO()
        output_red = io.BytesIO()
        self.surface_black.write_to_png(output_black)
        self.surface_red.write_to_png(output_red)
        output_black.seek(0)
        output_red.seek(0)

        # Open with Pillow.
        img_black = Image.open(output_black).convert("1")
        img_red = Image.open(output_red).convert("1")

        # Create a new RGB image with white background.
        composite = Image.new("RGB", img_black.size, (255, 255, 255))

        # Prepare color images for black and red. Here we fill an image with the desired color.
        black_layer = Image.new("RGB", img_black.size, (0, 0, 0))
        red_layer = Image.new("RGB", img_red.size, (255, 0, 0))

        # Create masks from the one-bit images.
        # In our "1" images, the foreground (drawing) is black (pixel value 0)
        # and the background is white (pixel value 255). We invert them so that
        # we can use them as masks: areas where the text exists should be opaque.
        mask_black = img_black.convert("L").point(lambda p: 255 - p)
        mask_red = img_red.convert("L").point(lambda p: 255 - p)

        # Composite the black and red layers onto the white background.
        # First paste the black elements.
        composite.paste(black_layer, mask=mask_black)
        # Then paste the red elements (which will appear over or alongside
        # the black as needed).
        composite.paste(red_layer, mask=mask_red)

        # Display the composite image.
        composite.show()

    def draw_time_grid(self, base_y):
        """
        Draws the time grid relative to a base_y position.

        base_y: the vertical offset for the top row of the time grid.
        The first row will be drawn at base_y (for example, 150) and the second row using an offset.
        """
        x_time = self.x_var_time
        t = self.current_time_one_hour
        # First row: 6 hours.
        for i in range(6):
            time_str = f'{t.strftime("%H")}:00'
            self.draw_text_freetype(self.ctx_black, time_str, TAHOMA_FONT_PATH, TIME_SIZE, x_time, base_y)
            x_time += 135
            t += timedelta(hours=1)

        # Second row: 7 hours. Define a vertical offset (for example, 170 pixels below the first row).
        x_time = self.x_var_time
        second_row_y = base_y + 170
        for i in range(6, 13):
            time_str = f'{t.strftime("%H")}:00'
            self.draw_text_freetype(self.ctx_black, time_str, TAHOMA_FONT_PATH, TIME_SIZE, x_time, second_row_y)
            x_time += 135
            t += timedelta(hours=1)

    def draw_weather_icons_grid(self, base_y):
        """
        Draws the weather icons grid relative to a base_y position.
        It uses the same vertical offsets as the time grid.
        """
        x_icon = self.x_var_icons
        # First row icons.
        for i in range(6):
            weather_symbol = self.search_for_forecast_icons(self.weather["hourly"][i + 1]["weather"][0]["icon"])
            self.draw_text_freetype(self.ctx_red, weather_symbol, METEO_FONT_PATH, SMALL_WEATHER_SIZE, x_icon,
                                    base_y + 35)
            x_icon += 135
        # Second row icons.
        x_icon = self.x_var_icons
        second_row_y = base_y + 170
        for i in range(6, 13):
            weather_symbol = self.search_for_forecast_icons(self.weather["hourly"][i + 1]["weather"][0]["icon"])
            self.draw_text_freetype(self.ctx_red, weather_symbol, METEO_FONT_PATH, SMALL_WEATHER_SIZE, x_icon,
                                    second_row_y + 35)
            x_icon += 135

    def draw_temperature_grid(self, base_y):
        """
        Draws the temperature grid relative to a base_y position.
        """
        x_temp = self.x_var_temp
        # First row temperatures.
        for i in range(6):
            temp_value = round(self.weather["hourly"][i + 1]["temp"])
            self.draw_text_freetype(self.ctx_black, f'{temp_value}°C', TAHOMA_FONT_PATH, TEMP_SIZE, x_temp,
                                    base_y + 110)
            x_temp += 135

        # Second row temperatures.
        x_temp = self.x_var_temp
        second_row_y = base_y + 170
        for i in range(6, 13):
            temp_value = round(self.weather["hourly"][i + 1]["temp"])
            self.draw_text_freetype(self.ctx_black, f'{temp_value}°C', TAHOMA_FONT_PATH, TEMP_SIZE, x_temp,
                                    second_row_y + 110)
            x_temp += 135

    def draw_all_grids(self, start_y):
        """
        Draws time, weather icons, and temperature grids one after the other.
        The intention is to leave the top (time grid) at start_y,
        and then add a fixed vertical gap between grids.
        """
        self.draw_time_grid(start_y)
        # Calculate next grid start based on the height used by the time grid.
        next_y = start_y + 350  # adjust this as needed (the height of a complete grid block)
        self.draw_weather_icons_grid(next_y)
        next_y += 200  # adjust based on the weather icons grid's height
        self.draw_temperature_grid(next_y)

# Main execution flow
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