import os
from instagrapi import Client

# Access username and password from environment variables set in GitHub Actions
username = os.getenv('IG_USERNAME')
password = os.getenv('IG_PASSWORD')

cl = Client()

# Log in using the environment variables
cl.login(username, password)

# Upload Instagram story
cl.photo_upload_to_story("image.jpg", caption="Weekly story via GitHub Actions!")

print("✅ Story posted successfully!")