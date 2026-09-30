"""Offline tests for the configuration loader.

Run with: python3 -m unittest discover -s tests
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402


class LoadConfigTests(unittest.TestCase):
    def test_missing_file_returns_defaults(self):
        loaded = config.load_config(os.path.join(tempfile.gettempdir(), 'does-not-exist.json'))
        self.assertEqual(loaded, config.DEFAULT_CONFIG)
        self.assertFalse(config.is_enabled(loaded, 'calendar'))
        self.assertFalse(config.is_enabled(loaded, 'news'))

    def test_defaults_are_not_mutated(self):
        loaded = config.load_config(None)
        loaded['news']['feeds'].append('https://example.invalid/rss')
        self.assertEqual(config.DEFAULT_CONFIG['news']['feeds'], [])

    def test_partial_file_is_merged_with_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'config.json')
            with open(path, 'w', encoding='utf-8') as handle:
                json.dump({'news': {'enabled': True, 'feeds': ['https://example.invalid/rss']}}, handle)
            loaded = config.load_config(path)
        self.assertTrue(config.is_enabled(loaded, 'news'))
        self.assertEqual(loaded['news']['feeds'], ['https://example.invalid/rss'])
        self.assertEqual(loaded['news']['max_headlines'],
                         config.DEFAULT_CONFIG['news']['max_headlines'])
        self.assertFalse(config.is_enabled(loaded, 'calendar'))

    def test_malformed_file_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'config.json')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('{not json')
            loaded = config.load_config(path)
        self.assertEqual(loaded, config.DEFAULT_CONFIG)


if __name__ == '__main__':
    unittest.main()
