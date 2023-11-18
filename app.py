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




def extract_frames(video_path, max_frames=5):
    if not os.path.exists(video_path):
        print(f"Video file not found: {video_path}")
        return []

    print(f"Opening video file: {video_path}")
    absolute_video_path = os.path.abspath(video_path)
    video = cv2.VideoCapture(absolute_video_path)

    # Calculate the total number of frames and the interval for frame extraction
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = total_frames // max_frames

    base64_frames = []
    for i in range(max_frames):
        # Set the video position to the frame number
        frame_number = i * frame_interval
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

        success, frame = video.read()
        if not success:
            break

        _, buffer = cv2.imencode(".jpg", frame)
        base64_frames.append(base64.b64encode(buffer).decode("utf-8"))

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
            max_tokens=500  

        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
    
    
def generate_voice(description):
    
    client = OpenAI()    
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input= description,
    )
    response.stream_to_file("output2.mp3")

if __name__ == "__main__":
    target_profile = 'apple'
    # video_files = download_videos(target_profile)

    # for video_file in video_files:
    #     frames = extract_frames(video_file, max_frames=5)  # Adjust max_frames as needed
    #     description = generate_description(frames)
    #     print(description)
    generate_voice("Hello I am inamulrehman, I am a hackathon enthusiast.")