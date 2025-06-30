# utils/cloudinary_manager.py
import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure Cloudinary with your credentials
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

def upload_image(file_to_upload):
    """Uploads an image file to Cloudinary and returns its secure URL."""
    try:
        # The 'folder' parameter helps organize uploads in your Cloudinary account
        upload_result = cloudinary.uploader.upload(file_to_upload, folder="securescribe_avatars")
        return upload_result.get("secure_url")
    except Exception as e:
        print(f"Error uploading to Cloudinary: {e}")
        return None