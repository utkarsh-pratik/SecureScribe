# utils/secrets_manager.py
import streamlit as st
import os

def get_secret(key: str) -> str:
    """
    Retrieves a secret value.
    Checks Streamlit's secrets manager first, then falls back to environment variables.
    """
    if hasattr(st, 'secrets') and key in st.secrets:
        return st.secrets[key]
    
    return os.getenv(key)
