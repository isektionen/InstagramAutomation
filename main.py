from gcsa.google_calendar import GoogleCalendar
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from google.oauth2.credentials import Credentials
import locale
from datetime import datetime
import requests
from instagrapi import Client


locale.setlocale(locale.LC_TIME, 'sv_SE.UTF-8')

load_dotenv()

TOKEN = os.environ["TOKEN"]
REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
SCOPES = [os.environ["SCOPES"]]
TOKEN_URI = os.environ["TOKEN_URI"]
API_KEY = os.environ["API_KEY"]
TEMPLATE_ID = os.environ["TEMPLATE_ID"]
IG_USERNAME = os.environ["IG_USERNAME"]
IG_PASSWORD = os.environ["IG_PASSWORD"]



AUTH_TOKEN = Credentials(
    token=TOKEN,
    refresh_token=REFRESH_TOKEN,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scopes=SCOPES,
    token_uri=TOKEN_URI
)

def main():
    event_list = []
    calendar =  GoogleCalendar('iare.nu_pre97odp8btuq3u2a9i6u3fnbc@group.calendar.google.com', credentials=AUTH_TOKEN)
    events = calendar.get_events(time_min=datetime.now(), time_max=datetime.now() + timedelta(days=7),  order_by="startTime", single_events=True)

    for event in events:
        event_list.append(event)

    chunk_size = 6
    sub_lists = [event_list[i:i + chunk_size] for i in range(0, len(event_list), chunk_size)]

    for sub_list in sub_lists:
        event_dict = {}
        i = 1
        for event in sub_list:
            dt = datetime.fromisoformat(event.start.isoformat())
            date_str = f"{dt.strftime('%A')} {dt.day}/{dt.month}"
            time_str = dt.strftime("%H:%M")
            event_dict[f"event_{i}_date"] = date_str
            event_dict[f"event_{i}_description"] = event.summary + " " + time_str
            i += 1
        create_story(event_dict)
        

def create_story(event_dict):
    data = {}
    for key, value in event_dict.items():
        if key.endswith("_date"):
            data[f"{key}.text"] = value
            data[f"{key}.opacity"] = "100"
        elif key.endswith("_description"):
            data[f"{key}.text"] = value
            data[f"{key}.opacity"] = "100"

    payload = {
    "template": f"{TEMPLATE_ID}",
    "data": data
    }

    response = requests.post(
    "https://get.renderform.io/api/v2/render",
    json=payload,
    headers={
        "X-API-KEY": f"{API_KEY}",
        "Content-Type": "application/json"
        }
    )

    print(response.status_code)

    if(response.status_code == 200):
        image_url = response.json().get("href")
        image_path = "weekly_story.jpg"
        img_response = requests.get(image_url)
        with open(image_path, "wb") as img_file:
            img_file.write(img_response.content)
        post_story(image_path)
    
def post_story(image_path):

    cl = Client()
    cl.load_settings("insta_settings.json")
    cl.login(IG_USERNAME, IG_PASSWORD)
    cl.photo_upload_to_story(image_path, caption="Veckan på I")
    print("✅ Story posted successfully!")

if __name__ == '__main__':
    main()
