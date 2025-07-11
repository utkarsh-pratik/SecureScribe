import os
import json
import subprocess
import tempfile
from urllib.parse import urlparse, parse_qs
from langdetect import detect
from transformers import pipeline
from youtube_transcript_api import YouTubeTranscriptApi


# Load translation pipeline (many-to-English)
translation_pipeline = pipeline("translation", model="Helsinki-NLP/opus-mt-mul-en")

# Load summarization pipeline
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
    try:
        lang = detect(text)
        if lang == "en":
            return text, lang
        translated = translation_pipeline(text[:4000])[0]["translation_text"]  # Truncate to avoid model limits
        return translated, lang
    except Exception as e:
        return text, "undetected"

def summarize(text):
    return summarization_pipeline(text[:4000])[0]["summary_text"]  # Truncate for long content

def get_transcript(youtube_url):
    # This logic is preserved
    video_id = extract_video_id(youtube_url)
    if not video_id:
        return None, "⚠️ Invalid YouTube URL"

    try:
        # This logic is preserved: it will try to get the transcript in your
        # preferred languages, in the order you specified.
        langs = ["en", "hi", "mr", "bn", "ta", "te", "gu", "kn", "ml"]
        
        # The library fetches the transcript data directly, replacing the subprocess call.
        # The data structure is a list of text segments, just like your original code produced.
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=langs)

        # This logic is preserved: it joins the text segments into a single string.
        # This creates the `full_text` variable exactly as your original code did.
        full_text = " ".join([item['text'] for item in transcript_list]).strip()

        # This logic is preserved
        if not full_text:
            return None, "⚠️ Transcript was empty or unreadable."

        # The final output is identical to your original function's output
        return full_text, None

    except Exception as e:
        # This logic is preserved: it gracefully handles errors.
        return None, f"⚠️ Transcript extraction failed: {str(e)}"

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
