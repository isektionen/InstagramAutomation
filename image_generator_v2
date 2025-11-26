from PIL import Image, ImageDraw, ImageFont
from gcsa.google_calendar import GoogleCalendar
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
import os
from dotenv import load_dotenv
import locale

# -----------------------------
# CONFIGURATION
# -----------------------------
WIDTH = 1080
HEIGHT = 1920
BACKGROUND_COLOR = (30, 30, 60)      # top of gradient
GRADIENT_COLOR = (80, 0, 120)        # bottom of gradient
FONT_PATH = "arial.ttf"               # change to any .ttf on your system
TITLE_FONT_SIZE = 100
EVENT_FONT_SIZE = 60
OUTPUT_FILE = "weekly_events.png"
PADDING = 50
LINE_SPACING = 20
CHUNK_SIZE = 6  # max events per image
# -----------------------------

# Set locale for weekday names
locale.setlocale(locale.LC_TIME, 'sv_SE.UTF-8')

# Load environment variables
load_dotenv()

TOKEN = os.environ["TOKEN"]
REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
SCOPES = [os.environ["SCOPES"]]
TOKEN_URI = os.environ["TOKEN_URI"]

AUTH_TOKEN = Credentials(
    token=TOKEN,
    refresh_token=REFRESH_TOKEN,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scopes=SCOPES,
    token_uri=TOKEN_URI
)


def fetch_events():
    """Fetch events for the next 7 days from Google Calendar"""
    calendar = GoogleCalendar(
        'iare.nu_pre97odp8btuq3u2a9i6u3fnbc@group.calendar.google.com',
        credentials=AUTH_TOKEN
    )
    events = calendar.get_events(
        time_min=datetime.now(),
        time_max=datetime.now() + timedelta(days=7),
        order_by="startTime",
        single_events=True
    )
    event_list = list(events)
    # Split into chunks if needed
    sub_lists = [event_list[i:i + CHUNK_SIZE] for i in range(0, len(event_list), CHUNK_SIZE)]
    return sub_lists


def create_gradient_background(width, height, color1, color2):
    """Creates a vertical gradient background"""
    img = Image.new("RGB", (width, height), color1)
    draw = ImageDraw.Draw(img)
    for y in range(height):
        ratio = y / (height - 1)
        new_color = (
            int(color1[0] * (1 - ratio) + color2[0] * ratio),
            int(color1[1] * (1 - ratio) + color2[1] * ratio),
            int(color1[2] * (1 - ratio) + color2[2] * ratio),
        )
        draw.line([(0, y), (width, y)], fill=new_color)
    return img


def generate_event_image(events):
    """Generate an image with title and structured events"""
    img = create_gradient_background(WIDTH, HEIGHT, BACKGROUND_COLOR, GRADIENT_COLOR)
    draw = ImageDraw.Draw(img)

    # Load fonts
    try:
        title_font = ImageFont.truetype(FONT_PATH, TITLE_FONT_SIZE)
        event_font = ImageFont.truetype(FONT_PATH, EVENT_FONT_SIZE)
    except:
        print("Warning: Font not found. Using default font.")
        title_font = ImageFont.load_default()
        event_font = ImageFont.load_default()

    # Draw title
    title_text = "Veckan på I"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    x_title = (WIDTH - title_width) / 2
    y = PADDING
    draw.text((x_title, y), title_text, fill=(255, 255, 255), font=title_font)
    y += TITLE_FONT_SIZE + 2 * LINE_SPACING

    # Draw events
    for i, event in enumerate(events, start=1):
        dt = datetime.fromisoformat(event.start.isoformat())
        date_str = f"{dt.strftime('%A')} {dt.day}/{dt.month}".capitalize()
        time_str = dt.strftime("%H:%M")
        description = f"{event.summary} {time_str}"

        # Draw date
        draw.text((PADDING, y), date_str, fill=(255, 255, 255), font=event_font)
        y += EVENT_FONT_SIZE + LINE_SPACING // 2

        # Draw description
        draw.text((PADDING + 50, y), description, fill=(255, 255, 255), font=event_font)
        y += EVENT_FONT_SIZE + LINE_SPACING

    img.save(OUTPUT_FILE)
    print(f"✅ Image saved as {OUTPUT_FILE}")


if __name__ == "__main__":
    event_chunks = fetch_events()
    for chunk in event_chunks:
        generate_event_image(chunk)
