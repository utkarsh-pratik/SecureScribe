import streamlit as st
from datetime import datetime
from note_manager import load_notes, add_note, save_notes, update_notes_after_folder_rename, update_notes_after_folder_delete
from summarizer import summarize_note
from pdf_exporter import generate_pdf
from semantic_search import build_index, semantic_search
from youtube_to_note import get_transcript
from note_generator import convert_to_notes
from storage import load_folders, save_folders
import json
import os
from auth.user_manager import signup_user, login_user
from auth.auth_manager import create_access_token # Make sure this is imported
from routes.user_profile import user_profile_page
import base64

st.set_page_config(page_title="SecureScribe", layout="wide")

# --- SESSION STATE INITIALIZATION ---
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "active_page" not in st.session_state:
    st.session_state.active_page = "View Notes"

# --- DEBUGGING: Print current token status on each run ---
print(f"SCRIPT RUN: Token is {'None' if st.session_state.token is None else 'Exists'}")

# --- AUTHENTICATION GATE ---
if not st.session_state.token:
    st.title("🔐 SecureScribe")
    
    col1, col2 = st.columns(2)

    # --- LOGIN FORM ---
    with col1:
        with st.form("login_form"):
            st.subheader("Login")
            login_email = st.text_input("📧 Email", key="login_email")
            login_password = st.text_input("🔑 Password", type="password", key="login_password")
            login_submitted = st.form_submit_button("Login")

            if login_submitted:
                print("LOGIN ATTEMPT: Submitted login form.")
                success, user_data = login_user(login_email, login_password)
                if success:
                    # Add this line to convert the _id to a string before using it.
                    user_data["_id"] = str(user_data["_id"])
                    # -----------------------------------------
                    print("LOGIN SUCCESS: Setting token and user.")
                    st.session_state.token = create_access_token(data={"sub": user_data["_id"]})
                    st.session_state.user = user_data
                    st.rerun()
                else:
                    print(f"LOGIN FAILED: {user_data}")
                    st.error(user_data)

    # --- SIGNUP FORM ---
    with col2:
        with st.form("signup_form"):
            st.subheader("Sign Up")
            signup_name = st.text_input("👤 Name", key="signup_name")
            signup_email = st.text_input("📧 Email", key="signup_email")
            signup_password = st.text_input("🔑 Password", type="password", key="signup_password")
            signup_submitted = st.form_submit_button("Sign Up")

            if signup_submitted:
                print("SIGNUP ATTEMPT: Submitted signup form.")
                success, message = signup_user(signup_name, signup_email, signup_password)
                if success:
                    st.success(message)
                    st.info("You can now log in.")
                else:
                    st.error(message)
    
    st.stop() # Stop execution here if not logged in


# --- IF LOGGED IN ---
user = st.session_state["user"]
token = st.session_state["token"]
user_id = user["_id"]

st.title(f"📝 SecureScribe - Welcome, {user.get('name', 'User')}")

# --- Sidebar Profile Display ---

# CSS to make the image round and centered
st.sidebar.markdown("""
<style>
.profile-img img {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    object-fit: cover;
    display: block;
    margin-left: auto;
    margin-right: auto;
}
</style>
""", unsafe_allow_html=True)

# Get the user's avatar URL, providing a default if it doesn't exist
default_avatar = "https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y"
avatar_url = user.get("avatar_url", default_avatar)

