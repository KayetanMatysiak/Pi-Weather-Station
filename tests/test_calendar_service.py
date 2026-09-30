"""Offline tests for the Google Calendar helpers (no credentials, no network)."""

import os
import sys
import unittest
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import calendar_service  # noqa: E402


class ParseEventTests(unittest.TestCase):
    def test_timed_event_is_converted_to_configured_timezone(self):
        event = calendar_service.parse_event(
            {'summary': 'Team Meeting', 'start': {'dateTime': '2026-01-02T09:00:00Z'}},
            timezone.utc)
        self.assertIsNotNone(event)
        self.assertFalse(event['all_day'])
        self.assertEqual(event['summary'], 'Team Meeting')
        self.assertEqual(event['start'], datetime(2026, 1, 2, 9, 0, tzinfo=timezone.utc))

    def test_all_day_event(self):
        event = calendar_service.parse_event({'summary': 'Holiday', 'start': {'date': '2026-01-02'}})
        self.assertTrue(event['all_day'])
        self.assertEqual(event['start'], date(2026, 1, 2))

    def test_cancelled_and_malformed_events_are_skipped(self):
        self.assertIsNone(calendar_service.parse_event(
            {'summary': 'Gone', 'status': 'cancelled', 'start': {'date': '2026-01-02'}}))
        self.assertIsNone(calendar_service.parse_event({'summary': 'No start'}))
        self.assertIsNone(calendar_service.parse_event({'start': {'dateTime': 'not-a-date'}}))
        self.assertIsNone(calendar_service.parse_event({'start': {'date': '2026-13-45'}}))
        self.assertIsNone(calendar_service.parse_event('nonsense'))

    def test_missing_summary_gets_placeholder(self):
        event = calendar_service.parse_event({'start': {'date': '2026-01-02'}})
        self.assertEqual(event['summary'], '(no title)')


class FormatEventTests(unittest.TestCase):
    def test_timed_event_line(self):
        line = calendar_service.format_event(
            {'summary': 'Dentist', 'all_day': False, 'start': datetime(2026, 1, 2, 14, 30)})
        self.assertEqual(line, '02/01 14:30  Dentist')

    def test_all_day_event_line(self):
        line = calendar_service.format_event(
            {'summary': 'Holiday', 'all_day': True, 'start': date(2026, 1, 2)})
        self.assertEqual(line, '02/01 all day  Holiday')

    def test_long_title_is_truncated(self):
        line = calendar_service.format_event(
            {'summary': 'A' * 50, 'all_day': True, 'start': date(2026, 1, 2)}, 10)
        self.assertTrue(line.endswith('…'))
        self.assertEqual(line, '02/01 all day  ' + 'A' * 9 + '…')


class CalendarServiceTests(unittest.TestCase):
    def test_disabled_service_returns_no_lines(self):
        service = calendar_service.CalendarService({'calendar': {'enabled': False}})
        self.assertFalse(service.enabled)
        self.assertEqual(service.get_lines(), [])

    def test_api_failure_degrades_gracefully(self):
        service = calendar_service.CalendarService({'calendar': {'enabled': True}})

        def boom():
            raise RuntimeError('network down')

        service._raw_events = boom
        self.assertEqual(service.get_lines(), [])

    def test_events_are_limited_and_filtered(self):
        service = calendar_service.CalendarService(
            {'calendar': {'enabled': True, 'max_events': 2, 'timezone': 'UTC'}})
        service._raw_events = lambda: [
            {'status': 'cancelled', 'start': {'date': '2026-01-01'}},
            {'summary': 'One', 'start': {'dateTime': '2026-01-02T09:00:00Z'}},
            {'summary': 'Two', 'start': {'date': '2026-01-03'}},
            {'summary': 'Three', 'start': {'date': '2026-01-04'}},
        ]
        lines = service.get_lines()
        self.assertEqual(lines, ['02/01 09:00  One', '03/01 all day  Two'])

    def test_unknown_timezone_falls_back_to_local(self):
        service = calendar_service.CalendarService(
            {'calendar': {'enabled': True, 'timezone': 'Not/AZone'}})
        self.assertIsNone(service.tzinfo)


if __name__ == '__main__':
    unittest.main()
