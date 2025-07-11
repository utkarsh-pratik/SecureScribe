from cryptography.fernet import Fernet
import os
import streamlit as st

KEY_PATH = "data/secret.key"

def load_key():
    """
    Loads the encryption key.
    Priority 1: From Streamlit secrets (for deployment).
    Priority 2: From a local file (for local development).
    """
    # Check if the key is in Streamlit's secrets (for deployed app)
    if "FERNET_KEY" in st.secrets:
        print("Loading encryption key from Streamlit secrets.")
        # Secrets are strings, but Fernet needs bytes.
        return st.secrets["FERNET_KEY"].encode()
    
    # Fallback to local file method (for local development)
    else:
        print("Loading encryption key from local file.")
        if not os.path.exists(KEY_PATH):
            os.makedirs("data", exist_ok=True)
            key = Fernet.generate_key()
            with open(KEY_PATH, "wb") as key_file:
                key_file.write(key)
        
        with open(KEY_PATH, "rb") as key_file:
            return key_file.read()

# --- Main initialization logic ---
try:
    # Use the new function to get the key
    key = load_key()
    fernet = Fernet(key)
except Exception as e:
    # Provide a more helpful error in the app itself
    st.error("CRITICAL: Encryption key could not be loaded. Please ensure FERNET_KEY is set in Streamlit secrets.")
    print(f"CRITICAL: Could not load encryption key. {e}")
    fernet = None

def encrypt(message: str) -> str:
    """Encrypts a string message."""
    if fernet is None:
        raise Exception("Encryption service is not available.")
    return fernet.encrypt(message.encode()).decode()

def decrypt(encrypted_message: str) -> str:
    """Decrypts an encrypted string message."""
    if fernet is None:
        raise Exception("Decryption service is not available.")
    
    try:
        # The message must be bytes.
        decrypted_message = fernet.decrypt(encrypted_message.encode())
        return decrypted_message.decode()
    except Exception:
        # This will catch any decryption error, like an invalid token or key
        return "[Decryption Failed]"