# Display the avatar, username, and email
st.sidebar.markdown(f'<div class="profile-img"><img src="{avatar_url}" alt="Avatar"></div>', unsafe_allow_html=True)
st.sidebar.markdown(f"<h4 style='text-align: center;'>{user.get('name', 'User')}</h4>", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='text-align: center; color: grey;'>{user.get('email')}</p>", unsafe_allow_html=True)


st.sidebar.title("Navigation")

# Initialize the active page in session state if it doesn't exist
if "active_page" not in st.session_state:
    st.session_state.active_page = "View Notes" # Set a default page

# When a button is clicked, it updates the active_page in the session state
if st.sidebar.button("✍️ Create Note"):
    st.session_state.active_page = "Create Note"
    st.rerun()

if st.sidebar.button("📚 View Notes"):
    st.session_state.active_page = "View Notes"
    st.rerun()

if st.sidebar.button("📥 YouTube to Note"):
    st.session_state.active_page = "YouTube to Note"
    st.rerun()

if st.sidebar.button("👤 Profile"):
    st.session_state.active_page = "Profile"
    st.rerun()

st.sidebar.markdown("---")

# Add logout button in sidebar
if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.rerun()


user_email = st.session_state.get("user_email", "default@example.com")

# Add this function to fix existing notes
# def fix_existing_notes():
#     """Add missing favorite field to existing notes"""
#     notes = load_notes()
#     updated = False
#     for note in notes:
#         if 'favorite' not in note:
#             note['favorite'] = False
#             updated = True
#     if updated:
#         save_notes(notes)
#     return notes


# ----------------------------- CREATE NOTE -----------------------------
if st.session_state.active_page == "Create Note":
    st.subheader("✍️ Create a New Note")
    title = st.text_input("Title")
    content = st.text_area("Note Content", height=300)
    tags = st.text_input("Tags (comma-separated)")
    subject = st.text_input("Subject")
    folder = st.selectbox("Folder (optional)", [""] + load_folders(user["_id"]))
    is_fav = st.checkbox("⭐ Mark as Favorite")

    if st.button("Save Note"):
        if title and content:
            note = add_note(user["_id"], title, content, tags.split(","), subject, folder or None, favorite=is_fav)
            st.success(f"Note '{note['title']}' saved!")
        else:
            st.warning("⚠️ Title and content are required.")

# ----------------------------- VIEW NOTES (Corrected Version) -----------------------------
elif st.session_state.active_page == "View Notes":
    st.subheader("📚 Your Notes")

    # This helper function creates the link to view a PDF in a new tab
    def get_pdf_display_link(pdf_buffer, link_text="View PDF in New Tab"):
        """Generates an HTML link to display a PDF in a new tab."""
        pdf_bytes = pdf_buffer.getvalue()
        b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        return f'<a href="data:application/pdf;base64,{b64_pdf}" target="_blank" style="text-decoration: none; color: #007BFF; font-weight: bold;">{link_text}</a>'

    # --- Load Data ---

    all_notes = load_notes(user["_id"])
    all_folders = load_folders(user["_id"])

    # --- Folder Management ---
    st.markdown("### 📂 Manage Folders")
    with st.expander("➕ Create New Folder"):
        new_folder_name = st.text_input("New folder name", key="new_folder_input")
        if st.button("Add Folder"):
            if new_folder_name and new_folder_name not in all_folders:
                all_folders.append(new_folder_name)
                save_folders(user["_id"], all_folders)
                st.success(f"Folder '{new_folder_name}' added!")
                st.rerun()
            elif not new_folder_name:
                st.warning("Folder name cannot be empty.")
            else:
                st.warning(f"Folder '{new_folder_name}' already exists.")

    # Display folder list
    for folder in all_folders:
        folder_notes = [n for n in all_notes if n.get("folder") == folder]
        count = len(folder_notes)
        
        # Check if this specific folder is in rename or delete mode
        is_renaming = st.session_state.get(f"rename_mode_{folder}", False)
        is_deleting = st.session_state.get("folder_to_delete") == folder

        # Main folder row with toggle, rename, delete buttons
        if not is_renaming and not is_deleting:
            col1, col2, col3 = st.columns([0.8, 0.1, 0.1])
            with col1:
                expand_icon = '▼' if st.session_state.get(f"folder_expanded_{folder}", False) else '▶'
                if st.button(f"{expand_icon} 📁 {folder} ({count})", key=f"toggle_{folder}"):
                    st.session_state[f"folder_expanded_{folder}"] = not st.session_state.get(f"folder_expanded_{folder}", False)
            with col2:
                if st.button("✏️", key=f"edit_{folder}", help="Rename folder"):
                    st.session_state[f"rename_mode_{folder}"] = True
                    st.rerun()
            with col3:
                if st.button("🗑️", key=f"del_{folder}", help="Delete folder"):
                    st.session_state["folder_to_delete"] = folder
                    st.rerun()

        # --- Confirmation Dialogs ---
        # Display RENAME confirmation UI only for the selected folder
        if is_renaming:
            st.info(f"Renaming folder: **{folder}**")
            new_name = st.text_input("New name", value=folder, key=f"new_name_{folder}")
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                if st.button("✅ Confirm", key=f"confirm_rename_{folder}"):
                    if new_name and new_name != folder:
                        update_notes_after_folder_rename(user["_id"], folder, new_name)
                        all_folders[all_folders.index(folder)] = new_name
                        save_folders(user["_id"], all_folders)
                    del st.session_state[f"rename_mode_{folder}"]
                    st.rerun()
            with r_col2:
                if st.button("❌ Cancel", key=f"cancel_rename_{folder}"):
                    del st.session_state[f"rename_mode_{folder}"]
                    st.rerun()



        if is_deleting:
            st.warning(f"Delete **'{folder}'**? Notes inside will be un-categorized.")
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                if st.button("✅ Yes, Delete"):
                    update_notes_after_folder_delete(user["_id"], folder)
                    all_folders.remove(folder)
                    save_folders(user["_id"], all_folders)
                    del st.session_state["folder_to_delete"]
                    st.rerun()
            with d_col2:
                if st.button("❌ No, Cancel"):
                    del st.session_state["folder_to_delete"]
                    st.rerun()

        # Display the list of notes if the folder is expanded
        if st.session_state.get(f"folder_expanded_{folder}", False) and not is_renaming and not is_deleting:
            if folder_notes:
                for note in folder_notes:
                    fav_icon = "⭐" if note.get("favorite") else ""
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;📄 {note['title']} {fav_icon}")
            else:
                st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;*No notes in this folder.*")
        st.markdown("---") # Separator for each folder item

    # Filters
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        selected_folder_filter = st.selectbox("Filter by Folder", ["All"] + all_folders)
    with filter_col2:
        show_fav_only = st.checkbox("⭐ Show Only Favorites")

    # Filter notes with explicit boolean checking
    notes_to_display = all_notes.copy()
    if selected_folder_filter != "All":
        notes_to_display = [n for n in notes_to_display if n.get("folder") == selected_folder_filter]
    if show_fav_only:
        notes_to_display = [n for n in notes_to_display if n.get("favorite") is True]


    if not notes_to_display:
        if show_fav_only:
            st.info("No favorite notes found. Click the ☆ icon next to any note to mark it as favorite!")
        else:
            st.info("No notes found.")
    else:
        # 🔍 Semantic Search
        st.markdown("## 🔍 Semantic Search")
        try:
            # Create a mapping from note content to note title for easy lookup later
            content_to_title_map = {note['content']: note['title'] for note in notes_to_display}

            # Build the search index from the content of the notes to be displayed
            index, embeddings, texts = build_index(notes_to_display)

            query = st.text_input("Search your notes")

            if query:
                # Get the search results
                results = semantic_search(query, index, texts)

                # Sort the results by score in descending order (highest score first)
                results.sort(key=lambda item: item[1], reverse=True)

                st.markdown("### 🔎 Results:")
                if not results:
                    st.info("No relevant notes found for your query.")
                else:
                    # Display each result with its title and score
                    for i, (text_content, score) in enumerate(results, 1):
                        # Look up the note title using the content
                        note_title = content_to_title_map.get(text_content, "Unknown Note")

                        # Display the match number, note title, and score
                        st.markdown(f"**Match {i}: *{note_title}* (Score: {score:.2f})**")

                        # Display a snippet of the note's content
                        st.write(f"> {text_content[:500]}...")
                        st.markdown("---")
        except Exception as e:
            st.warning(f"Semantic search unavailable: {e}")

        # 📄 Show Notes
        st.markdown("## 📝 Notes")
        for note in notes_to_display:
            with st.expander(f"{note['title']}"):
                
                # --- Action Buttons ---
                col1, col2, col3, col4, col5 = st.columns(5)

                # 2. View Note Content Button
                with col2:
                    view_key = f"view_note_{note['id']}"
                    if view_key not in st.session_state:
                        st.session_state[view_key] = False
                    
                    button_label = "Hide Note" if st.session_state[view_key] else "View Note"
                    if st.button(button_label, key=f"toggle_view_{note['id']}"):
                        st.session_state[view_key] = not st.session_state[view_key]

                # 4. Summarize Button
                with col4:
                    if st.button("Summarize", key=f"summarize_{note['id']}"):
                        with st.spinner("Generating summary..."):
                            summary = summarize_note(note["content"])
                            note["summary"] = summary
                            save_notes(user_id, all_notes)
                            st.rerun()

                 # 1. Favorite Button
                with col1:
                    is_favorite = note.get("favorite", False)
                    star_icon = "⭐" if is_favorite else "☆"
                    if st.button(star_icon, key=f"star_{note['id']}", help="Toggle favorite"):
                        note["favorite"] = not is_favorite
                        save_notes(user_id, all_notes)
                        st.rerun()

                # 3. View Note as PDF Button
                with col3:
                    if st.button("View note as PDF", key=f"pdf_full_{note['id']}"):
                        pdf_buffer, _ = generate_pdf(note['title'], note['content'])
                        link = get_pdf_display_link(pdf_buffer, "Click here to view Note PDF")
                        st.markdown(link, unsafe_allow_html=True)

                # 5. NEW: View Summarized PDF Button
                with col5:
                    # This button only appears if a summary already exists
                    if note.get("summary"):
                        if st.button("Summary PDF", key=f"pdf_summary_{note['id']}"):
                            pdf_buffer, _ = generate_pdf(f"Summary of {note['title']}", note["summary"])
                            link = get_pdf_display_link(pdf_buffer, "Click here to view Summary PDF")
                            st.markdown(link, unsafe_allow_html=True)


                # --- Conditionally Display Content ---
                if st.session_state[view_key]:
                    st.markdown("---")
                    st.markdown(f"**Content:**")
                    st.write(note["content"])
                    st.markdown("---")

                # --- Display Summary (if it exists) ---
                if note.get("summary"):
                    st.markdown("#### 🧠 Summary:")
                    st.info(note["summary"])


# ----------------------------- YOUTUBE -----------------------------

elif st.session_state.active_page == "YouTube to Note":
    st.subheader("📥 Import from YouTube")

    # This helper function creates the link to view a PDF in a new tab
    def get_pdf_display_link(pdf_buffer, link_text="View PDF in New Tab"):
        """Generates an HTML link to display a PDF in a new tab."""
        pdf_bytes = pdf_buffer.getvalue()
        b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        return f'<a href="data:application/pdf;base64,{b64_pdf}" target="_blank" style="text-decoration: none; color: #007BFF; font-weight: bold;">{link_text}</a>'

    # Initialize session state variables to manage the workflow
    if "youtube_note_content" not in st.session_state:
        st.session_state.youtube_note_content = None
    if "youtube_note_title" not in st.session_state:
        st.session_state.youtube_note_title = "YouTube Note" # Default title
    if "youtube_save_mode" not in st.session_state:
        st.session_state.youtube_save_mode = False

    yt_link = st.text_input("YouTube URL")

    if st.button("Generate Notes"):
        # When generating new notes, always exit the "save mode"
        st.session_state.youtube_save_mode = False
        with st.spinner("Fetching transcript..."):
            # Assuming get_transcript can be modified to return the video title
            transcript, error = get_transcript(yt_link) 
        
        if error:
            st.error(error)
            st.session_state.youtube_note_content = None
        else:
            st.success("Transcript extracted successfully.")
            with st.spinner("Generating notes from transcript..."):
                generated_notes = convert_to_notes(transcript)
                
                # Store results in session state
                # For a better experience, you could modify get_transcript to return the video's actual title
                st.session_state.youtube_note_title = "YouTube Note" 
                st.session_state.youtube_note_content = generated_notes

    # --- Display the generated notes preview and initial actions ---
    if st.session_state.youtube_note_content and not st.session_state.youtube_save_mode:
        st.markdown("---")
        st.markdown("### 📝 Generated Notes Preview")
        st.write(st.session_state.youtube_note_content)
        
        col1, col2 = st.columns(2)
        with col1:
            # This button will activate the save form
            if st.button("Edit and Save Note"):
                st.session_state.youtube_save_mode = True
                st.rerun()
        with col2:
            if st.button("View Preview as PDF"):
                pdf_buffer, _ = generate_pdf(
                    st.session_state.youtube_note_title,
                    st.session_state.youtube_note_content
                )
                link = get_pdf_display_link(pdf_buffer, "Click here to view PDF")
                st.markdown(link, unsafe_allow_html=True)

    # --- Display the full save form if in "save mode" ---
    if st.session_state.get("youtube_save_mode", False):
        st.markdown("---")
        st.markdown("### 💾 Save Your New Note")
        
        with st.form("youtube_save_form"):
            # Pre-fill the form with the generated content, but allow edits
            note_title = st.text_input("Title", value=st.session_state.youtube_note_title)
            note_content = st.text_area("Content", value=st.session_state.youtube_note_content, height=300)
            
            # Add the other metadata fields, just like in "Create Note"
            note_tags = st.text_input("Tags (comma-separated)", value="youtube")
            note_subject = st.text_input("Subject", value="YouTube Import")
            
            all_folders = load_folders(user_id)
            note_folder = st.selectbox("Folder (optional)", [""] + all_folders)
            
            note_favorite = st.checkbox("⭐ Mark as Favorite")

            # The final save button inside the form
            submitted = st.form_submit_button("Save Note to Vault")

            if submitted:
                if not note_title or not note_content:
                    st.error("Title and Content cannot be empty.")
                else:
                    add_note(
                        user_id=user_id,
                        title=note_title,
                        content=note_content,
                        tags=note_tags.split(","),
                        subject=note_subject,
                        folder=note_folder or None,
                        favorite=note_favorite
                    )
                    st.success("✅ Note saved successfully!")
                    
                    # Clean up session state and exit save mode
                    st.session_state.youtube_note_content = None
                    st.session_state.youtube_note_title = "YouTube Note"
                    st.session_state.youtube_save_mode = False
                    st.rerun()

# ----------------------------- USER PROFILE -----------------------------
elif st.session_state.active_page == "Profile":
    user_profile_page(user)
