import requests
from ics import Calendar
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from jinja2 import Template
from playwright.sync_api import sync_playwright
import json
import os

CACHE_FILE = "events_cache.json"

OUTPUT_FILE = "weekly_events.png"

if os.path.exists(CACHE_FILE):
    print(f"Loading events from {CACHE_FILE}")
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        events_by_day = json.load(f)
else:
    # 1. Define the URL
    url = "https://calendar.google.com/calendar/ical/iare.nu_pre97odp8btuq3u2a9i6u3fnbc@group.calendar.google.com/public/basic.ics"

    # 2. Fetch the data
    response = requests.get(url)
    response.raise_for_status()  # Check for errors

    # 3. Parse the calendar
    c = Calendar(response.text)

    # 4. Calculate this week's Monday and Sunday
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    sunday = sunday.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Make datetime objects timezone-aware (Stockholm timezone)
    stockholm_tz = ZoneInfo("Europe/Stockholm")
    monday = monday.replace(tzinfo=stockholm_tz)
    sunday = sunday.replace(tzinfo=stockholm_tz)

    # 5. Filter and organize events by day
    this_week_events = [e for e in c.events if monday <= e.begin.datetime <= sunday]

    # Organize events by weekday
    events_by_day = {
        "monday": [],
        "tuesday": [],
        "wednesday": [],
        "thursday": [],
        "friday": [],
        "saturday": [],
        "sunday": [],
    }

    weekday_map = {
        0: "monday",
        1: "tuesday",
        2: "wednesday",
        3: "thursday",
        4: "friday",
        5: "saturday",
        6: "sunday",
    }

    for event in this_week_events:
        weekday = event.begin.datetime.weekday()
        if weekday in weekday_map:
            events_by_day[weekday_map[weekday]].append(
                {
                    "name": event.name,
                    "start_time": event.begin.datetime.strftime("%H:%M"),
                    "end_time": event.end.datetime.strftime("%H:%M"),
                }
            )

    # Sort events by start time for each day
    for day in events_by_day:
        events_by_day[day].sort(key=lambda x: x["start_time"])

    print(f"Found {len(this_week_events)} events this week (Monday to Sunday)\n")

    # Save to cache
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(events_by_day, f, ensure_ascii=False, indent=4)

# Calculate dynamic font size
num_active_days = sum(1 for events in events_by_day.values() if events)
total_events = sum(len(events) for events in events_by_day.values())

# Constants for layout calculation
AVAILABLE_HEIGHT = (
    1770  # 1920 - title (90) - title margin (20) - container padding (40)
)
DAY_OVERHEAD = 80  # margins (10), padding (20), day name header (~50)
EVENT_OVERHEAD = 18  # margins (8), padding (10) per event
FONT_MULTIPLIER = (
    2.4  # Height factor per pixel of font size (2 lines * 1.2 line-height)
)

if total_events > 0:
    # Calculate available space for events content
    space_for_events = (
        AVAILABLE_HEIGHT
        - (num_active_days * DAY_OVERHEAD)
        - (total_events * EVENT_OVERHEAD)
    )

    # Calculate max font size
    calculated_font_size = space_for_events / (total_events * FONT_MULTIPLIER)

    # Clamp font size
    font_size = max(20, min(70, int(calculated_font_size)))
else:
    font_size = 70

print(
    f"Calculated font size: {font_size}px (Active days: {num_active_days}, Total events: {total_events})"
)

# 6. Load and render the Jinja template
with open("template.html", "r", encoding="utf-8") as f:
    template_content = f.read()

template = Template(template_content)
html_output = template.render(events=events_by_day, font_size=font_size)

# 7. Generate PNG using Playwright with higher resolution
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(
        viewport={"width": 1080, "height": 1920}, device_scale_factor=2
    )
    page.set_content(html_output)
    page.screenshot(path=OUTPUT_FILE, full_page=False)
    browser.close()

print("PNG generated:" + OUTPUT_FILE)
