

from instagrapi import Client
import os
from dotenv import load_dotenv

# Load .env file
root_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(root_dir, '.env')
load_dotenv(dotenv_path)

username = os.getenv('INSTA_USERNAME')
password = os.getenv('INSTA_PASSWORD')



def download_videos(target_profile):
    cl = Client()

    cl.login(username, password)

    user_id = cl.user_id_from_username(target_profile)
    medias = cl.user_medias(user_id, amount=5)

    # Check if the 'videos' folder exists, and create it if it doesn't
    if not os.path.exists('videos'):
        os.makedirs('videos')

    for media in medias:
        if media.media_type == 2:  # 2 represents a video
            cl.video_download(media.pk, folder='./videos')

if __name__ == "__main__":

    target_profile = 'apple'

    download_videos(target_profile)

