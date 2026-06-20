#!/usr/bin/env python3
"""Hush pin drip builder — gated daily auto-release (R-020/R-023), Hush parity.

Mirror of korp-blog/scripts/build_pin_feeds.py, but for the ISOLATED Hush brand:
serves feeds from docs/feeds/ via GitHub Pages (Hush has no own-domain feed repo
like korp.studio). Runs DAILY in the cloud (GitHub Action). Releases pins whose
release_date is due (<= today UTC, within WINDOW_DAYS) into
docs/feeds/pins-<slug>.xml from data/pins-manifest.json; the Action commits any
change and GitHub Pages republishes.

The GATE is the schedule itself: a pin gets a release_date ONLY when Brandon
STARTS its batch at a chosen rate ("release N per day" -> start_campaign("hush")).
Un-started pins have NO release_date and are NEVER released — so when nothing is
started, this releases nothing. Item links stay on hushchews.com (the claimed
domain); images are Cloudinary URLs from the manifest.

Self-contained: Python stdlib only. Override today for testing with QUARRY_TODAY.
"""
from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "pins-manifest.json"
FEEDS_DIR = ROOT / "docs" / "feeds"            # GitHub Pages serves /docs as the site root
WINDOW_DAYS = 14
DESC_MAX = 500
_EPOCH = "Mon, 01 Jan 2024 00:00:00 +0000"


def slug(board: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (board or "quarry-pins").lower()).strip("-") or "pins"


def rfc822_from_date(d: str) -> str:
    return datetime.fromisoformat(d).replace(hour=9, tzinfo=timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S +0000")


def today_utc() -> date:
    override = os.environ.get("QUARRY_TODAY")
    return date.fromisoformat(override) if override else datetime.now(timezone.utc).date()


def build() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    brand = data.get("brand", "hush")
    domain = data.get("domain", "")
    pins = data.get("pins", [])

    today = today_utc()
    build_ts = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    lo = (today - timedelta(days=WINDOW_DAYS)).isoformat()
    hi = today.isoformat()
    due = [p for p in pins if p.get("release_date") and lo <= p["release_date"] <= hi]

    boards: dict[str, list[dict]] = {(p.get("board") or "Quarry Pins"): [] for p in pins}
    for p in due:
        boards[p.get("board") or "Quarry Pins"].append(p)

    FEEDS_DIR.mkdir(parents=True, exist_ok=True)
    for board, bpins in sorted(boards.items()):
        # newest-first (RSS convention; the freshest pins sit at the top of the feed)
        bpins.sort(key=lambda p: (p.get("release_date", ""), p.get("pin_id", "")), reverse=True)
        items = []
        for p in bpins:
            img = p.get("image_url", "")
            items.append(
                "    <item>\n"
                f"      <title>{escape(p.get('title', ''))}</title>\n"
                f"      <link>{escape(p.get('link', ''))}</link>\n"
                f'      <guid isPermaLink="false">{brand}:{p.get("pin_id", "")}</guid>\n'
                f"      <pubDate>{rfc822_from_date(p['release_date'])}</pubDate>\n"
                f"      <description><![CDATA[{(p.get('description') or '')[:DESC_MAX]}]]></description>\n"
                f'      <media:content url="{escape(img)}" medium="image" type="image/png"/>\n'
                f'      <enclosure url="{escape(img)}" type="image/png" length="0"/>\n'
                "    </item>"
            )
        last_build = build_ts
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">\n'
            "  <channel>\n"
            f"    <title>{escape(board)} — Hush</title>\n"
            f"    <link>https://{domain}/</link>\n"
            f"    <description>{escape(board)} — hormone-free menopause self-care pins from Hush.</description>\n"
            "    <language>en-us</language>\n"
            f"    <lastBuildDate>{last_build}</lastBuildDate>\n"
            + ("\n".join(items) + "\n" if items else "")
            + "  </channel>\n"
            "</rss>\n"
        )
        (FEEDS_DIR / f"pins-{slug(board)}.xml").write_text(xml, encoding="utf-8")

    print(f"[hush-drip] {today.isoformat()} — {len(due)} pin(s) live across {len(boards)} feed(s) "
          f"(started batches only; un-started pins never release)")
    for board, bpins in sorted(boards.items()):
        print(f"  pins-{slug(board)}.xml: {len(bpins)} item(s)")
    return len(due)


if __name__ == "__main__":
    build()
