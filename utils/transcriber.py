# utils/transcriber.py

import streamlit as st
from deepgram import DeepgramClient, PrerecordedOptions, ClientOptionsFromEnv
import yt_dlp
import tempfile
import os
import base64
import mimetypes

def transcribe_from_file(uploaded_file, language: str = "auto") -> tuple[str | None, str | None]:
    """
    Transcribes an uploaded audio or video file using the Deepgram API.
    """
    if "DEEPGRAM_API_KEY" not in st.secrets:
        return None, "Error: DEEPGRAM_API_KEY is not configured in secrets."
    try:
        # --- FIX: Configure client with a longer timeout ---
        config = ClientOptionsFromEnv(timeout=300) # 5-minute timeout
        deepgram = DeepgramClient(st.secrets["DEEPGRAM_API_KEY"], config)
        # -------------------------------------------------
        
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
    Downloads audio from a general video URL using yt-dlp to a temporary file,
    then transcribes the downloaded file using the Deepgram API.
    """
    if "DEEPGRAM_API_KEY" not in st.secrets:
        return None, "Error: DEEPGRAM_API_KEY is not configured in secrets."
    if "YOUTUBE_COOKIES_BASE64" not in st.secrets:
        return None, "Error: YOUTUBE_COOKIES_BASE64 secret is missing for reliable URL extraction."

    cookie_filepath = None
    audio_output_path = None
    try:
        # Create a temporary cookie file for yt-dlp
        decoded_cookies = base64.b64decode(st.secrets["YOUTUBE_COOKIES_BASE64"])
        fd_cookie, cookie_filepath = tempfile.mkstemp()
        with os.fdopen(fd_cookie, 'wb') as cookie_file:
            cookie_file.write(decoded_cookies)

        # Create a temporary directory to download the audio file into
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_output_template = os.path.join(tmpdir, 'downloaded_audio.%(ext)s')

            st.info("Extracting and downloading audio from URL...")
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': audio_output_template,
                'noplaylist': True,
                'cookiefile': cookie_filepath,
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                audio_output_path = ydl.prepare_filename(info)

            if not audio_output_path or not os.path.exists(audio_output_path):
                return None, "Error: Failed to locate downloaded audio file."

            st.info("Sending downloaded audio to transcription service...")
            # --- FIX: Configure client with a longer timeout ---
            config = ClientOptionsFromEnv(timeout=300) # 5-minute timeout
            deepgram = DeepgramClient(st.secrets["DEEPGRAM_API_KEY"], config)
            # -------------------------------------------------

            with open(audio_output_path, 'rb') as audio_file:
                audio_bytes = audio_file.read()

            mimetype, _ = mimetypes.guess_type(audio_output_path)
            payload = {"buffer": audio_bytes, "mimetype": mimetype or 'application/octet-stream'}
            
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
    finally:
        if cookie_filepath and os.path.exists(cookie_filepath):
            os.remove(cookie_filepath)
