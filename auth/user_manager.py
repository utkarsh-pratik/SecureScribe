# auth/user_manager.py

from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from auth.auth_manager import hash_password, verify_password, create_access_token, decode_token
from db.mongo import get_users_collection
import re

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# ------------------------ SIGNUP ------------------------

def signup_user(name: str, email: str, password: str) -> tuple[bool, str]:
    """Create a new user. Returns (success, message)."""
    users = get_users_collection()
    
    # 1. Check for empty fields
    if not name or not email or not password:
        return False, "All fields are required."

    # 2. Validate email format using regex
    if not re.match(EMAIL_REGEX, email):
        return False, "Invalid email format. Please enter a valid email address."

    # 3. Check if email already exists in the database
    if users.find_one({"email": email}):
        return False, "Email already exists."

    hashed = hash_password(password)
    user_doc = {
        "name": name,
        "email": email,
        "password": hashed,
        "created_at": datetime.utcnow()
    }

    users.insert_one(user_doc)
    return True, "Signup successful! You can now log in."

# ------------------------ LOGIN ------------------------

def login_user(email: str, password: str) -> tuple[bool, dict | str]:
    """
    Logs in a user.
    On success, returns (True, user_document).
    On failure, returns (False, error_message_string).
    """
    users = get_users_collection()
    user = users.find_one({"email": email})

    if user and verify_password(password, user["password"]):
        # Convert the ObjectId to a string so it can be used easily
        user["_id"] = str(user["_id"])
        # The username is stored as 'name' in your signup function
        user["username"] = user.get("name") 
        return True, user  # Return the full user dictionary
    
    return False, "Invalid email or password."

# ------------------------ GET USER BY TOKEN ------------------------

def get_current_user(token: str):
    """Get user data from token."""
    try:
        payload = decode_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            return None

        users = get_users_collection()
        user = users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return None

        return {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"]
        }

    except Exception as e:
        return None
    
# ------------------------ UPDATE USER PROFILE ------------------------

def update_user_profile(user_id: str, profile_data: dict ) -> tuple[bool, str]:
    """Updates a user's profile information in the database."""
    users = get_users_collection()

    update_payload = {k: v for k, v in profile_data.items() if v is not None}

    if not update_payload:
        return False, "No new information was provided to update."

    
    try:
        result = users.update_one(
            {"_id": ObjectId(user_id)},  # Find the user by their unique ID
            {"$set": update_payload} # Set the new values
        )
        
        if result.modified_count > 0:
            return True, "Profile updated successfully!"
        else:
            return False, "No changes were made to the profile."
            
    except Exception as e:
        return False, f"An error occurred: {e}"
