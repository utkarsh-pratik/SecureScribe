# 📝 SecureScribe - Your Private AI Note Vault

SecureScribe is a modern, secure, and intelligent note-taking application built with Python and Streamlit. It combines robust security features like end-to-end encryption with powerful AI capabilities, including note summarization, semantic search, and content generation from YouTube videos.
<!--
 ![SecureScribe Screenshot](https://via.placeholder.com/800x450.png?text=SecureScribe+App+Screenshot)
 
*(Replace the placeholder above with a real screenshot of your application)*
-->
---

## ✨ Features

-   **🔐 Secure User Authentication:** Complete login/signup system with password hashing.
-   **🔒 End-to-End Encryption:** All notes are encrypted using the `cryptography` library, ensuring your data is private and secure.
-   **👤 Personalized Profiles:** Users can customize their profiles with a username, bio, and a profile avatar hosted on Cloudinary.
-   **📂 Folder Organization:** Organize your notes into custom folders with rename and delete functionality.
-   **⭐ Favorites System:** Mark your most important notes as favorites for quick access.
-   **🧠 AI-Powered Summarization:** Generate concise summaries of long notes using the OpenRouter API with Mistral-7B.
-   **🔍 Semantic Search:** Find notes based on meaning and context, not just keywords, powered by Sentence-Transformers and FAISS.
-   **🎥 YouTube to Notes:** Paste a YouTube video link to automatically extract the transcript and generate structured notes from it.
-   **📄 PDF Export:** View any note or summary as a PDF directly in your browser.
-   **🚀 Responsive UI:** A clean and fast user interface built with Streamlit, featuring sidebar navigation and interactive widgets.

---

## 🛠️ Tech Stack

-   **Backend & Frontend:** [Python](https://www.python.org/), [Streamlit](https://streamlit.io/)
-   **Database:** [MongoDB](https://www.mongodb.com/) (via `pymongo`)
-   **Encryption:** `cryptography`
-   **AI Models:**
    -   **Summarization:** `mistralai/mistral-7b-instruct` via [OpenRouter](https://openrouter.ai/)
    -   **Semantic Search:** `all-MiniLM-L6-v2` via `sentence-transformers`
    -   **Vector Search:** `faiss-cpu`
-   **Image Hosting:** [Cloudinary](https://cloudinary.com/)
-   **PDF Generation:** `fpdf2`

---

## 🚀 Getting Started

Follow these instructions to get a local copy up and running.

### Prerequisites

-   Python 3.9+
-   A MongoDB Atlas account (or a local MongoDB instance)
-   A Cloudinary account for avatar hosting
-   An OpenRouter API key for note summarization

### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/your-username/securescribe.git
    cd securescribe
    ```

2.  **Create and activate a virtual environment:**
    ```sh
    # For Windows
    python -m venv .venv
    .venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the required packages:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Set up your environment variables:**
    Create a file named `.env` in the root of the project and add your credentials:
    ```env
    # .env file
    MONGO_URI="your_mongodb_connection_string"
    SECRET_KEY="a_strong_jwt_secret_key_for_tokens"
    OPENROUTER_API_KEY="your_openrouter_api_key"
    CLOUDINARY_CLOUD_NAME="your_cloudinary_cloud_name"
    CLOUDINARY_API_KEY="your_cloudinary_api_key"
    CLOUDINARY_API_SECRET="your_cloudinary_api_secret"
    ```

### Running the Application

Once the installation is complete, run the Streamlit app from your terminal:

```sh
streamlit run app.py

