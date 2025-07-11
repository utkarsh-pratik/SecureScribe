# youtube_to_note.py

import streamlit as st
from urllib.parse import urlparse, parse_qs
from langdetect import detect
from transformers import pipeline
import googleapiclient.discovery
import re

# --- Your existing models and functions (unchanged) ---
translation_pipeline = pipeline("translation", model="Helsinki-NLP/opus-mt-mul-en")
summarization_pipeline = pipeline("summarization", model="google/flan-t5-large")

def extract_video_id(youtube_url):
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
    # ... (This function remains exactly the same)
    try:
        lang = detect(text)
        if lang == "en":
            return text, lang
        translated = translation_pipeline(text[:4000])[0]["translation_text"]
        return translated, lang
    except Exception as e:
        return text, "undetected"

def summarize(text):
    # ... (This function remains exactly the same)
    return summarization_pipeline(text[:4000])[0]["summary_text"]

# --- NEW: Function to parse SRT format from the API ---
def parse_srt(srt_text: str) -> str:
    """Parses an SRT formatted string and extracts only the text lines."""
    lines = srt_text.splitlines()
    text_lines = [line for line in lines if not line.isdigit() and '-->' not in line and line.strip() != '']
    return " ".join(text_lines).strip()

# --- REWRITTEN: get_transcript function using the official YouTube API ---
def get_transcript(youtube_url: str) -> tuple[str | None, str | None]:
    video_id = extract_video_id(youtube_url)
    if not video_id:
        return None, "⚠️ Invalid YouTube URL"

    if "YOUTUBE_API_KEY" not in st.secrets:
        return None, "⚠️ YOUTUBE_API_KEY not found in secrets."

    try:
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=st.secrets["YOUTUBE_API_KEY"]
        )

        # 1. Get the list of available captions for the video
        request = youtube.captions().list(part="snippet", videoId=video_id)
        response = request.execute()

        # 2. Find a caption track that matches your preferred languages
        caption_id = None
        preferred_langs = ["en", "hi", "mr", "bn", "ta", "te", "gu", "kn", "ml"]
        available_tracks = response.get("items", [])
        
        for lang in preferred_langs:
            for track in available_tracks:
                if track['snippet']['language'] == lang:
                    caption_id = track['id']
                    break
            if caption_id:
                break

        if not caption_id:
            return None, "⚠️ No suitable transcript found for the preferred languages."

        # 3. Download the caption track content
        caption_request = youtube.captions().download(id=caption_id, tfmt="srt")
        srt_transcript = caption_request.execute()

        # 4. Parse the SRT content to get clean text
        full_text = parse_srt(srt_transcript)

        if not full_text:
            return None, "⚠️ Transcript was empty or unreadable."

        return full_text, None

    except Exception as e:
        return None, f"⚠️ API Error: {str(e)}"

# --- Your existing main function (unchanged) ---
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
