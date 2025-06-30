# note_manager.py
from encryption import encrypt, decrypt
from datetime import datetime
from bson import ObjectId
from db_info import notes_col
import streamlit as st

@st.cache_data(ttl=600) # Cache for 10 minutes
def load_notes(user_id):
    notes = list(notes_col.find({"user_id": ObjectId(user_id)}))
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
                notes_col.replace_one({"_id": note["_id"]}, note)
            else:
                notes_col.insert_one(note)
        return True
    except Exception as e:
        print("Error saving notes:", e)
        return False

def add_note(user_id, title, content, tags, subject, folder=None, favorite=False):
    note = {
        "user_id": ObjectId(user_id),
        "title": title,
        "content": encrypt(content),
        "tags": [t.strip() for t in tags if t.strip()],
        "subject": subject,
        "folder": folder,
        "favorite": favorite,
        "created_at": datetime.now().isoformat()
    }
    result = notes_col.insert_one(note)
    note["id"] = str(result.inserted_id)
    note["content"] = content  # decrypted for in-app use
    return note

def update_notes_after_folder_rename(user_id, old, new):
    notes_col.update_many(
        {"user_id": ObjectId(user_id), "folder": old},
        {"$set": {"folder": new}}
    )

def update_notes_after_folder_delete(user_id, folder_name):
    notes_col.update_many(
        {"user_id": ObjectId(user_id), "folder": folder_name},
        {"$unset": {"folder": ""}}
    )
