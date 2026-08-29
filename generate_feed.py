#!/usr/bin/env python3
"""
Generates a "Palabra del día" RSS feed (Spanish word of the day, with
English translation and an example sentence) from words.json.

No third-party dependencies -- only the Python standard library, so this
runs anywhere Python 3 runs, including a bare GitHub Actions runner.

Usage:
    python3 generate_feed.py

Produces rss.xml in the same directory. Re-run it daily (see the
GitHub Actions workflow in feed.yml) and it regenerates the feed with a
rolling window of recent + upcoming days.
"""

import json
import html
from datetime import date, timedelta, datetime, timezone
from pathlib import Path
from email.utils import format_datetime

HERE = Path(__file__).parent
WORDS_FILE = HERE / "words.json"
OUTPUT_FILE = HERE / "rss.xml"

# --- Configure this for your own feed -------------------------------------
FEED_TITLE = "Palabra del Día"
FEED_LINK = "https://armoredrodent.github.io/palabra-del-dia/"  # change to where you host it
FEED_DESCRIPTION = "A Spanish word of the day, with English translation and an example sentence."
FEED_LANGUAGE = "en"
DAYS_BACK = 13   # how many past days to include as items
DAYS_FORWARD = 0  # set > 0 only if you want to preview future days
# ---------------------------------------------------------------------------


def load_words():
    with open(WORDS_FILE, encoding="utf-8") as f:
        return json.load(f)


def word_for_date(words, d: date):
    """Deterministic pick: same day-of-year formula the companion app uses,
    so the RSS feed and the app always agree on 'today's word'."""
    day_of_year = d.timetuple().tm_yday
    idx = day_of_year % len(words)
    return words[idx]


def build_item_xml(d: date, word: dict) -> str:
    title = html.escape(f"{word['es']} — {word['en']}")
    pub_date = format_datetime(datetime(d.year, d.month, d.day, 6, 0, tzinfo=timezone.utc))
    guid = f"palabra-del-dia-{d.isoformat()}"

    description_html = (
        f"<p><strong>{html.escape(word['es'])}</strong> "
        f"<em>{html.escape(word['ipa'])}</em> — {html.escape(word['pos'])}</p>"
        f"<p>{html.escape(word['en'])}</p>"
        f"<p><strong>En una frase:</strong><br>"
        f"{html.escape(word['ex_es'])}<br>"
        f"<span style=\"color:#666\">{html.escape(word['ex_en'])}</span></p>"
    )
    description = html.escape(description_html)

    return f"""    <item>
      <title>{title}</title>
      <link>{FEED_LINK}</link>
      <guid isPermaLink="false">{guid}</guid>
      <pubDate>{pub_date}</pubDate>
      <description>{description}</description>
    </item>"""


def build_feed_xml(items_xml: list) -> str:
    now = format_datetime(datetime.now(timezone.utc))
    items_joined = "\n".join(items_xml)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{html.escape(FEED_TITLE)}</title>
    <link>{FEED_LINK}</link>
    <description>{html.escape(FEED_DESCRIPTION)}</description>
    <language>{FEED_LANGUAGE}</language>
    <lastBuildDate>{now}</lastBuildDate>
{items_joined}
  </channel>
</rss>
"""


def main():
    words = load_words()
    today = date.today()

    dates = [
        today - timedelta(days=i)
        for i in range(DAYS_BACK, -1, -1)
    ] + [
        today + timedelta(days=i)
        for i in range(1, DAYS_FORWARD + 1)
    ]

    items_xml = [build_item_xml(d, word_for_date(words, d)) for d in dates]
    # newest first, which is the RSS convention
    items_xml.reverse()

    feed_xml = build_feed_xml(items_xml)
    OUTPUT_FILE.write_text(feed_xml, encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE} with {len(items_xml)} items.")


if __name__ == "__main__":
    main()
