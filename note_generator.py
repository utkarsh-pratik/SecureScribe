import os
import requests
from langdetect import detect
from transformers import GPT2TokenizerFast

# Setup
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or "sk-..."  # Replace safely
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}
MODEL = "mistralai/mistral-7b-instruct:free"
MAX_CHUNK_TOKENS = 30000

# Load GPT2 tokenizer (works well for token estimation)
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

def detect_language(text):
    try:
        return detect(text)
    except:
        return "unknown"

def openrouter_chat(prompt):
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(OPENROUTER_BASE_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    elif response.status_code == 400 and "maximum context length" in response.text:
        return "⚠️ Chunk too long. Please shorten your input."
    else:
        return f"⚠️ OpenRouter API error: {response.status_code} - {response.text}"

def chunk_text_by_tokens(text, max_tokens=MAX_CHUNK_TOKENS):
    tokens = tokenizer.encode(text)
    chunks = []

    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i+max_tokens]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)

    return chunks

def convert_to_notes(transcript_text):
    lang = detect_language(transcript_text)
    print(f"\n🌐 Detected Language: {lang}")
    print(f"📄 Transcript Preview:\n{transcript_text[:500]}...\n")

    # Save original transcript
    with open("debug_transcript.txt", "w", encoding="utf-8") as f:
        f.write(transcript_text)

    # Basic validation
    if not transcript_text.strip():
        return "⚠️ Transcript is empty. Cannot generate notes."
    if len(transcript_text.split()) < 50:
        return "⚠️ Transcript is too short to generate meaningful notes."

    # Translate if not in English
    if lang != "en":
        print("🌐 Translating transcript to English in chunks...")
    
        translated_chunks = []
        chunks_to_translate = chunk_text_by_tokens(transcript_text, max_tokens=3000)
    
        for i, chunk in enumerate(chunks_to_translate):
            print(f"🔄 Translating chunk {i+1} of {len(chunks_to_translate)}...")
            prompt = f"Translate the following Hindi or Hinglish transcript into English:\n\n{chunk}"
            translated = openrouter_chat(prompt)
    
            if translated.startswith("⚠️"):
                print(f"⚠️ Skipped translation chunk {i+1}: {translated}")
                continue
            
            translated_chunks.append(translated)
    
        translated_text = "\n\n".join(translated_chunks)
    
        # Save the translated transcript
        with open("translated_transcript.txt", "w", encoding="utf-8") as f:
            f.write(translated_text)
    
        transcript_text = translated_text  # Use translated text for note generation

    # Chunk and summarize
    chunks = chunk_text_by_tokens(transcript_text)
    all_notes = []

    for i, chunk in enumerate(chunks):
        prompt = (
            f"You're a helpful assistant. Read the following transcript chunk and generate detailed, structured, lecture-style notes with headings, bullet points, and key ideas preserved.\n"
            f"Also if problem statement or question is given, then also provide the solution or code in a separate section.\n"
            f"If there is need of any diagram or image to explain the concept, then also provide the link to that image.\n"
            f"Rephrase accurately and organize well:\n\n{chunk}"
        )
        notes = openrouter_chat(prompt)
        if notes.startswith("⚠️"):
            print(f"⚠️ Skipped chunk {i+1} due to error: {notes}")
            continue
        all_notes.append(f"### Notes from Part {i+1}:\n\n{notes}")

    return "\n\n".join(all_notes)
