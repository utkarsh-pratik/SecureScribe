# 📝 SecureScribe - Your Private AI-Powered Note Vault

**SecureScribe** is a modern, secure, and intelligent note-taking application designed to be your personal knowledge engine. It goes beyond simple text storage by leveraging multiple AI models to automatically capture, transcribe, summarize, and synthesize information from various sources. The standout feature is a personalized AI Tutor that can answer questions based on the user's own repository of notes.

**Live Demo:** [Link to your deployed Streamlit App]

---

## ✨ Key Features

SecureScribe is built with a robust set of features that make it a powerful tool for students, researchers, and professionals.

### Core Note-Taking & Security
*   **🔒 Secure User Authentication:** Full user registration and login system handled by the `auth/` module.
*   **🔐 End-to-End Encryption:** All note content is encrypted using AES via `encryption.py` before being stored in the database, ensuring user privacy.
*   **🗂️ Folder & Tagging System:** Organize notes with nested folders and searchable tags for efficient management, handled by `storage.py`.
*   **⭐ Favorites:** Mark important notes for quick access.
*   **📄 PDF Export:** Export any note into a beautifully formatted PDF document using `pdf_exporter.py`.

### 🤖 AI-Powered Content Creation & Import
*   **🌐 From Website URL:** Provide any website URL to automatically scrape its main content (`utils/web_scraper.py`) and generate structured notes (`note_generator.py`).
*   **📺 From YouTube:** Paste a YouTube link to fetch the video's transcript (`youtube_to_note.py`) and convert it into detailed, lecture-style notes.
*   **🎙️ From Audio/Video (Both File Upload & URL):** Upload an audio/video file or provide a public URL. The app uses the Deepgram API (`utils/transcriber.py`) to get a transcript, which is then converted into notes.

### 🧠 Advanced AI Analysis & Synthesis
*   **📄 Multimodal PDF Summarization:** Upload a PDF containing both text and images. The application parses the text, uses a vision model to describe the images, and generates a comprehensive summary based on all content (`summarizer.py` and `note_manager.py`).
*   **💡 Automatic Note Summarization:** Generate a concise summary for any note with a single click.
*   **🔍 Semantic Search:** A powerful search engine (`semantic_search.py`) that understands the *meaning* behind your query, not just keywords, to find the most relevant notes. Powered by Sentence-Transformers and FAISS.
*   **✨ **(Standout Feature)** Personalized AI Tutor:** A floating chat widget that allows you to "chat with your notes." Ask questions in natural language, and the AI will synthesize answers based on the knowledge contained within your personal note repository, using a Retrieval-Augmented Generation (RAG) pipeline (`rag_pipeline.py`).

---

## 🛠️ Tech Stack

This project leverages a modern stack to deliver a responsive and intelligent user experience.

*   **Frontend:** [Streamlit](https://streamlit.io/)
*   **Backend / Business Logic:** Python
*   **Database:** [MongoDB](https://www.mongodb.com/) (via `pymongo` in `db/mongo.py`)
*   **AI & Machine Learning:**
    *   **LLM Orchestration:** [OpenRouter API](https://openrouter.ai/) (for models like Mistral-7B)
    *   **Speech-to-Text:** [Deepgram API](https://deepgram.com/)
    *   **Local Transformers:** [Hugging Face Transformers](https://huggingface.co/docs/transformers/index) for on-demand translation and summarization pipelines.
    *   **Vector Embeddings:** `sentence-transformers` for semantic search and RAG.
*   **Core Libraries:** `PyMuPDF` (PDF parsing), `yt-dlp` (media downloading), `BeautifulSoup4` (web scraping), `scikit-learn` (cosine similarity).
*   **Security:** `pycryptodome` for AES encryption.

---

## 🚀 Setup and Local Installation

To run this project locally, follow these steps:

1.  **Prerequisites:**
    *   Python 3.9+
    *   MongoDB instance (local or on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas))
    *   A Cloudinary account for avatar hosting
    *   An OpenRouter API key for note summarization

2.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/securescribe.git
    cd securescribe
    ```

3.  **Set up a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure Environment Variables:**
    Create a `.streamlit/secrets.toml` file in the root of the project and add your API keys and database credentials:
    ```toml
    # MongoDB Credentials
    MONGO_URI = "your_mongodb_connection_string"
    DB_NAME = "securescribe_db"

    # Encryption Key (must be 16, 24, or 32 bytes long)
    ENCRYPTION_KEY = "your_secret_encryption_key_here"

    # API Keys
    OPENROUTER_API_KEY = "your_openrouter_api_key"
    DEEPGRAM_API_KEY = "your_deepgram_api_key"

    # YouTube Cookies (for reliable transcript fetching)
    YOUTUBE_COOKIES_BASE64 = "your_base64_encoded_cookies_file"
    ```

6.  **Run the Application:**
    ```bash
    streamlit run app.py
    ```
