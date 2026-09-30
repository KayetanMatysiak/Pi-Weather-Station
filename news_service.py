"""Optional local news support based on RSS/Atom feeds.

No news provider is hard coded: the feed URLs come from ``config.json``.
If the feature is disabled, no feed is configured, ``feedparser`` is missing
or a feed cannot be fetched/parsed, the station keeps working without news.
"""

import html
import re
import textwrap
from datetime import datetime
from typing import Any, Dict, List, Optional

TAG_RE = re.compile(r'<[^>]+>')
WHITESPACE_RE = re.compile(r'\s+')


def clean_text(value: Any) -> str:
    """Strip HTML markup and collapse whitespace from a feed value."""
    if not isinstance(value, str):
        return ''
    return WHITESPACE_RE.sub(' ', html.unescape(TAG_RE.sub(' ', value))).strip()


def truncate(text: str, max_length: int) -> str:
    """Shorten ``text`` to ``max_length`` characters with an ellipsis."""
    if not max_length or len(text) <= max_length:
        return text
    return text[:max(0, max_length - 1)].rstrip() + '…'


def wrap(text: str, width: int, max_lines: int) -> List[str]:
    """Wrap ``text`` to at most ``max_lines`` lines of ``width`` characters."""
    if not text:
        return []
    if width <= 0 or max_lines <= 0:
        return [text]
    lines = textwrap.wrap(text, width=width) or ['']
    if len(lines) <= max_lines:
        return lines
    lines = lines[:max_lines]
    lines[-1] = truncate(lines[-1] + ' …', width)
    return lines


def parse_published(entry: Dict[str, Any]) -> Optional[datetime]:
    """Return the publication date of an entry when the feed provides one."""
    for key in ('published_parsed', 'updated_parsed'):
        parsed = entry.get(key)
        if not parsed:
            continue
        try:
            return datetime(*tuple(parsed)[:6])
        except (TypeError, ValueError):
            continue
    return None


def parse_entry(entry: Any, source: str = '') -> Optional[Dict[str, Any]]:
    """Convert a feed entry into a simple headline dictionary."""
    if not isinstance(entry, dict):
        return None
    title = clean_text(entry.get('title'))
    if not title:
        return None
    return {
        'title': title,
        'source': clean_text(source),
        'link': entry.get('link') if isinstance(entry.get('link'), str) else '',
        'published': parse_published(entry),
    }


def format_headline(headline: Dict[str, Any], max_length: int = 40,
                    show_source: bool = True) -> str:
    """Format a headline, optionally prefixed with source and time."""
    prefix = ''
    if show_source:
        parts = [part for part in (headline.get('source', ''),) if part]
        published = headline.get('published')
        if isinstance(published, datetime):
            parts.append(published.strftime('%H:%M'))
        if parts:
            prefix = f"[{' '.join(parts)}] "
    return truncate(prefix + headline.get('title', ''), max_length)


class NewsService:
    """Reads headlines from one or more configurable RSS/Atom feeds."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('news', {}) if config else {}
        feeds = self.config.get('feeds') or []
        self.feeds = [feed for feed in feeds if isinstance(feed, str) and feed.strip()]
        self.enabled = bool(self.config.get('enabled', False)) and bool(self.feeds)

    def _parse_feed(self, url: str) -> List[Dict[str, Any]]:
        """Fetch and parse a single feed, returning its headlines."""
        import socket

        import feedparser

        previous_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(float(self.config.get('timeout', 10) or 10))
        try:
            parsed = feedparser.parse(url)
        finally:
            socket.setdefaulttimeout(previous_timeout)
        if getattr(parsed, 'bozo', 0) and not getattr(parsed, 'entries', None):
            raise ValueError(getattr(parsed, 'bozo_exception', 'unparsable feed'))
        source = ''
        feed_info = getattr(parsed, 'feed', None)
        if isinstance(feed_info, dict):
            source = feed_info.get('title', '')
        headlines = []
        for entry in getattr(parsed, 'entries', []) or []:
            parsed_entry = parse_entry(entry, source)
            if parsed_entry is not None:
                headlines.append(parsed_entry)
        return headlines

    def get_headlines(self) -> List[Dict[str, Any]]:
        """Return headlines from every configured feed, newest feeds first."""
        if not self.enabled:
            return []

        max_headlines = int(self.config.get('max_headlines', 4) or 4)
        per_feed = max(1, -(-max_headlines // len(self.feeds)))
        headlines: List[Dict[str, Any]] = []
        for url in self.feeds:
            try:
                feed_headlines = self._parse_feed(url)
            except Exception as error:
                print(f"Error reading news feed {url}: {error}")
                continue
            headlines.extend(feed_headlines[:per_feed])
        return headlines[:max_headlines]

    def get_lines(self) -> List[str]:
        """Return the headlines as ready-to-draw text lines."""
        max_length = int(self.config.get('max_headline_length', 40) or 40)
        headline_lines = int(self.config.get('headline_lines', 2) or 1)
        show_source = bool(self.config.get('show_source', True))
        lines: List[str] = []
        for headline in self.get_headlines():
            text = format_headline(headline, max_length * headline_lines, show_source)
            lines.extend(wrap(text, max_length, headline_lines))
        return lines
