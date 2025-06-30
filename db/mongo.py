# db/mongo.py

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGODB_URL")
DB_NAME = "securescribe"

# Singleton client and DB
_client = None
_db = None

def get_client():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URL)
    return _client

def get_db():
    global _db
    if _db is None:
        _db = get_client()[DB_NAME]
    return _db

def get_users_collection():
    return get_db()["users"]

def get_notes_collection():
    return get_db()["notes"]

def get_folders_collection():
    return get_db()["folders"]
