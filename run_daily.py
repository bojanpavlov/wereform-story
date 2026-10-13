"""Check the slots and render the story. Publishing happens in publish_story.py.

Post times (Skopje):
  morning story    check 19:25, post 19:30, for TOMORROW (morning slots plus slots after 15:00)
  afternoon story  check 09:55, post 10:00, for TODAY (slots after 15:00)

A run is started in one of three ways:

  external trigger  FORCE_KIND=morning|afternoon, no date. An outside scheduler
                    (cron-job.org) starts the workflow at 19:25 / 09:55. The date
                    is worked out here.
  GitHub schedule   no FORCE_* values. A backup: GitHub's own timer often starts
                    runs late or not at all, so its window is wide and a late
                    run still checks fresh and posts.
  manual            FORCE_KIND and FORCE_DATE. Checks, renders and publishes at
                    once for that date.

The first two skip when published/<date>-<kind>.txt exists, so a story is never
posted twice. The slots are always read fresh from the booking calendar here,
right before the image is drawn.

Writes the image to docs/stories/ and prints `file`, `kind` and `marker` for the workflow.
"""
import os
import sys
from datetime import date, datetime, time, timedelta, timezone

import fetch_availability
import make_story

HERE = os.path.dirname(os.path.abspath(__file__))
STORIES_DIR = os.path.join(HERE, "docs", "stories")
PUBLISHED_DIR = os.path.join(HERE, "published")

# Post time for each story (Skopje). The check runs about 5 minutes before it.
POST_TIME = {"morning": (19, 30), "afternoon": (10, 0)}

# When a run may produce each story (Skopje, start inclusive, end exclusive).
# The GitHub-schedule window starts at the check time and stays open for late runs.
SCHEDULE_WINDOW = {"morning": (time(19, 20), time(21, 30)), "afternoon": (time(9, 50), time(12, 0))}
# An external trigger names the kind itself. It may not run early (the publish
# step waits 15 minutes at most) or on the wrong day.
TRIGGER_WINDOW = {"morning": (time(19, 15), time(23, 59, 59)), "afternoon": (time(9, 45), time(15, 0))}


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


def _in_window(now, window):
    start, end = window
    return start <= now.time().replace(tzinfo=None) < end


def class_day(now, kind):
    """The morning story is for tomorrow, the afternoon story for today."""
    return now.date() + timedelta(days=1) if kind == "morning" else now.date()


def due_story(now):
    """Return (day, kind) if the GitHub schedule should produce a story at this Skopje time, else None."""
    for kind, window in SCHEDULE_WINDOW.items():
        if _in_window(now, window):
            return class_day(now, kind), kind
    return None


def resolve_target(now, forced_kind, forced_date):
    """Return ((day, kind, manual), None) for this run, or (None, reason) when there is nothing to do."""
    if forced_kind and forced_kind not in POST_TIME:
        return None, f"Unknown kind {forced_kind!r}."
    if forced_kind and forced_date:
        return (date.fromisoformat(forced_date), forced_kind, True), None
    if forced_kind:
        if not _in_window(now, TRIGGER_WINDOW[forced_kind]):
            return None, f"{now.strftime('%H:%M')} Skopje is outside the {forced_kind} story's hours; nothing to do."
        return (class_day(now, forced_kind), forced_kind, False), None
    due = due_story(now)
    if due is None:
        return None, "Not a posting time in Skopje; nothing to do."
    return (due[0], due[1], False), None


def marker_name(day, kind):
    return f"{day.isoformat()}-{kind}"


def already_published(day, kind):
    return os.path.exists(os.path.join(PUBLISHED_DIR, marker_name(day, kind) + ".txt"))


def main():
    now = skopje_now(datetime.now(timezone.utc))
    target, reason = resolve_target(now, os.environ.get("FORCE_KIND"), os.environ.get("FORCE_DATE"))
    if target is None:
        print(reason)
        return 0
    day, kind, manual = target

    if not manual and already_published(day, kind):
        print(f"The {kind} story for {day.isoformat()} is already published; nothing to do.")
        return 0

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

    # The publish step waits for the post time (not on manual runs), after the image is committed.
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"file={rel}\n")
            f.write(f"kind={'' if manual else kind}\n")
            f.write(f"marker={marker_name(day, kind)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
