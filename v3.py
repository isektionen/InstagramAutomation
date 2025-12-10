import requests
import os
import random
import base64
from ics import Calendar
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from jinja2 import Template
from playwright.sync_api import sync_playwright
from instagrapi import Client

IG_USERNAME = os.environ["BURNER_USERNAME"]
IG_PASSWORD = os.environ["BURNER_PASSWORD"]

OUTPUT_FILE = "weekly_events.png"

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

# 6. Load background image
imgs_dir = "imgs"
background_image = None
if os.path.exists(imgs_dir):
    images = [
        f for f in os.listdir(imgs_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    if images:
        selected_image = random.choice(images)
        with open(os.path.join(imgs_dir, selected_image), "rb") as img_file:
            b64_string = base64.b64encode(img_file.read()).decode("utf-8")
            ext = os.path.splitext(selected_image)[1].lower().replace(".", "")
            if ext == "jpg":
                ext = "jpeg"
            background_image = f"data:image/{ext};base64,{b64_string}"
            print(f"Using background image: {selected_image}")

# 7. Load and render the Jinja template
with open("template.html", "r", encoding="utf-8") as f:
    template_content = f.read()

template = Template(template_content)
html_output = template.render(events=events_by_day, background_image=background_image)

# 8. Generate PNG using Playwright with higher resolution
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(
        viewport={"width": 1080, "height": 1920}, device_scale_factor=2
    )
    page.set_content(html_output)
    page.screenshot(path=OUTPUT_FILE, full_page=False)
    browser.close()

print("PNG generated: " + OUTPUT_FILE)

def post_story(image_path):
    settings_path = "insta_settings.json"
    cl = Client()
    cl.load_settings(settings_path)
    cl.login(IG_USERNAME, IG_PASSWORD)
    cl.photo_upload_to_story(image_path, caption="Veckan på I")
    print("✅ Story posted successfully!")
post_story(OUTPUT_FILE)

def post_story(image_path):
    settings_path = "insta_settings.json"
    cl = Client()
    cl.load_settings(settings_path)
    cl.login(IG_USERNAME, IG_PASSWORD)
    cl.photo_upload_to_story(image_path, caption="Veckan på I")
    print("✅ Story posted successfully!")
