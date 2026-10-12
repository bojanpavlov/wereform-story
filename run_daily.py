"""Check the slots and render the story. Publishing happens in publish_story.py.

Each scheduled run starts 5 minutes before the post time:

  19:25 -> check the slots for TOMORROW's morning sessions, render, post at 19:30
  09:55 -> check the slots for TODAY's afternoon sessions, render, post at 10:00

The slots are read fresh from the booking calendar at the check time. The
publish step (publish_story.py) waits for the post time after the image is
committed, so the story goes out at 19:30 or 10:00 with data that is about
5 minutes old.

GitHub cron runs in UTC and does not follow daylight saving, so the workflow
fires at both possible UTC times. This script exits quietly unless the Skopje
time falls in a check window. The windows are wide enough to allow for GitHub
starting a run a few minutes late.

Manual run: FORCE_KIND=morning FORCE_DATE=2026-10-13 python run_daily.py
A manual run checks, renders and publishes at once, without waiting for a post time.
Writes the image to docs/stories/ and prints `file=<path>` for the workflow.
"""
import os
import sys
from datetime import date, datetime, timedelta, timezone

import fetch_availability
import make_story

HERE = os.path.dirname(os.path.abspath(__file__))
STORIES_DIR = os.path.join(HERE, "docs", "stories")

# Post time for each story (Skopje). The check runs about 5 minutes before it.
POST_TIME = {"morning": (19, 30), "afternoon": (10, 0)}


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
    """Return (day, kind) if a check is due at this Skopje time, else None.

    The morning check starts at 19:20 (for tomorrow), the afternoon check at 09:50 (for today).
    """
    if now.hour == 19 and now.minute >= 20:
        return now.date() + timedelta(days=1), "morning"
    if now.hour == 9 and now.minute >= 50:
        return now.date(), "afternoon"
    return None


def main():
    forced_kind = os.environ.get("FORCE_KIND")
    forced_date = os.environ.get("FORCE_DATE")
    now = skopje_now(datetime.now(timezone.utc))
    if forced_kind and forced_date:
        day, kind = date.fromisoformat(forced_date), forced_kind
        scheduled = False
    else:
        due = due_story(now)
        if due is None:
            print("Not a check time in Skopje; nothing to do.")
            return 0
        day, kind = due
        scheduled = True

    calendar = fetch_availability.fetch_calendar()
    if not fetch_availability.is_open_day(calendar, day):
        print(f"{day.isoformat()} is a closed day (holiday or not open for booking); no story posted.")
        return 0

    # The morning story also lists the afternoon slots; the afternoon story lists only its own.
    kind_filter = None if kind == "morning" else kind
    slots = fetch_availability.slots_for_day(calendar, day, kind_filter)
    if not slots:
        print(f"No free {kind} slots on {day.isoformat()}; no story posted.")
        return 0

    print(f"Checked at {now.strftime('%H:%M')} Skopje, {day.isoformat()} {kind}:")
    for s in slots:
        print(f"  {s['time']}  {s['kind']:<9}  {s['free']} free")

    os.makedirs(STORIES_DIR, exist_ok=True)
    # The check time is in the name, so a new image never reuses an old URL that
    # GitHub Pages may still have cached.
    out_path = os.path.join(STORIES_DIR, f"{day.isoformat()}-{kind}-{now.strftime('%H%M')}.png")
    make_story.render(day, kind, slots, out_path)
    rel = os.path.relpath(out_path, HERE)
    print(f"Rendered {rel} with {len(slots)} slot(s).")

    # The publish step waits for the post time, after the image is committed.
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"file={rel}\n")
            f.write(f"kind={kind if scheduled else ''}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
