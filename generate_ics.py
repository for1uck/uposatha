# -*- coding: utf-8 -*-
"""
Generate iCalendar (.ics) subscriptions for the Uposatha days computed by
mmcalendar_kernel.py (the algorithm embedded in the Metteyya Android app).

Two feeds are produced:

  uposatha.ics            - every uposatha day (4 monthly phases) plus the
                            five great festival days
  uposatha-festivals.ics  - only the five great festival days

The files are RFC 5545 compliant: all-day VALUE=DATE events, CRLF line
endings, UTF-8 with 75-octet line folding and stable, deterministic UIDs so
calendar apps update (not duplicate) events when the feed is regenerated.

Usage:
  python3 generate_ics.py --start 2018 --end 2040 --out site
"""

import argparse
import datetime as _dt
from pathlib import Path

from mmcalendar_kernel import (
    calculate_days, get_moon_name,
    FULL_MOON, NEW_MOON, FIRST_QUARTER, LAST_QUARTER,
)

# Stable domain used in UIDs. Change via --domain if you deploy elsewhere;
# changing it later makes subscribers see a fresh set of events.
DEFAULT_DOMAIN = "for1uck.github.io"

PHASE_EN = {
    FULL_MOON: "Full Moon Uposatha",
    NEW_MOON: "New Moon Uposatha",
    FIRST_QUARTER: "First Quarter Uposatha",
    LAST_QUARTER: "Last Quarter Uposatha",
}

# The five festivals hard-coded in the app.
FESTIVAL_EN = {
    "敬僧节": "Magha Puja (Sangha Day)",
    "敬佛节": "Vesak Puja (Buddha Day)",
    "敬法节": "Asalha Puja (Dhamma Day)",
    "入雨安居": "Vassa Begins (Rain Retreat)",
    "出雨安居": "Pavarana Day (Vassa Ends)",
}

CALENDARS = [
    ("uposatha.ics",
     "布萨日（月圆/月黑/上弦/下弦）Uposatha Days",
     "缅甸传统算法计算的每月四个布萨（伍波思特）日及佛教重大节日。",
     "all"),
    ("uposatha-festivals.ics",
     "佛教重大节日 Buddhist Festival Days",
     "敬僧节、敬佛节、敬法节、入雨安居、出雨安居。",
     "festivals"),
]


def fold(line: str) -> bytes:
    """RFC 5545 line folding: first line <=75 octets, continuations <=74."""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return raw + b"\r\n"
    out, first = b"", True
    while raw:
        limit = 75 if first else 74
        chunk, raw = raw[:limit], raw[limit:]
        out += chunk + b"\r\n"
        if raw:
            out += b" "
        first = False
    return out


def esc(text: str) -> str:
    return (text.replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\n", "\\n"))


def build_events(year0, year1, kind, domain):
    """Yield VEVENT field dicts in chronological order."""
    d = _dt.date(year0, 1, 1)
    end = _dt.date(year1, 12, 31)
    while d <= end:
        moon = get_moon_name(d)
        _, festival = calculate_days(d, moon)
        if not moon and not festival:
            d += _dt.timedelta(days=1)
            continue
        if kind == "festivals" and not festival:
            d += _dt.timedelta(days=1)
            continue

        key = festival or PHASE_EN[moon]
        uid = "uposatha-%s-%s@%s" % (
            d.strftime("%Y%m%d"),
            (festival or moon).encode("utf-8").hex(),
            domain)

        if festival:
            if moon:
                summary = "%s · %s / %s" % (
                    festival, moon, FESTIVAL_EN[festival])
            else:
                summary = "%s / %s" % (festival, FESTIVAL_EN[festival])
            desc = ("%s — %s。\n"
                    "日期依据「美德雅 Metteyya」App 内置缅甸历法算法计算。"
                    % (festival, FESTIVAL_EN[festival]))
        else:
            summary = "%s（布萨日） / %s" % (moon, PHASE_EN[moon])
            desc = ("%s（伍波思特日），依缅甸传统历法。\n"
                    "Dates follow the arithmetic Myanmar calendar used by the "
                    "Metteyya app; they may differ by a day from the "
                    "astronomical phase." % moon)

        yield {
            "uid": uid,
            "dtstart": d.strftime("%Y%m%d"),
            "dtend": (d + _dt.timedelta(days=1)).strftime("%Y%m%d"),
            "summary": summary,
            "desc": desc,
            "categories": festival or PHASE_EN[moon],
        }
        d += _dt.timedelta(days=1)


def render_ics(events, name, desc, domain, now):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//metteyya//Uposatha Calendar//ZH",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:%s" % name,
        "X-WR-CALDESC:%s" % desc,
        "X-WR-TIMEZONE:Asia/Yangon",
    ]
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    for ev in events:
        lines += [
            "BEGIN:VEVENT",
            "UID:%s" % ev["uid"],
            "DTSTAMP:%s" % stamp,
            "DTSTART;VALUE=DATE:%s" % ev["dtstart"],
            "DTEND;VALUE=DATE:%s" % ev["dtend"],
            "SUMMARY:%s" % esc(ev["summary"]),
            "DESCRIPTION:%s" % esc(ev["desc"]),
            "CATEGORIES:%s" % esc(ev["categories"]),
            "STATUS:CONFIRMED",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return b"".join(fold(l) for l in lines)


def main():
    ap = argparse.ArgumentParser()
    today = _dt.date.today()
    ap.add_argument("--start", type=int, default=today.year - 2)
    ap.add_argument("--end", type=int, default=today.year + 10)
    ap.add_argument("--out", default="site")
    ap.add_argument("--domain", default=DEFAULT_DOMAIN)
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    now = _dt.datetime.now(_dt.timezone.utc)

    for fname, name, desc, kind in CALENDARS:
        events = list(build_events(args.start, args.end, kind, args.domain))
        data = render_ics(events, name, desc, args.domain, now)
        path = out_dir / fname
        path.write_bytes(data)
        print("%-26s %5d events  %d bytes  (%d-%d)"
              % (fname, len(events), len(data), args.start, args.end))


if __name__ == "__main__":
    main()
