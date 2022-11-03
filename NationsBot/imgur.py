import os
from logger import *

from dotenv import load_dotenv
from imgurpython import ImgurClient

def upload(filepath):
    client = ImgurClient(os.getenv('IMGUR_CLIENT_ID'), os.getenv('IMGUR_CLIENT_SECRET'))

    link = client.upload_from_path(filepath)['link']

    logInfo(f"Uploaded image from {filepath} to link: {link}")
    return link
