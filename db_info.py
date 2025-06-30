# db.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URL")
client = MongoClient(MONGO_URI)
db = client["securescribe_db"]

# Collections
notes_col = db["notes"]
folders_col = db["folders"]
users_col = db["users"]
