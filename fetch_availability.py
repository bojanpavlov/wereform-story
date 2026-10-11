"""Read free spots for the group classes from the public Amelia booking calendar.

Makes the same request the booking page makes in a visitor's browser, so no
login is needed. Slots come back with `c` = free places when someone has
already booked; a slot without `c` has no bookings, so all places are free.
Fully booked slots are not listed here.

Usage: python fetch_availability.py 2026-10-13 [morning|afternoon]
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import date

BASE_URL = os.environ.get("WEREFORM_BASE_URL", "https://wereform.mk")
MAX_CAPACITY = int(os.environ.get("MAX_CAPACITY", "5"))
GROUP_SERVICE_ID = os.environ.get("AMELIA_GROUP_SERVICE_ID", "3")
USER_AGENT = "wereform-story/1.0 (+https://github.com/bojanpavlov/wereform-story)"
LOCATION_ID = "1"
PROVIDER_ID = "1"


def kind_for_hour(hour):
    """Morning: 06:00-09:59. Afternoon: after 15:00. Anything else is not published."""
    if 6 <= hour < 10:
        return "morning"
    if hour > 15:
        return "afternoon"
    return None


def fetch_calendar():
    """Return the calendar data: "slots" (open slots) and "occupied" (booked-out slots), keyed by date."""
    params = {
        "action": "wpamelia_api",
        "call": "/slots",
        "monthsLoad": "1",
        "locationId": LOCATION_ID,
        "serviceId": GROUP_SERVICE_ID,
        "providerIds": PROVIDER_ID,
        "group": "1",
        "page": "booking",
        "structured": "true",
        "persons": "1",
    }
    url = f"{BASE_URL}/wp-admin/admin-ajax.php?{urllib.parse.urlencode(params)}"
    # The site rejects Python's default user agent with HTTP 406.
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    if "data" not in body or "slots" not in body["data"]:
        raise RuntimeError(f"Unexpected response from Amelia: {str(body)[:300]}")
    return body["data"]


def is_open_day(calendar, day):
    """A day is open for booking when it has any slot, free or fully booked.

    Closed days (for example holidays) have no entry at all in the calendar.
    """
    key = day.isoformat()
    return key in calendar.get("slots", {}) or key in calendar.get("occupied", {})


def slots_for_day(calendar, day, kind=None):
    """Published slots for one day: [{"time", "hour", "free", "kind"}], sorted by time."""
    result = []
    for time_str, entries in calendar.get("slots", {}).get(day.isoformat(), {}).items():
        hour = int(time_str.split(":")[0])
        slot_kind = kind_for_hour(hour)
        if slot_kind is None or (kind and slot_kind != kind):
            continue
        free = max(int(e.get("c", MAX_CAPACITY)) for e in entries)
        if free <= 0:
            continue
        result.append({"time": time_str, "hour": hour, "free": free, "kind": slot_kind})
    return sorted(result, key=lambda s: s["hour"])


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    day = date.fromisoformat(argv[0])
    kind = argv[1] if len(argv) > 1 else None
    calendar = fetch_calendar()
    if not is_open_day(calendar, day):
        print(f"{day.isoformat()} is a closed day (no bookable slots).")
        return 0
    slots = slots_for_day(calendar, day, kind)
    print(json.dumps(slots, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
