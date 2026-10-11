"""Decide which story is due now, render it, and print its path.

Schedule (Skopje time):
  19:30 -> morning sessions for TOMORROW
  10:00 -> afternoon sessions for TODAY

GitHub cron runs in UTC and does not follow daylight saving, so the workflow
fires at both possible UTC times. This script exits quietly unless the Skopje
hour matches one of the two posting times. Matching on the hour leaves room
for GitHub starting a run a few minutes late.

Manual run: FORCE_KIND=morning FORCE_DATE=2026-10-13 python run_daily.py
Writes the image to docs/stories/ and prints `file=<path>` for the workflow.
"""
import os
import sys
from datetime import date, datetime, timedelta, timezone

import fetch_availability
import make_story

HERE = os.path.dirname(os.path.abspath(__file__))
STORIES_DIR = os.path.join(HERE, "docs", "stories")


def skopje_now(utc_now):
    """Europe/Skopje follows EU rules: DST from the last Sunday of March to the last Sunday of October."""
    year = utc_now.year
    dst_start = _last_sunday(year, 3).replace(hour=1, tzinfo=timezone.utc)
    dst_end = _last_sunday(year, 10).replace(hour=1, tzinfo=timezone.utc)
    offset = 2 if dst_start <= utc_now < dst_end else 1
    return utc_now + timedelta(hours=offset)


def _last_sunday(year, month):
    d = datetime(year, month + 1, 1, tzinfo=timezone.utc) if month < 12 else datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    d -= timedelta(days=1)
    return d - timedelta(days=(d.weekday() + 1) % 7)


def due_story(now):
    """Return (day, kind) if a story is due at this Skopje time, else None."""
    if now.hour == 19:
        return now.date() + timedelta(days=1), "morning"
    if now.hour == 10:
        return now.date(), "afternoon"
    return None


def main():
    forced_kind = os.environ.get("FORCE_KIND")
    forced_date = os.environ.get("FORCE_DATE")
    if forced_kind and forced_date:
        day, kind = date.fromisoformat(forced_date), forced_kind
    else:
        due = due_story(skopje_now(datetime.now(timezone.utc)))
        if due is None:
            print("Not a posting time in Skopje; nothing to do.")
            return 0
        day, kind = due

    slots = fetch_availability.slots_for_day(fetch_availability.fetch_calendar(), day, kind)
    if not slots:
        print(f"No free {kind} slots on {day.isoformat()}; no story posted.")
        return 0

    os.makedirs(STORIES_DIR, exist_ok=True)
    out_path = os.path.join(STORIES_DIR, f"{day.isoformat()}-{kind}.png")
    make_story.render(day, kind, slots, out_path)
    rel = os.path.relpath(out_path, HERE)
    print(f"Rendered {rel} with {len(slots)} slot(s).")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"file={rel}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
