# db_info.py
import os
from pymongo import MongoClient
import streamlit as st
from dotenv import load_dotenv
from utils.secrets_manager import get_secret # Import the helper


def get_mongo_client():
    """
    Establishes a connection to MongoDB.
    It correctly uses Streamlit secrets when deployed and falls back to a local
    .env file for local development.
    """
    mongo_uri = get_secret("MONGODB_URL")

    # This block runs when the app is deployed on Streamlit Community Cloud
    if hasattr(st, 'secrets'):
        mongo_uri = st.secrets.get("MONGODB_URL")

    # This block runs for local development if secrets aren't found
    if not mongo_uri:
        load_dotenv()
        mongo_uri = os.getenv("MONGODB_URL")

    # If no URI is found in either place, raise an error
    if not mongo_uri:
        st.error("MongoDB connection URL not found. Please set MONGODB_URL in your Streamlit secrets.")
        raise ValueError("MONGODB_URL not found. Set it in Streamlit secrets or your local .env file.")

    try:
        client = MongoClient(mongo_uri)
        # Ping the server to check the connection
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"🔥 Failed to connect to MongoDB. Please check your MONGODB_URL secret. Error: {e}")
        raise ConnectionError("Could not connect to MongoDB") from e

# --- Initialize the client and export collections ---
client = get_mongo_client()
db = client["securescribe_db"]

# Collections that other files can import
notes_col = db["notes"]
folders_col = db["folders"]
users_col = db["users"]
