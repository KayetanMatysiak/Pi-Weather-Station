"""Offline tests for the local news helpers (no network access)."""

import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import news_service  # noqa: E402


class TextHelperTests(unittest.TestCase):
    def test_clean_text_strips_markup_and_entities(self):
        self.assertEqual(news_service.clean_text('<b>Big</b>  news &amp; more\n'), 'Big news & more')
        self.assertEqual(news_service.clean_text(None), '')

    def test_truncate(self):
        self.assertEqual(news_service.truncate('short', 10), 'short')
        self.assertEqual(news_service.truncate('abcdefghij', 5), 'abcd…')

    def test_wrap_limits_lines(self):
        text = 'one two three four five six seven eight nine ten'
        lines = news_service.wrap(text, 10, 2)
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(len(line) <= 10 for line in lines))
        self.assertTrue(lines[-1].endswith('…'))
        self.assertEqual(news_service.wrap('', 10, 2), [])


class ParseEntryTests(unittest.TestCase):
    def test_entry_is_parsed_with_publication_metadata(self):
        entry = news_service.parse_entry(
            {'title': '<i>Road works</i> downtown', 'link': 'https://example.invalid/1',
             'published_parsed': (2026, 1, 2, 8, 30, 0, 0, 0, 0)},
            'Local Times')
        self.assertEqual(entry['title'], 'Road works downtown')
        self.assertEqual(entry['source'], 'Local Times')
        self.assertEqual(entry['published'], datetime(2026, 1, 2, 8, 30))

    def test_invalid_entries_are_skipped(self):
        self.assertIsNone(news_service.parse_entry({'title': '  '}))
        self.assertIsNone(news_service.parse_entry(None))

    def test_missing_publication_date(self):
        entry = news_service.parse_entry({'title': 'Headline'})
        self.assertIsNone(entry['published'])

    def test_format_headline(self):
        headline = {'title': 'Headline', 'source': 'Local Times',
                    'published': datetime(2026, 1, 2, 8, 30)}
        self.assertEqual(news_service.format_headline(headline, 80),
                         '[Local Times 08:30] Headline')
        self.assertEqual(news_service.format_headline(headline, 80, show_source=False),
                         'Headline')


class NewsServiceTests(unittest.TestCase):
    def test_disabled_without_feeds(self):
        service = news_service.NewsService({'news': {'enabled': True, 'feeds': []}})
        self.assertFalse(service.enabled)
        self.assertEqual(service.get_lines(), [])

    def test_headlines_are_collected_from_multiple_feeds(self):
        service = news_service.NewsService({'news': {
            'enabled': True,
            'feeds': ['https://a.invalid/rss', 'https://b.invalid/rss'],
            'max_headlines': 2,
            'max_headline_length': 40,
            'headline_lines': 1,
            'show_source': False,
        }})
        feeds = {
            'https://a.invalid/rss': [{'title': 'From A', 'source': '', 'link': '', 'published': None}],
            'https://b.invalid/rss': [{'title': 'From B', 'source': '', 'link': '', 'published': None}],
        }
        service._parse_feed = lambda url: feeds[url]
        self.assertEqual(service.get_lines(), ['From A', 'From B'])

    def test_broken_feed_does_not_break_the_others(self):
        service = news_service.NewsService({'news': {
            'enabled': True,
            'feeds': ['https://broken.invalid/rss', 'https://ok.invalid/rss'],
            'max_headlines': 2,
            'headline_lines': 1,
            'show_source': False,
        }})

        def parse(url):
            if 'broken' in url:
                raise ValueError('unparsable feed')
            return [{'title': 'Still here', 'source': '', 'link': '', 'published': None}]

        service._parse_feed = parse
        self.assertEqual(service.get_lines(), ['Still here'])


if __name__ == '__main__':
    unittest.main()
