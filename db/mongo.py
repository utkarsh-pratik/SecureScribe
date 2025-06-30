# db/mongo.py
from pymongo import MongoClient
import streamlit as st
import os

def get_mongo_client():
    """
    Establishes a connection to MongoDB using a single, consistent secret name.
    Uses Streamlit secrets when deployed, otherwise uses local .env file.
    """
    mongo_uri = None

    # Check for the secret in Streamlit's secrets manager first (for deployment)
    if hasattr(st, 'secrets') and "MONGO_URI" in st.secrets:
        mongo_uri = st.secrets["MONGO_URI"]
    else:
        # Fallback for local development using the .env file
        from dotenv import load_dotenv
        load_dotenv()
        mongo_uri = os.getenv("MONGO_URI")

    if not mongo_uri:
        st.error("MongoDB connection URL not found. Please set MONGO_URI in your Streamlit secrets.")
        raise ValueError("MONGO_URI not found. Set it in Streamlit secrets or your local .env file.")

    try:
        client = MongoClient(mongo_uri)
        # Ping the server to verify the connection is successful
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"🔥 Failed to connect to MongoDB. Please check your MONGO_URI secret. Error: {e}")
        raise ConnectionError("Could not connect to MongoDB") from e

# --- Initialize the client and export collection-getter functions ---
client = get_mongo_client()
db = client.get_database("securescribe") # Using a consistent database name

def get_users_collection():
    """Returns the 'users' collection object."""
    return db.get_collection("users")

def get_notes_collection():
    """Returns the 'notes' collection object."""
    return db.get_collection("notes")

def get_folders_collection():
    """Returns the 'folders' collection object."""
    return db.get_collection("folders")
