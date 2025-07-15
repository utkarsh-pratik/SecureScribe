# summarizer.py

import streamlit as st
import requests
import base64
from openai import OpenAI

# --- Constants for models ---
TEXT_MODEL = "mistralai/mistral-7b-instruct:free"
VISION_MODEL = "nousresearch/nous-hermes-2-vision-7b" # A good, free vision model

def summarize_note(content: str) -> str:
    """
    Summarizes a block of text using a text-based LLM.
    This function remains as it was, using your preferred text model.
    """
    if "OPENROUTER_API_KEY" not in st.secrets:
        return "Error: OPENROUTER_API_KEY not found in Streamlit secrets."
    
    api_key = st.secrets["OPENROUTER_API_KEY"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://securescribe.streamlit.app", # Use your app's URL
        "X-Title": "SecureScribe Note Summarizer"
    }

    try:
        # Handle token limit by truncating input
        prompt = f"Summarize this note in a clear and structured way:\n\n{content[:15000]}"

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={
                "model": TEXT_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that summarizes educational notes."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.5
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        if "choices" in data and data["choices"]:
            return data['choices'][0]['message']['content'].strip()
        else:
            return f"Error: API returned an unexpected response: {data}"

    except Exception as e:
        return f"Error during summarization: {str(e)}"

def describe_image(image_bytes: bytes) -> str:
    """
    Sends image bytes to a vision model to get a text description.
    """
    if "OPENROUTER_API_KEY" not in st.secrets:
        return "[Image description failed: API key not configured]"

    try:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=st.secrets["OPENROUTER_API_KEY"],
        )
        
        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image concisely for the purpose of summarizing a document. Focus on key information, data, or objects."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=150,
            timeout=30
        )
        
        if response.choices and response.choices[0].message.content:
            return response.choices[0].message.content.strip()
        else:
            return "[Image description failed: No response from API]"

    except Exception as e:
        print(f"Error describing image: {e}")
        return f"[Image description failed: {e}]"
