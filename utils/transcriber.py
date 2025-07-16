# utils/transcriber.py

import streamlit as st
from deepgram import DeepgramClient, PrerecordedOptions
import yt_dlp
import tempfile
import os
import base64

def transcribe_from_file(uploaded_file, language: str = "auto") -> tuple[str | None, str | None]:
    """
    Transcribes an uploaded audio or video file using the Deepgram API.
    (This function is already correct and remains unchanged.)
    """
    if "DEEPGRAM_API_KEY" not in st.secrets:
        return None, "Error: DEEPGRAM_API_KEY is not configured in secrets."
    try:
        deepgram = DeepgramClient(st.secrets["DEEPGRAM_API_KEY"])
        payload = {"buffer": uploaded_file.getvalue(), "mimetype": uploaded_file.type}
        
        if language == "auto":
            options = PrerecordedOptions(model="nova-2", smart_format=True, detect_language=True)
        else:
            options = PrerecordedOptions(model="nova-2", smart_format=True, language=language)

        response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
        transcript_text = response["results"]["channels"][0]["alternatives"][0]["transcript"]
        
        if not transcript_text:
            return None, "Transcription successful, but the content was empty."
        return transcript_text, None
    except Exception as e:
        return None, f"An error occurred during transcription: {e}"

def transcribe_from_url(url: str, language: str = "auto") -> tuple[str | None, str | None]:
    """
    Extracts a direct media link from any general video URL using yt-dlp with cookies,
    then transcribes it using the Deepgram API.
    """
    if "DEEPGRAM_API_KEY" not in st.secrets:
        return None, "Error: DEEPGRAM_API_KEY is not configured in secrets."
    
    # Cookies are essential for reliably extracting from sites like Dailymotion/YouTube
    if "YOUTUBE_COOKIES_BASE64" not in st.secrets:
        return None, "Error: YOUTUBE_COOKIES_BASE64 secret is missing. It is required for reliable URL extraction."

    cookie_filepath = None
    try:
        # --- Create a temporary cookie file from secrets ---
        decoded_cookies = base64.b64decode(st.secrets["YOUTUBE_COOKIES_BASE64"])
        fd, cookie_filepath = tempfile.mkstemp()
        with os.fdopen(fd, 'wb') as cookie_file:
            cookie_file.write(decoded_cookies)
        # ----------------------------------------------------

        st.info("Extracting direct media link from URL...")
        # --- Add noplaylist and cookiefile options for robustness ---
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'noplaylist': True, # Ignore playlists
            'cookiefile': cookie_filepath, # Use cookies for authentication
        }
        # -----------------------------------------------------------
        
        direct_media_url = None
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'url' in info:
                direct_media_url = info['url']
        
        if not direct_media_url:
            return None, "Error: Could not extract a direct media stream from the provided URL."

        st.info("Sending media stream to transcription service...")
        deepgram = DeepgramClient(st.secrets["DEEPGRAM_API_KEY"])
        source = {"url": direct_media_url}

        if language == "auto":
            options = PrerecordedOptions(model="nova-2", smart_format=True, detect_language=True)
        else:
            options = PrerecordedOptions(model="nova-2", smart_format=True, language=language)

        response = deepgram.listen.prerecorded.v("1").transcribe_url(source, options)
        transcript_text = response["results"]["channels"][0]["alternatives"][0]["transcript"]

        if not transcript_text:
            return None, "Transcription successful, but the content was empty."
        return transcript_text, None

    except Exception as e:
        return None, f"An error occurred during transcription: {e}"
    finally:
        # --- Clean up the temporary cookie file ---
        if cookie_filepath and os.path.exists(cookie_filepath):
            os.remove(cookie_filepath)
        # ------------------------------------------
