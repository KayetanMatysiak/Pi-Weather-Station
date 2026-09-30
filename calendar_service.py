"""Optional Google Calendar support.

The integration is entirely optional: if it is not configured, the Google
libraries are missing, or authorisation / the API call fails, the service
simply reports that it has no events and the weather display keeps working.
"""

import os
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

try:  # Python 3.9+
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - very old Python
    ZoneInfo = None  # type: ignore[assignment]

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def _resolve_timezone(name: str):
    """Return a tzinfo for ``name`` or None to keep the local timezone."""
    if not name or ZoneInfo is None:
        return None
    try:
        return ZoneInfo(name)
    except Exception as error:
        print(f"Unknown calendar timezone '{name}': {error}")
        return None


def parse_datetime(value: str) -> Optional[datetime]:
    """Parse an RFC 3339 timestamp coming from the Calendar API."""
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None


def parse_event(raw_event: Any, tzinfo=None) -> Optional[Dict[str, Any]]:
    """Convert a Calendar API event into a simple dictionary.

    Returns None for cancelled or malformed events so that they can be
    skipped without breaking the rest of the agenda.
    """
    if not isinstance(raw_event, dict):
        return None
    if raw_event.get('status') == 'cancelled':
        return None

    start = raw_event.get('start')
    if not isinstance(start, dict):
        return None

    summary = raw_event.get('summary') or '(no title)'
    location = raw_event.get('location') or ''

    if start.get('date'):
        try:
            all_day_start = date.fromisoformat(start['date'])
        except (TypeError, ValueError):
            return None
        return {
            'summary': str(summary).strip(),
            'location': str(location).strip(),
            'all_day': True,
            'start': all_day_start,
        }

    start_time = parse_datetime(start.get('dateTime', ''))
    if start_time is None:
        return None
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if tzinfo is not None:
        start_time = start_time.astimezone(tzinfo)
    else:
        start_time = start_time.astimezone()
    return {
        'summary': str(summary).strip(),
        'location': str(location).strip(),
        'all_day': False,
        'start': start_time,
    }


def format_event(event: Dict[str, Any], max_title_length: int = 32) -> str:
    """Format a parsed event as a single agenda line."""
    summary = event.get('summary') or '(no title)'
    if max_title_length and len(summary) > max_title_length:
        summary = summary[:max(0, max_title_length - 1)].rstrip() + '…'

    start = event.get('start')
    if event.get('all_day') or (isinstance(start, date) and not isinstance(start, datetime)):
        prefix = start.strftime('%d/%m') if isinstance(start, date) else '--'
        return f'{prefix} all day  {summary}'
    if isinstance(start, datetime):
        return f'{start.strftime("%d/%m %H:%M")}  {summary}'
    return summary


class CalendarService:
    """Fetches the next events of a Google Calendar over OAuth 2.0."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('calendar', {}) if config else {}
        self.enabled = bool(self.config.get('enabled', False))
        self.tzinfo = _resolve_timezone(self.config.get('timezone', ''))

    def _credentials(self):
        """Load (and refresh or create) the stored OAuth credentials."""
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow

        token_file = self.config.get('token_file', 'token.json')
        credentials_file = self.config.get('credentials_file', 'credentials.json')

        creds = None
        if token_file and os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        if creds and creds.valid:
            return creds
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_file):
                raise FileNotFoundError(
                    f"Google OAuth client secrets not found: {credentials_file}")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        if token_file:
            with open(token_file, 'w', encoding='utf-8') as token:
                token.write(creds.to_json())
        return creds

    def _raw_events(self) -> List[Any]:
        """Call the Calendar API and return the raw event list."""
        from googleapiclient.discovery import build

        max_events = int(self.config.get('max_events', 5) or 5)
        lookahead_days = int(self.config.get('lookahead_days', 7) or 7)
        now = datetime.now(timezone.utc)

        service = build('calendar', 'v3', credentials=self._credentials(),
                        cache_discovery=False)
        response = service.events().list(
            calendarId=self.config.get('calendar_id', 'primary'),
            timeMin=now.isoformat(),
            timeMax=(now + timedelta(days=lookahead_days)).isoformat(),
            maxResults=max_events,
            singleEvents=True,
            orderBy='startTime',
        ).execute()
        items = response.get('items', []) if isinstance(response, dict) else []
        return items if isinstance(items, list) else []

    def get_events(self) -> List[Dict[str, Any]]:
        """Return the upcoming events, or an empty list on any failure."""
        if not self.enabled:
            return []
        try:
            raw_events = self._raw_events()
        except Exception as error:
            print(f"Error fetching calendar events: {error}")
            return []

        max_events = int(self.config.get('max_events', 5) or 5)
        events = []
        for raw_event in raw_events:
            parsed = parse_event(raw_event, self.tzinfo)
            if parsed is not None:
                events.append(parsed)
            if len(events) >= max_events:
                break
        return events

    def get_lines(self) -> List[str]:
        """Return the agenda as ready-to-draw text lines."""
        max_title_length = int(self.config.get('max_title_length', 32) or 32)
        return [format_event(event, max_title_length) for event in self.get_events()]
