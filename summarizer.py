import os
import requests
from dotenv import load_dotenv
from utils.secrets_manager import get_secret # Import the helper


load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "HTTP-Referer": "https://openrouter.ai",  # Required
    "X-Title": "SecureScribe Note Summarizer"
}

MODEL = "mistralai/mistral-7b-instruct:free"

def summarize_note(content):
    try:
        prompt = f"Summarize this note in a clear and structured way:\n\n{content[:4000]}"

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=HEADERS,
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that summarizes educational notes."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.5
            },
            timeout=20
        )

        data = response.json()
        return data['choices'][0]['message']['content'].strip()

    except Exception as e:
        return f"Error: {str(e)}"
