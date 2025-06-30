from db_info import folders_col
from bson import ObjectId
import streamlit as st

@st.cache_data(ttl=600) # Cache for 10 minutes
def load_folders(user_id):
    folders = folders_col.find({"user_id": ObjectId(user_id)})
    return [f["name"] for f in folders]

def save_folders(user_id, folder_list):
    folders_col.delete_many({"user_id": ObjectId(user_id)})
    for name in folder_list:
        folders_col.insert_one({"user_id": ObjectId(user_id), "name": name})

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
    return True
