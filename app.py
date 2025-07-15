import streamlit as st
from datetime import datetime
from note_manager import load_notes, add_note, save_notes, update_notes_after_folder_rename, update_notes_after_folder_delete, generate_summary_for_note
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
from utils.file_parser import parse_file
import cloudinary
import cloudinary.uploader
from utils.web_scraper import scrape_website_text
from utils.transcriber import transcribe_from_file, transcribe_from_url

st.set_page_config(page_title="SecureScribe", layout="wide")

# --- SESSION STATE INITIALIZATION ---
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "active_page" not in st.session_state:
    st.session_state.active_page = "View Notes"
if "pre_filled_content" not in st.session_state:
    st.session_state.pre_filled_content = ""
if "attachment_url" not in st.session_state:
    st.session_state.attachment_url = None
if "note_creation_mode" not in st.session_state:
    st.session_state.note_creation_mode = "text" # Default to 'text' mode

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

if st.sidebar.button("📥 Import from Web"):
    st.session_state.active_page = "Import from Web"
    st.rerun()

if st.sidebar.button("🎙️ Transcribe Media"):
    st.session_state.active_page = "Transcribe Media"
    st.rerun()

if st.sidebar.button("👤 Profile"):
    st.session_state.active_page = "Profile"
    st.rerun()

