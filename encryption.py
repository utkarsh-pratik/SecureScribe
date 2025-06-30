from cryptography.fernet import Fernet
import os

KEY_PATH = "data/secret.key"

def load_key():
    """
    Loads the key from KEY_PATH. If it doesn't exist, a new one is created.
    """
    if not os.path.exists(KEY_PATH):
        os.makedirs("data", exist_ok=True)
        key = Fernet.generate_key()
        with open(KEY_PATH, "wb") as key_file:
            key_file.write(key)
    
    with open(KEY_PATH, "rb") as key_file:
        return key_file.read()

# Load the key once when the module is imported
try:
    key = load_key()
    fernet = Fernet(key)
except Exception as e:
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
