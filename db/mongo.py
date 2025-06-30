# db/mongo.py
from pymongo import MongoClient
import streamlit as st
import os

def get_mongo_client():
    """
    Establishes a connection to MongoDB.
    Uses Streamlit secrets when deployed, otherwise uses local .env file.
    """
    # Check if running in Streamlit Cloud
    if hasattr(st, 'secrets'):
        # Use Streamlit secrets
        mongo_uri = st.secrets["MONGO_URI"]
    else:
        # Fallback for local development using .env file
        from dotenv import load_dotenv
        load_dotenv()
        mongo_uri = os.getenv("MONGO_URI")

    if not mongo_uri:
        raise ValueError("MONGO_URI not found. Please set it in your Streamlit secrets or .env file.")

    client = MongoClient(mongo_uri)
    return client

# Initialize the client
client = get_mongo_client()
db = client.get_database("securescribe")

def get_users_collection():
    return db.get_collection("users")

def get_notes_collection():
    return db.get_collection("notes")

def get_folders_collection():
    return db.get_collection("folders")
