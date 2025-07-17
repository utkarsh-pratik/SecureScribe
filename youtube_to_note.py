# youtube_to_note.py

import streamlit as st
from transformers import pipeline
from langdetect import detect
import yt_dlp
import tempfile
import os
import base64
import json
from urllib.parse import urlparse, parse_qs

# --- Cached functions to load heavy models on-demand (This part is correct) ---
@st.cache_resource
def get_translation_pipeline():
    """Loads and caches the translation pipeline."""
    return pipeline("translation", model="Helsinki-NLP/opus-mt-mul-en")

@st.cache_resource
def get_summarization_pipeline():
    """Loads and caches the summarization pipeline."""
    return pipeline("summarization", model="google/flan-t5-large")

# --- Other functions (extract_video_id, translate_to_english, summarize) remain correct ---
def extract_video_id(youtube_url):
    query = urlparse(youtube_url)
    if query.hostname == "youtu.be":
        return query.path[1:]
    if query.hostname in ("www.youtube.com", "youtube.com"):
        if query.path == "/watch":
            return parse_qs(query.query).get("v", [None])[0]
        elif query.path.startswith(("/embed/", "/v/")):
            return query.path.split("/")[2]
    return None

def translate_to_english(text):
    try:
        lang = detect(text)
        if lang == "en":
            return text, lang
        translation_pipeline = get_translation_pipeline()
        translated = translation_pipeline(text[:4000])[0]["translation_text"]
        return translated, lang
    except Exception as e:
        return text, f"undetected ({e})"

def summarize(text):
    summarization_pipeline = get_summarization_pipeline()
    return summarization_pipeline(text[:4000])[0]["summary_text"]

# --- THE CORRECTED get_transcript FUNCTION ---
def get_transcript(youtube_url):
    """
    Downloads a transcript from a YouTube URL efficiently, trying languages
    one by one to avoid rate limiting.
    """
    video_id = extract_video_id(youtube_url)
    if not video_id:
        return None, "⚠️ Invalid YouTube URL"
    
    clean_youtube_url = f"https://www.youtube.com/watch?v={video_id}"

    if "YOUTUBE_COOKIES_BASE64" not in st.secrets:
        return None, "Error: YOUTUBE_COOKIES_BASE64 secret is missing."

    cookie_filepath = None
    try:
        decoded_cookies = base64.b64decode(st.secrets["YOUTUBE_COOKIES_BASE64"])
        fd_cookie, cookie_filepath = tempfile.mkstemp()
        with os.fdopen(fd_cookie, 'wb') as cookie_file:
            cookie_file.write(decoded_cookies)

        # List of preferred languages in order of priority
        preferred_langs = ["en", "hi", "mr", "bn", "ta", "te", "gu", "kn", "ml"]

        # Loop through preferred languages and try to download one at a time
        for lang in preferred_langs:
            with tempfile.TemporaryDirectory() as tmpdir:
                ydl_opts = {
                    'writeautomaticsub': True,
                    'subtitleslangs': [lang], # <-- Try only ONE language at a time
                    'subtitlesformat': 'json3',
                    'skip_download': True,
                    'outtmpl': os.path.join(tmpdir, '%(id)s'),
                    'noplaylist': True,
                    'cookiefile': cookie_filepath,
                    'quiet': True,
                }
                
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.extract_info(clean_youtube_url, download=True)

                    # Check if the subtitle file was successfully downloaded
                    subtitle_path = os.path.join(tmpdir, f"{video_id}.{lang}.json3")
                    if os.path.exists(subtitle_path):
                        with open(subtitle_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        
                        transcript = []
                        for event in data.get("events", []):
                            segs = event.get("segs")
                            if segs:
                                text = "".join(seg["utf8"] for seg in segs).strip()
                                transcript.append(text)

                        full_text = " ".join(transcript).strip()
                        if full_text:
                            return full_text, None # Success! Return the transcript.
                
                except Exception as e:
                    # This might happen if a specific language subtitle is not available.
                    # We can ignore it and let the loop try the next language.
                    print(f"Could not fetch subtitle for language '{lang}': {e}")
                    continue
        
        # If the loop finishes without finding any subtitles
        return None, "⚠️ No readable transcript found for any of the preferred languages."

    except Exception as e:
        return None, f"⚠️ Transcript extraction failed: {str(e)}"
    finally:
        if cookie_filepath and os.path.exists(cookie_filepath):
            os.remove(cookie_filepath)

# --- The generate_notes_from_youtube function remains correct ---
def generate_notes_from_youtube(youtube_url):
    transcript, error = get_transcript(youtube_url)
    if error:
        return None, error

    translated_text, detected_lang = translate_to_english(transcript)
    summary = summarize(translated_text)

    return {
        "original_language": detected_lang,
        "transcript": transcript,
        "translated_text": translated_text,
        "summary": summary
    }, None
