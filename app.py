import os
import cv2
import base64
from openai import OpenAI
from instagrapi import Client
from dotenv import load_dotenv

# Load environment variables
root_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(root_dir, '.env')
load_dotenv(dotenv_path)

username = os.getenv('INSTA_USERNAME')
password = os.getenv('INSTA_PASSWORD')
openai_api_key = os.getenv('OPENAI_API_KEY')

def download_videos(target_profile):
    cl = Client()
    cl.login(username, password)

    user_id = cl.user_id_from_username(target_profile)
    medias = cl.user_medias(user_id, amount=5)

    video_paths = []
    if not os.path.exists('videos'):
        os.makedirs('videos')

    for media in medias:
        if media.media_type == 2:  # 2 represents a video
            video_path = cl.video_download(media.pk, folder='./videos')
            print(f"Downloaded video path: {video_path}")  # Debugging line
            video_paths.append(video_path)


    return video_paths

def extract_frames(video_path, frame_skip=10, max_frames=5):
    if not os.path.exists(video_path):
        print(f"Video file not found: {video_path}")
        return []
    """
    Extracts frames from a video, skipping a set number of frames.

    :param video_path: Path to the video file.
    :param frame_skip: Number of frames to skip. Default is 10.
    :return: List of base64-encoded frames.
    """
    print(f"Opening video file: {video_path}")
    absolute_video_path = os.path.abspath(video_path)
    video = cv2.VideoCapture(absolute_video_path)
    base64_frames = []
    frame_count = 0

    added_frames = 0


    while video.isOpened() and added_frames < max_frames:
        success, frame = video.read()
        if not success:
            break

        if frame_count % frame_skip == 0:
            _, buffer = cv2.imencode(".jpg", frame)
            base64_frames.append(base64.b64encode(buffer).decode("utf-8"))
            added_frames += 1

        frame_count += 1

    video.release()
    return base64_frames

def generate_description(frames):
    client = OpenAI(api_key=openai_api_key)
    prompt_messages = [
        {
            "role": "user",
            "content": [
                "These are frames of a video. Describe what is happening in the video.",
                *map(lambda x: {"image": x}, frames),
            ],
        },
    ]

    try:
        chat_completion = client.chat.completions.create(
            messages=prompt_messages,
            model="gpt-4-vision-preview",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    target_profile = 'apple'
    video_files = download_videos(target_profile)

    for video_file in video_files:
        frames = extract_frames(video_file, frame_skip=10, max_frames=5)  # Adjust max_frames as needed
        description = generate_description(frames)
        print(description)