#st.sidebar.markdown("---")

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

    # --- NEW: File Uploader Feature ---
    st.markdown("---")
    st.markdown("#### Attach a file or extract its text:")
    uploaded_file = st.file_uploader("Upload PDF/TXT to Pre-fill or Attach", 
        type=["pdf", "txt"],
        help="Use the buttons below to either extract the text or attach the file to the note."
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 Extract Text from File", disabled=(uploaded_file is None)):
            with st.spinner("Extracting content from file..."):
                st.session_state.pre_filled_content = parse_file(uploaded_file)
            st.session_state.note_creation_mode = "text" # Set mode to text
            st.session_state.attachment_url = None # Clear any previous attachment
            st.rerun()

    with col2:
        if st.button("📎 Attach File to Note", disabled=(uploaded_file is None)):
            try:
                with st.spinner("Uploading attachment..."):
                    # Use "raw" for non-image files like PDFs to preserve them
                    upload_result = cloudinary.uploader.upload(
                        uploaded_file, 
                        resource_type="raw", 
                        folder="securescribe_attachments",
                        public_id=uploaded_file.name,
                        overwrite=True # Allow overwriting if a file with the same name exists
                    )

                public_url = upload_result.get("secure_url")
                
                if public_url:
                    st.session_state.attachment_url = public_url
                    st.session_state.note_creation_mode = "attachment" # Set mode to attachment
                    st.session_state.pre_filled_content = "" # Clear text content
                    st.success(f"File '{uploaded_file.name}' attached.")
                else:
                    st.error("File upload succeeded, but could not construct a public URL.")
                # ---------------------------------------------
            except Exception as e:
                st.error(f"File upload failed: {e}")
                st.session_state.attachment_url = None

    st.markdown("---")
    # ------------------------------------

    is_attachment_mode = st.session_state.note_creation_mode == "attachment"

    title = st.text_input("Title")

    # Conditionally disable the content area
    content_placeholder = "Note content is taken from the attached file." if is_attachment_mode else ""
    content = st.text_area(
        "Note Content", 
        value=st.session_state.pre_filled_content, 
        height=300, 
        disabled=is_attachment_mode,
        placeholder=content_placeholder
    )
        
    tags = st.text_input("Tags (comma-separated)")
    subject = st.text_input("Subject")
    folder = st.selectbox("Folder (optional)", [""] + load_folders(user["_id"]))
    is_fav = st.checkbox("⭐ Mark as Favorite")

    # Display info about the attachment if one is ready
    if st.session_state.get("attachment_url"):
        st.info(f"Attachment ready: {st.session_state.attachment_url}")

    if st.button("Save Note"):
        if title and (content or st.session_state.get("attachment_url")):
            note = add_note(
                user["_id"], 
                title, 
                content, 
                tags.split(","), 
                subject, 
                folder or None, 
                favorite=is_fav,
                attachment_url=st.session_state.get("attachment_url") # Pass the URL
            )
            st.success(f"Note '{note['title']}' saved!")
            # --- NEW: Clear the pre-filled content after saving ---
            st.session_state.pre_filled_content = ""
            st.session_state.attachment_url = None  # Clear the attachment URL after saving
            st.session_state.note_creation_mode = "text"
        else:
            st.warning("⚠️ A title and either content or an attachment is required.")
            
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
                            # --- FIX: Call the correct function ---
                            summary = generate_summary_for_note(note)

                            # Check if the function returned an error
                            if summary.startswith("Error:"):
                                st.error(summary)
                            else:
                                # If successful, save the summary
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


                # --- Conditionally Display Content or Attachment Link ---
                if st.session_state.get(f"view_note_{note['id']}", False):
                    st.markdown("---")
                    
                    if note.get("content"):
                        # If there is text content, display it
                        st.markdown(f"**Content:**")
                        st.write(note["content"])
                    elif note.get("attachment_url"):
                        # If there is no text content BUT there is an attachment, show the link
                        st.markdown(f"**📎 Attachment:** [View Attached File]({note['attachment_url']})", unsafe_allow_html=True)
                    # --------------------

                    st.markdown("---")

                # --- Display Summary (if it exists) ---
                if note.get("summary"):
                    st.markdown("#### 🧠 Summary:")
                    st.info(note["summary"])


# ----------------------------- IMPORT FROM WEB -----------------------------
elif st.session_state.active_page == "Import from Web": # <-- RENAMED
    st.subheader("📥 Import from Web")

    # --- Refactored Session State Initialization ---
    if "generated_note_content" not in st.session_state:
        st.session_state.generated_note_content = None
    if "generated_note_title" not in st.session_state:
        st.session_state.generated_note_title = "Generated Note"
    if "generated_note_save_mode" not in st.session_state:
        st.session_state.generated_note_save_mode = False
    # ---------------------------------------------

    # --- Tabbed Interface for YouTube and Website ---
    tab1, tab2 = st.tabs(["From YouTube", "From Website URL"])

    with tab1:
        st.markdown("#### Generate Notes from a YouTube Video")
        yt_link = st.text_input("YouTube URL", key="youtube_url_input")
        if st.button("Generate from YouTube"):
            st.session_state.generated_note_save_mode = False # Reset save mode
            with st.spinner("Fetching transcript..."):
                transcript, error = get_transcript(yt_link)
            
            if error:
                st.error(error)
                st.session_state.generated_note_content = None
            else:
                st.success("Transcript extracted successfully.")
                with st.spinner("Generating notes from transcript..."):
                    st.session_state.generated_note_title = "YouTube Note"
                    st.session_state.generated_note_content = convert_to_notes(transcript)

    with tab2:
        st.markdown("#### Generate Notes from a Website")
        web_url = st.text_input("Website URL", key="website_url_input")
        if st.button("Generate from Website"):
            st.session_state.generated_note_save_mode = False # Reset save mode
            with st.spinner("Scraping website content..."):
                scraped_text, page_title = scrape_website_text(web_url)
            
            if not scraped_text:
                st.error(page_title) # page_title will contain the error message
                st.session_state.generated_note_content = None
            else:
                st.success("Website content scraped successfully.")
                with st.spinner("Generating notes from content..."):
                    st.session_state.generated_note_title = page_title
                    st.session_state.generated_note_content = convert_to_notes(scraped_text)

    # --- Display the generated notes preview and save form (this part is now generic) ---
    if st.session_state.generated_note_content:
        st.markdown("---")
        st.markdown("### 📝 Generated Notes Preview")
        st.write(st.session_state.generated_note_content)
        
        # Activate the save form if not already active
        if not st.session_state.generated_note_save_mode:
            if st.button("Edit and Save Note"):
                st.session_state.generated_note_save_mode = True
                st.rerun()

    # Display the full save form if in "save mode"
    if st.session_state.generated_note_save_mode:
        st.markdown("---")
        st.markdown("### 💾 Save Your New Note")
        
        with st.form("generated_note_save_form"):
            note_title = st.text_input("Title", value=st.session_state.generated_note_title)
            note_content = st.text_area("Content", value=st.session_state.generated_note_content, height=300)
            
            note_tags = st.text_input("Tags (comma-separated)", value="generated, import")
            note_subject = st.text_input("Subject")
            
            all_folders = load_folders(user_id)
            note_folder = st.selectbox("Folder (optional)", [""] + all_folders)
            note_favorite = st.checkbox("⭐ Mark as Favorite")

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
                    st.session_state.generated_note_content = None
                    st.session_state.generated_note_save_mode = False
                    st.rerun()


# ----------------------------- TRANSCRIBE MEDIA (with Auto-Detect) -----------------------------
elif st.session_state.active_page == "Transcribe Media":
    st.subheader("🎙️ Transcribe Media to Notes")

    # --- Generic Session State Initialization ---
    if "generated_note_content" not in st.session_state:
        st.session_state.generated_note_content = None
    if "generated_note_title" not in st.session_state:
        st.session_state.generated_note_title = "Generated Note"
    if "generated_note_save_mode" not in st.session_state:
        st.session_state.generated_note_save_mode = False

    # --- UPDATED: Language Selection with Auto-Detect ---
    SUPPORTED_LANGUAGES = {
        "Auto-Detect": "auto", # Add the auto-detect option
        "English": "en",
        "Hindi": "hi",
        "Spanish": "es",
        "French": "fr",
        "German": "de",
        "Italian": "it",
        "Portuguese": "pt",
        "Russian": "ru",
        "Japanese": "ja",
        "Korean": "ko",
        "Chinese": "zh"
    }
    selected_language_name = st.selectbox(
        "Select the language of the audio/video (or let us detect it):",
        options=list(SUPPORTED_LANGUAGES.keys()) # The list of user-friendly names
    )
    language_code = SUPPORTED_LANGUAGES[selected_language_name] # Get the corresponding code ('auto', 'en', etc.)
    st.markdown("---")
    # ----------------------------------------------------

    # --- Tabbed Interface for Upload and URL (no changes needed here) ---
    upload_tab, url_tab = st.tabs(["Upload File", "From URL"])

    with upload_tab:
        st.markdown("#### Generate Notes from an Audio or Video File")
        media_file = st.file_uploader(
            "Upload an audio or video file",
            type=["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
        )
        if st.button("Generate from Uploaded File", disabled=(media_file is None)):
            st.session_state.generated_note_save_mode = False
            spinner_text = "Transcribing file (auto-detecting language)..." if language_code == "auto" else f"Transcribing {selected_language_name} file..."
            with st.spinner(spinner_text):
                # Pass the selected language code to the function
                transcript, error = transcribe_from_file(media_file, language=language_code)
            
            if error:
                st.error(error)
            else:
                st.success("File transcribed successfully.")
                with st.spinner("Generating notes from transcript..."):
                    st.session_state.generated_note_title = f"Notes from {media_file.name}"
                    st.session_state.generated_note_content = convert_to_notes(transcript)
    
    with url_tab:
        st.markdown("#### Generate Notes from a Public URL")
        media_url = st.text_input("Public URL to an audio or video file", key="media_url_input")
        if st.button("Generate from URL", disabled=(not media_url)):
            st.session_state.generated_note_save_mode = False
            spinner_text = "Transcribing from URL (auto-detecting language)..." if language_code == "auto" else f"Transcribing {selected_language_name} from URL..."
            with st.spinner(spinner_text):
                # Pass the selected language code to the function
                transcript, error = transcribe_from_url(media_url, language=language_code)

            if error:
                st.error(error)
            else:
                st.success("URL transcribed successfully.")
                with st.spinner("Generating notes from transcript..."):
                    st.session_state.generated_note_title = "Notes from URL"
                    st.session_state.generated_note_content = convert_to_notes(transcript)


    # --- The generic preview and save form  ---
    if st.session_state.generated_note_content:
        st.markdown("---")
        st.markdown("### 📝 Generated Notes Preview")
        st.write(st.session_state.generated_note_content)
        
        if not st.session_state.generated_note_save_mode:
            if st.button("Edit and Save Note"):
                st.session_state.generated_note_save_mode = True
                st.rerun()

    if st.session_state.generated_note_save_mode:
        st.markdown("---")
        st.markdown("### 💾 Save Your New Note")
        with st.form("generated_note_save_form"):
            note_title = st.text_input("Title", value=st.session_state.generated_note_title)
            note_content = st.text_area("Content", value=st.session_state.generated_note_content, height=300)
            note_tags = st.text_input("Tags (comma-separated)", value="generated, import, transcription")
            note_subject = st.text_input("Subject")
            all_folders = load_folders(user_id)
            note_folder = st.selectbox("Folder (optional)", [""] + all_folders)
            note_favorite = st.checkbox("⭐ Mark as Favorite")
            submitted = st.form_submit_button("Save Note to Vault")
            if submitted:
                if not note_title or not note_content:
                    st.error("Title and Content cannot be empty.")
                else:
                    add_note(user_id=user_id, title=note_title, content=note_content, tags=note_tags.split(","), subject=note_subject, folder=note_folder or None, favorite=note_favorite)
                    st.success("✅ Note saved successfully!")
                    st.session_state.generated_note_content = None
                    st.session_state.generated_note_save_mode = False
                    st.rerun()

# ----------------------------- USER PROFILE -----------------------------
elif st.session_state.active_page == "Profile":
    user_profile_page(user)
