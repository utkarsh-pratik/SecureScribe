# utils/chat_ui.py

import streamlit as st

def render_chat_css():
    """Injects the CSS for the floating button and chat popup."""
    st.markdown("""
        <style>
            /* Floating Action Button */
            .chat-button {
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 60px;
                height: 60px;
                background-color: #0d6efd; /* A modern blue */
                color: white;
                border-radius: 50%;
                border: none;
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 24px;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                z-index: 1000;
                text-decoration: none; /* Remove underline from link */
            }
            .chat-button:hover {
                background-color: #0b5ed7;
            }
            /* Main Chat Popup Container */
            .chat-popup-container {
                position: fixed;
                bottom: 100px;
                right: 30px;
                width: 420px;
                max-height: 70vh;
                background-color: #f9f9f9;
                border-radius: 15px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
                z-index: 1001;
                /* Use a container query for responsive design if needed */
                container-type: inline-size;
            }
        </style>
    """, unsafe_allow_html=True)

def render_chat_button():
    """Renders the floating chat button as a styled link."""
    st.markdown('<a href="?chat=open" target="_self" class="chat-button">🧠</a>', unsafe_allow_html=True)
