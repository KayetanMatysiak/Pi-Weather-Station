"""Optional configuration loading for the weather station.

The station works without any configuration file at all: in that case the
defaults below are used and the optional Google Calendar / local news panels
stay disabled, so the display keeps behaving exactly as before.
"""

import copy
import json
import os
from typing import Any, Dict

CONFIG_FILE = 'config.json'

DEFAULT_CONFIG: Dict[str, Any] = {
    'weather': {
        # Leave empty to keep the values already set in main.py.
        'lat': '',
        'lon': '',
        'appid': '',
        'units': 'metric',
    },
    'calendar': {
        'enabled': False,
        'calendar_id': 'primary',
        # OAuth 2.0 client secrets downloaded from the Google Cloud Console.
        'credentials_file': 'credentials.json',
        # Created automatically on the first authorisation, never commit it.
        'token_file': 'token.json',
        'max_events': 5,
        'lookahead_days': 7,
        # IANA name (e.g. "Europe/Madrid"); empty means the local timezone.
        'timezone': '',
        'max_title_length': 32,
    },
    'news': {
        'enabled': False,
        # Add one or more RSS/Atom feed URLs of your own local news provider.
        'feeds': [],
        'max_headlines': 4,
        'max_headline_length': 40,
        'headline_lines': 2,
        'show_source': True,
        'timeout': 10,
    },
}


def _merge(defaults: Dict[str, Any], overrides: Any) -> Dict[str, Any]:
    """Recursively merge ``overrides`` on top of ``defaults``."""
    merged = copy.deepcopy(defaults)
    if not isinstance(overrides, dict):
        return merged
    for key, value in overrides.items():
        if isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def load_config(path: str = CONFIG_FILE) -> Dict[str, Any]:
    """Load the configuration file, falling back to the defaults.

    A missing, unreadable or malformed file is not an error: the station keeps
    running with the optional features disabled.
    """
    config = copy.deepcopy(DEFAULT_CONFIG)
    if not path or not os.path.exists(path):
        return config
    try:
        with open(path, 'r', encoding='utf-8') as config_file:
            user_config = json.load(config_file)
    except (OSError, ValueError) as error:
        print(f"Error reading {path}, using defaults: {error}")
        return config
    return _merge(config, user_config)


def is_enabled(config: Dict[str, Any], section: str) -> bool:
    """Return True when an optional ``section`` is explicitly enabled."""
    return bool(config.get(section, {}).get('enabled', False))
