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
    try:
        cl.login(username, password)
    
    except Exception as e:
        if "ProxyAddressIsBlocked" in str(e):
            st.error("Your IP is blocked by Instagram for API operations, please use another IP")
            return []
        else:
            st.error(f"An error occurred during login: {e}")
            return []

    try:
        user_id = cl.user_id_from_username(target_profile)
        medias = cl.user_medias(user_id, amount=5)
    except Exception as e:
        st.error(f"An error occurred while fetching media: {e}")
        return []

    video_paths = []
    if not os.path.exists('videos'):
        os.makedirs('videos')

    for media in medias:
        if media.media_type == 2:  # 2 represents a video
            try:
                video_path = cl.video_download(media.pk, folder='./videos')
                st.write(f"Downloaded video path: {video_path}")
                video_paths.append(video_path)
            except Exception as e:
                st.error(f"An error occurred while downloading video: {e}")

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

# Function to delete video and MP3 files
def delete_files(video_path, mp3_path):
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                st.write(f"Deleted video file: {video_path}")

            if os.path.exists(mp3_path):
                os.remove(mp3_path)
                st.write(f"Deleted MP3 file: {mp3_path}")
        except Exception as e:
            st.error(f"An error occurred while deleting files: {e}")



# Streamlit app
def main():
    st.title("Instagram Video Computer Vision")

    # Initialize session state
    if 'video_mp3_paths' not in st.session_state:
        st.session_state['video_mp3_paths'] = []

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
            # Convert PosixPath to string and display the video player
            st.video(str(video_file))

            frames = extract_frames(video_file, max_frames=5)
            description = generate_description(frames, openai_api_key)
            st.write(description)

            video_filename = os.path.splitext(os.path.basename(video_file))[0]
            mp3_path = generate_voice(description, video_filename, openai_api_key)

            # Display MP3 file and update session state
            if os.path.exists(mp3_path):
                st.audio(mp3_path)
                st.session_state['video_mp3_paths'].append((video_file, mp3_path))

    # Button to delete all video and MP3 files
    if st.button("Delete All Videos and MP3s"):
        for video_path, mp3_path in st.session_state['video_mp3_paths']:
            delete_files(video_path, mp3_path)
        st.success("Deleted all video and MP3 files")
        st.session_state['video_mp3_paths'] = []  # Reset the session state


if __name__ == "__main__":
    main()
