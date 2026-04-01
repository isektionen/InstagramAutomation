import requests
import os
import random
import base64
import logging
from ics import Calendar
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from jinja2 import Template
from playwright.sync_api import sync_playwright
from instagrapi import Client
from instagrapi.exceptions import LoginRequired

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IG_USERNAME = os.environ["IG_USERNAME"]
IG_PASSWORD = os.environ["IG_PASSWORD"]

OUTPUT_FILE = "weekly_events.png"
SESSION_FILE = "insta_settings.json"

# ============================================================
# 1. Fetch calendar
# ============================================================
url = "https://calendar.google.com/calendar/ical/iare.nu_pre97odp8btuq3u2a9i6u3fnbc@group.calendar.google.com/public/basic.ics"

response = requests.get(url)
response.raise_for_status()

c = Calendar(response.text)

# ============================================================
# 2. Calculate this week's Monday–Sunday
# ============================================================
today = datetime.now()
monday = today - timedelta(days=today.weekday())
sunday = monday + timedelta(days=6)
monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
sunday = sunday.replace(hour=23, minute=59, second=59, microsecond=999999)

stockholm_tz = ZoneInfo("Europe/Stockholm")
monday = monday.replace(tzinfo=stockholm_tz)
sunday = sunday.replace(tzinfo=stockholm_tz)

# ============================================================
# 3. Filter and organize events by day
# ============================================================
this_week_events = [e for e in c.events if monday <= e.begin.datetime <= sunday]

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

for day in events_by_day:
    events_by_day[day].sort(key=lambda x: x["start_time"])

print(f"Found {len(this_week_events)} events this week (Monday to Sunday)\n")

# ============================================================
# 4. Load background image
# ============================================================
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

# ============================================================
# 5. Render HTML template
# ============================================================
with open("template.html", "r", encoding="utf-8") as f:
    template_content = f.read()

template = Template(template_content)
html_output = template.render(events=events_by_day, background_image=background_image)

# ============================================================
# 6. Generate PNG with Playwright
# ============================================================
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(
        viewport={"width": 1080, "height": 1920}, device_scale_factor=2
    )
    page.set_content(html_output)
    page.screenshot(path=OUTPUT_FILE, full_page=False)
    browser.close()

print("PNG generated: " + OUTPUT_FILE)

# ============================================================
# 7. Instagram login with session reuse
# ============================================================
def login_user():
    """
    Robust login following instagrapi best practices:
    1. Try loading saved session
    2. Validate with a test request
    3. Fall back to fresh login if session is dead
    4. Always save updated session
    """
    cl = Client()
    cl.delay_range = [1, 3]

    session_exists = os.path.exists(SESSION_FILE)

    if session_exists:
        # Attempt 1: reuse saved session
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(IG_USERNAME, IG_PASSWORD)
            # Validate session with a test request
            cl.get_timeline_feed()
            logger.info("✅ Logged in with saved session")
            return cl
        except LoginRequired:
            logger.warning("⚠️ Saved session expired, trying fresh login...")
        except Exception as e:
            logger.warning(f"⚠️ Session load failed: {e}")

    # Attempt 2: fresh login
    try:
        cl = Client()
        cl.delay_range = [1, 3]
        cl.login(IG_USERNAME, IG_PASSWORD)
        cl.dump_settings(SESSION_FILE)
        logger.info("✅ Fresh login successful, session saved")
        return cl
    except Exception as e:
        logger.error(f"❌ Login failed completely: {e}")
        raise


def post_story(image_path):
    highlight_title = "Veckan på I"

    cl = login_user()

    story = cl.photo_upload_to_story(image_path, caption="Veckan på I")
    print("✅ Story posted successfully!")

    # Find existing highlight by title
    highlights = cl.user_highlights(cl.user_id)
    highlight_id = None

    for h in highlights:
        if h.title == highlight_title:
            highlight_id = h.pk
            break

    if not highlight_id:
        raise Exception(f'❌ Highlight "{highlight_title}" not found')

    # Add story to highlight
    cl.highlight_add_stories(
        highlight_id=highlight_id,
        story_ids=[story.pk],
    )
    print(f'⭐ Story added to highlight "{highlight_title}"')

    # Save updated session for next run
    cl.dump_settings(SESSION_FILE)
    logger.info("💾 Updated session saved")


post_story(OUTPUT_FILE)
