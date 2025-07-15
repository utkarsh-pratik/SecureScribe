# note_manager.py
from encryption import encrypt, decrypt
from datetime import datetime
from bson import ObjectId
from db.mongo import get_notes_collection
import streamlit as st
import requests
from utils.multimodal_parser import parse_pdf_for_text_and_images
from summarizer import summarize_note, describe_image # Add describe_image

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


def generate_summary_for_note(note: dict) -> str:
    """
    Generates a summary for a note, handling text content or attachments with images.
    Manages token limits to prevent errors with large documents.
    """
    # Define a safe character limit for the context (leaving room for prompts and response)
    # A heuristic of 4 chars/token for a 4k model context window = ~16000 chars. We'll use 15000.
    CONTEXT_CHAR_LIMIT = 15000

    text_to_summarize = ""

    # 1. Prioritize the note's direct text content if it exists
    if note.get("content"):
        text_to_summarize = note["content"]
    
    # 2. If no text content, process the attachment
    elif note.get("attachment_url"):
        try:
            url = note["attachment_url"]
            
            # Handle non-PDF files gracefully
            if not url.lower().endswith(('.pdf', '.txt')):
                 return "Error: Attachment is not a PDF or TXT file."

            st.info(f"Downloading attachment from Cloudinary...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            if url.lower().endswith(".txt"):
                text_to_summarize = response.content.decode('utf-8')
            else: # It's a PDF
                st.info("Parsing PDF for text and images...")
                parsed_blocks = parse_pdf_for_text_and_images(response.content)
                
                enriched_content_parts = []
                current_char_count = 0

                # Build the enriched content while respecting the character limit
                for block in parsed_blocks:
                    if current_char_count >= CONTEXT_CHAR_LIMIT:
                        enriched_content_parts.append("\n\n[... Document content truncated due to length ...]")
                        break # Stop processing further blocks

                    if block['type'] == 'text':
                        block_text = block['content'] + " "
                        enriched_content_parts.append(block_text)
                        current_char_count += len(block_text)
                    
                    elif block['type'] == 'image':
                        st.info("Describing an image from the document...")
                        description = describe_image(block['content'])
                        image_text = f"\n\n[Image Description: {description}]\n\n"
                        enriched_content_parts.append(image_text)
                        current_char_count += len(image_text)
                
                text_to_summarize = "".join(enriched_content_parts)

        except Exception as e:
            return f"Error processing attachment: {e}"
    
    # 3. If we have text to summarize, call the final summarizer model
    if text_to_summarize:
        st.info("Generating final summary...")
        return summarize_note(text_to_summarize)
    else:
        return "Error: Note has no content or attachment to summarize."

