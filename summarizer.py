import streamlit as st
import requests

# This can remain a global constant
MODEL = "mistralai/mistral-7b-instruct:free"

def summarize_note(content):
    # 1. Check for the secret and get the API key. This is required for deployment.
    if "OPENROUTER_API_KEY" not in st.secrets:
        return "Error: OPENROUTER_API_KEY not found in Streamlit secrets."
    
    api_key = st.secrets["OPENROUTER_API_KEY"]

    # 2. Define headers inside the function using the key from secrets.
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://your-app-name.streamlit.app",  # Recommended: Use your app's URL
        "X-Title": "SecureScribe Note Summarizer"
    }

    try:
        prompt = f"Summarize this note in a clear and structured way:\n\n{content[:4000]}"

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
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
        response.raise_for_status()  # Raise an exception for bad status codes (like 401 Unauthorized)

        data = response.json()

        # 3. Safely access the response to prevent crashes.
        if "choices" in data and data["choices"]:
            return data['choices'][0]['message']['content'].strip()
        else:
            return f"Error: API returned an unexpected response: {data}"

    except Exception as e:
        return f"Error: {str(e)}"
    
