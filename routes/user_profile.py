# routes/user_profile.py
import streamlit as st
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
from auth.user_manager import update_user_profile
from utils.cloudinary_manager import upload_image

load_dotenv()

MONGO_URL = os.getenv("MONGODB_URL")
client = MongoClient(MONGO_URL)
db = client.securescribe
users_col = db.users

# Setup Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def user_profile_page(user: dict):
    """
    Displays the user profile page with bio, avatar, and social links.
    """
    st.subheader("👤 Your Profile")

    # --- Display current avatar ---
    # Use a default placeholder if no avatar is set
    default_avatar = "https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y"
    avatar_url = user.get("avatar_url", default_avatar)
    st.image(avatar_url, caption="Your Avatar", width=150)

    with st.form("profile_form", clear_on_submit=True):
        st.write("---")
        st.markdown("#### Edit Your Details")

        # --- Form Fields ---
        new_name = st.text_input("Username", value=user.get("name", ""))
        new_bio = st.text_area("Bio", value=user.get("bio", ""), placeholder="Tell us a little about yourself...")
        uploaded_avatar = st.file_uploader("Change Avatar", type=["png", "jpg", "jpeg"])

        st.markdown("#### Social Links")
        social_links = user.get("social_links", {})
        github_url = st.text_input("GitHub URL", value=social_links.get("github", ""))
        linkedin_url = st.text_input("LinkedIn URL", value=social_links.get("linkedin", ""))
        twitter_url = st.text_input("Twitter URL", value=social_links.get("twitter", ""))

        submitted = st.form_submit_button("Update Profile")

        if submitted:
            update_data = {
                "name": new_name,
                "bio": new_bio,
                "social_links": {
                    "github": github_url,
                    "linkedin": linkedin_url,
                    "twitter": twitter_url
                }
            }

            # Handle avatar upload separately
            if uploaded_avatar is not None:
                with st.spinner("Uploading new avatar..."):
                    new_avatar_url = upload_image(uploaded_avatar)
                    if new_avatar_url:
                        update_data["avatar_url"] = new_avatar_url
                        st.success("Avatar uploaded!")
                    else:
                        st.error("Avatar upload failed. Please try again.")

            # Call the backend to update the database
            success, message = update_user_profile(user["_id"], update_data)
            
            if success:
                # IMPORTANT: Update the session state to reflect changes immediately
                st.session_state["user"].update(update_data)
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    st.write("---")
    st.write(f"**Email:** {user.get('email')}")

