# utils/transcriber.py

import streamlit as st
from deepgram import DeepgramClient, PrerecordedOptions
import yt_dlp

def transcribe_from_file(uploaded_file, language: str = "auto") -> tuple[str | None, str | None]:
    """
    Transcribes an uploaded audio or video file using the Deepgram API.
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
    Extracts a direct media link from a general video URL using yt-dlp,
    then transcribes it using the Deepgram API.
    """
    if "DEEPGRAM_API_KEY" not in st.secrets:
        return None, "Error: DEEPGRAM_API_KEY is not configured in secrets."

    try:
        # --- NEW: Use yt-dlp to get the direct media URL ---
        st.info("Extracting direct media link from URL...")
        ydl_opts = {
            'format': 'bestaudio/best', # Get the best audio-only format
            'quiet': True,             # Suppress console output
        }
        
        direct_media_url = None
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'url' in info:
                direct_media_url = info['url']
        
        if not direct_media_url:
            return None, "Error: Could not extract a direct media stream from the provided URL."
        # ----------------------------------------------------

        st.info("Sending media stream to transcription service...")
        deepgram = DeepgramClient(st.secrets["DEEPGRAM_API_KEY"])
        source = {"url": direct_media_url} # Pass the *direct* URL to Deepgram

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
    
