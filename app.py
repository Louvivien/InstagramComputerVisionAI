import streamlit as st
import os
import cv2
import base64
from openai import OpenAI
from instagrapi import Client
from dotenv import load_dotenv

# Function to download videos from Instagram
def download_videos(target_profile, username, password):
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
            st.write(f"Downloaded video path: {video_path}")
            video_paths.append(video_path)

    return video_paths

# Function to extract frames from a video
def extract_frames(video_path, max_frames=5):
    if not os.path.exists(video_path):
        st.write(f"Video file not found: {video_path}")
        return []

    st.write(f"Opening video file: {video_path}")
    absolute_video_path = os.path.abspath(video_path)
    video = cv2.VideoCapture(absolute_video_path)

    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = total_frames // max_frames

    base64_frames = []
    for i in range(max_frames):
        frame_number = i * frame_interval
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

        success, frame = video.read()
        if not success:
            break

        _, buffer = cv2.imencode(".jpg", frame)
        base64_frames.append(base64.b64encode(buffer).decode("utf-8"))

    video.release()
    return base64_frames

# Function to generate description using OpenAI
def generate_description(frames, openai_api_key):
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
        st.write(f"An error occurred: {e}")
        return None

# Function to generate voice narration
def generate_voice(description, filename, openai_api_key):
    client = OpenAI(api_key=openai_api_key)
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=description,
    )

    if not os.path.exists('mp3'):
        os.makedirs('mp3')

    mp3_path = os.path.join('mp3', f"{filename}.mp3")
    response.stream_to_file(mp3_path)
    st.write(f"Narration saved for file: {filename}")
    return mp3_path

# Streamlit app
def main():
    st.title("Instagram Video Computer Vision")

    # Environment variables input
    st.sidebar.header("Environment Variables")
    insta_username = st.sidebar.text_input("Instagram Username")
    insta_password = st.sidebar.text_input("Instagram Password", type="password")
    openai_api_key = st.sidebar.text_input("OpenAI API Key")

    # Target profile input
    target_profile = st.text_input("Enter the Instagram profile to analyze:", value="apple")

    if st.button("Analyze Videos"):
        video_files = download_videos(target_profile, insta_username, insta_password)
        for video_file in video_files:
            frames = extract_frames(video_file, max_frames=5)
            description = generate_description(frames, openai_api_key)
            st.write(description)

            video_filename = os.path.splitext(os.path.basename(video_file))[0]
            mp3_path = generate_voice(description, video_filename, openai_api_key)

            # Display MP3 file
            if os.path.exists(mp3_path):
                st.audio(mp3_path)

if __name__ == "__main__":
    main()
