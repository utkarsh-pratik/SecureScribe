import os
import json
import subprocess
import tempfile
from urllib.parse import urlparse, parse_qs
from langdetect import detect
from transformers import pipeline

yt_dlp_path = "C:/Program Files/Python310/Scripts/yt-dlp.exe"  # update path


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
    video_id = extract_video_id(youtube_url)
    if not video_id:
        return None, "⚠️ Invalid YouTube URL"

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            langs = ["en", "hi", "mr", "bn", "ta", "te", "gu", "kn", "ml"]
            cmd = [
                yt_dlp_path,
                "--write-auto-sub",
                "--sub-lang", ",".join(langs),
                "--skip-download",
                "--sub-format", "json3",
                "-o", os.path.join(tmpdir, "%(id)s.%(ext)s"),
                youtube_url
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Look for the first available subtitle file
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
