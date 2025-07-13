# note_manager.py
from encryption import encrypt, decrypt
from datetime import datetime
from bson import ObjectId
from db.mongo import get_notes_collection
import streamlit as st

@st.cache_data(ttl=600) # Cache for 10 minutes
def load_notes(user_id):
    notes = list(get_notes_collection().find({"user_id": ObjectId(user_id)}))
    for note in notes:
        note["id"] = str(note["_id"])
        note["content"] = decrypt(note["content"])
    return notes

def save_notes(user_id, notes):
    try:
        for note in notes:
            note["user_id"] = ObjectId(user_id)
            note["content"] = encrypt(note["content"])
            if "_id" in note:
                note["_id"] = ObjectId(note["_id"])
                get_notes_collection().replace_one({"_id": note["_id"]}, note)
            else:
                get_notes_collection().insert_one(note)
        st.cache_data.clear() # <-- ADD THIS
        return True
    except Exception as e:
        print("Error saving notes:", e)
        return False

def add_note(user_id, title, content, tags, subject, folder=None, favorite=False, attachment_url=None):
    note = {
        "user_id": ObjectId(user_id),
        "title": title,
        "content": content,
        "tags": [t.strip() for t in tags if t.strip()],
        "subject": subject,
        "folder": folder,
        "attachment_url": attachment_url,
        "favorite": favorite,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    # Create a copy of the note for database insertion
    db_note = note.copy()
    
    # Encrypt the content only for the database version
    if content:
        db_note["content"] = encrypt(content)
    
    # Insert the encrypted version into the database
    result = get_notes_collection().insert_one(db_note)
    
    note["id"] = str(result.inserted_id)

    st.cache_data.clear() # Clear the cache after adding a note
    return note

def update_notes_after_folder_rename(user_id, old, new):
    get_notes_collection().update_many(
        {"user_id": ObjectId(user_id), "folder": old},
        {"$set": {"folder": new}}
    )

def update_notes_after_folder_delete(user_id, folder_name):
    get_notes_collection().update_many(
        {"user_id": ObjectId(user_id), "folder": folder_name},
        {"$unset": {"folder": ""}}
    )
