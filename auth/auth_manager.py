# auth/auth_manager.py

import jwt
import bcrypt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils.secrets_manager import get_secret # Import the helper


load_dotenv()

SECRET_KEY = get_secret("SECRET_KEY")

JWT_SECRET = os.getenv("JWT_SECRET", "defaultsecret")
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "1440"))  # 1 day default


# ------------------------ PASSWORD FUNCTIONS ------------------------

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Check password against stored hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ------------------------ TOKEN FUNCTIONS ------------------------

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Generate JWT token with expiry."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=JWT_EXPIRY_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    """Decode JWT token and return payload."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise Exception("Session expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise Exception("Invalid authentication token.")
