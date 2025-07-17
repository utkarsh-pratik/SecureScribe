# youtube_to_note.py

import streamlit as st
from transformers import pipeline
from langdetect import detect
import yt_dlp
import tempfile
import os
import base64
from urllib.parse import urlparse, parse_qs

# --- NEW: Cached functions to load heavy models on-demand ---

@st.cache_resource
def get_translation_pipeline():
    """Loads and caches the translation pipeline."""
    return pipeline("translation", model="Helsinki-NLP/opus-mt-mul-en")

@st.cache_resource
def get_summarization_pipeline():
    """Loads and caches the summarization pipeline."""
    return pipeline("summarization", model="google/flan-t5-large")

# -------------------------------------------------------------

def extract_video_id(youtube_url):
    # This function remains unchanged
    query = urlparse(youtube_url)
    if query.hostname == "youtu.be":
        return query.path[1:]
    if query.hostname in ("www.youtube.com", "youtube.com"):
        if query.path == "/watch":
            return parse_qs(query.query).get("v", [None])[0]
        elif query.path.startswith("/embed/") or query.path.startswith("/v/"):
            return query.path.split("/")[2]
    return None

def translate_to_english(text):
    """Translates text to English if it's not already."""
    try:
        lang = detect(text)
        if lang == "en":
            return text, lang
        
        # Get the cached pipeline
        translation_pipeline = get_translation_pipeline()
        translated = translation_pipeline(text[:4000])[0]["translation_text"]
        return translated, lang
    except Exception as e:
        return text, f"undetected ({e})"

def summarize(text):
    """Summarizes a given block of text."""
    # Get the cached pipeline
    summarization_pipeline = get_summarization_pipeline()
    return summarization_pipeline(text[:4000])[0]["summary_text"]

def get_transcript(youtube_url):
    """
    Downloads a transcript from a YouTube URL using yt-dlp.
    (This function is already correct and remains unchanged.)
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

        with tempfile.TemporaryDirectory() as tmpdir:
            langs = ["en", "hi", "mr", "bn", "ta", "te", "gu", "kn", "ml"]
            audio_output_template = os.path.join(tmpdir, 'downloaded_audio.%(ext)s')
            
            ydl_opts = {
                'writeautomaticsub': True,
                'subtitleslangs': langs,
                'subtitlesformat': 'json3',
                'skip_download': True,
                'outtmpl': audio_output_template,
                'noplaylist': True,
                'cookiefile': cookie_filepath,
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(clean_youtube_url, download=True)

            subtitle_file = None
            for lang in langs:
                path = os.path.join(tmpdir, f"{video_id}.{lang}.json3")
                if os.path.exists(path):
                    subtitle_file = path
                    break
            
            if not subtitle_file:
                return None, "⚠️ No readable transcript found (captions disabled or unavailable)."

            with open(subtitle_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            transcript = []
            for event in data.get("events", []):
                segs = event.get("segs")
                if segs:
                    text = "".join(seg["utf8"] for seg in segs).strip()
                    transcript.append(text)

            full_text = " ".join(transcript).strip()
            if not full_text:
                return None, "⚠️ Transcript was empty or unreadable."

            return full_text, None

    except Exception as e:
        return None, f"⚠️ Transcript extraction failed: {str(e)}"
    finally:
        if cookie_filepath and os.path.exists(cookie_filepath):
            os.remove(cookie_filepath)

def generate_notes_from_youtube(youtube_url):
    """
    Orchestrates the process of getting a transcript, translating, and summarizing.
    (This function remains unchanged.)
    """
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
