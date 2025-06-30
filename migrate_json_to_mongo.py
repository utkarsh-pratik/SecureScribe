# migrate_json_to_mongo.py
import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from encryption import decrypt
from datetime import datetime

# Load environment variables
load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
NOTES_PATH = "data/notes.json"
USER_ID = "default"  # You can change this to your actual user ID (e.g. email)

def migrate_notes():
    if not os.path.exists(NOTES_PATH):
        print("❌ notes.json not found.")
        return

    # Load notes
    with open(NOTES_PATH, "r", encoding="utf-8") as f:
        raw_notes = json.load(f)

    # Decrypt content
    decrypted_notes = []
    for note in raw_notes:
        try:
            content = decrypt(note["content"])
        except Exception as e:
            print(f"⚠️ Failed to decrypt note {note.get('id')}: {e}")
            continue

        decrypted_notes.append({
            "user_id": USER_ID,
            "id": note.get("id", 0),
            "title": note.get("title", ""),
            "content": content,
            "summary": note.get("summary", ""),
            "tags": note.get("tags", []),
            "subject": note.get("subject", ""),
            "folder": note.get("folder"),
            "favorite": note.get("favorite", False),
            "created_at": note.get("created_at", datetime.now().isoformat())
        })

    # Insert into MongoDB
    try:
        client = MongoClient(MONGODB_URL)
        db = client.securescribe
        result = db.notes.insert_many(decrypted_notes)
        print(f"✅ Migrated {len(result.inserted_ids)} notes to MongoDB for user '{USER_ID}'")
    except Exception as e:
        print(f"❌ MongoDB error: {e}")

if __name__ == "__main__":
    migrate_notes()
