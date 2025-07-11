from db.mongo import get_folders_collection
from bson import ObjectId
import streamlit as st

@st.cache_data(ttl=600) # Cache for 10 minutes
def load_folders(user_id):
    folders = get_folders_collection().find({"user_id": ObjectId(user_id)})
    return [f["name"] for f in folders]

def save_folders(user_id, folder_list):
    get_folders_collection().delete_many({"user_id": ObjectId(user_id)})
    for name in folder_list:
        get_folders_collection().insert_one({"user_id": ObjectId(user_id), "name": name})
    st.cache_data.clear() # <-- ADD THIS

def rename_folder(user_id, old, new):
    folders = load_folders(user_id)
    if old in folders:
        folders[folders.index(old)] = new
        save_folders(user_id, folders)
    return True

def delete_folder(user_id, name):
    folders = load_folders(user_id)
    if name in folders:
        folders.remove(name)
        save_folders(user_id, folders)
    st.cache_data.clear() # <-- ADD THIS
    return True
