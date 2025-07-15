# utils/transcriber.py

import streamlit as st
from deepgram import DeepgramClient, PrerecordedOptions

def transcribe_from_file(uploaded_file, language: str = "auto") -> tuple[str | None, str | None]:
    """
    Transcribes an uploaded file. If language is 'auto', lets Deepgram detect it.
    """
    if "DEEPGRAM_API_KEY" not in st.secrets:
        return None, "Error: DEEPGRAM_API_KEY is not configured in secrets."

    try:
        deepgram = DeepgramClient(st.secrets["DEEPGRAM_API_KEY"])
        payload = {"buffer": uploaded_file.getvalue(), "mimetype": uploaded_file.type}
        
        # --- MODIFIED: Conditionally set the language ---
        if language == "auto":
            options = PrerecordedOptions(model="nova-2", smart_format=True, detect_language=True)
        else:
            options = PrerecordedOptions(model="nova-2", smart_format=True, language=language)
        # ------------------------------------------------

        response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
        transcript_text = response["results"]["channels"][0]["alternatives"][0]["transcript"]
        
        if not transcript_text:
            return None, "Transcription successful, but the content was empty."
        return transcript_text, None

    except Exception as e:
        return None, f"An error occurred during transcription: {e}"

def transcribe_from_url(url: str, language: str = "auto") -> tuple[str | None, str | None]:
    """
    Transcribes from a URL. If language is 'auto', lets Deepgram detect it.
    """
    if "DEEPGRAM_API_KEY" not in st.secrets:
        return None, "Error: DEEPGRAM_API_KEY is not configured in secrets."

    try:
        deepgram = DeepgramClient(st.secrets["DEEPGRAM_API_KEY"])
        source = {"url": url}

        # --- MODIFIED: Conditionally set the language ---
        if language == "auto":
            options = PrerecordedOptions(model="nova-2", smart_format=True, detect_language=True)
        else:
            options = PrerecordedOptions(model="nova-2", smart_format=True, language=language)
        # ------------------------------------------------

        response = deepgram.listen.prerecorded.v("1").transcribe_url(source, options)
        transcript_text = response["results"]["channels"][0]["alternatives"][0]["transcript"]

        if not transcript_text:
            return None, "Transcription successful, but the content was empty."
        return transcript_text, None

    except Exception as e:
        return None, f"An error occurred during transcription: {e}"
