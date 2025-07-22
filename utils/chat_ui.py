# utils/chat_ui.py

import streamlit as st

def render_chat_widget(user_id: str):
    """
    Injects the HTML, CSS, and JavaScript for a true floating chat widget
    that loads the chat interface in a self-referential iframe.
    """
    # The URL for the iframe to load. It points to the same app with a query param.
    chat_app_url = f"?page=chat&user_id={user_id}"

    st.markdown(f"""
        <style>
            .chat-button {{
                position: fixed; bottom: 30px; right: 30px; width: 60px; height: 60px;
                background-color: #0d6efd; color: white; border-radius: 50%; border: none;
                display: flex; justify-content: center; align-items: center; font-size: 24px;
                cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.2); z-index: 1000;
            }}
            .chat-popup {{
                display: none; /* Hidden by default */
                position: fixed; bottom: 100px; right: 30px; width: 420px; height: 600px;
                border: 1px solid #ccc; border-radius: 15px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.3); z-index: 1001;
                flex-direction: column; background-color: white;
            }}
            .chat-popup iframe {{
                width: 100%; height: 100%; border: none; border-radius: 15px;
            }}
        </style>

        <div id="chat-button" class="chat-button" onclick="openChat()">🧠</div>

        <div id="chat-popup" class="chat-popup">
            <iframe id="chat-iframe" src="{chat_app_url}" title="AI Tutor"></iframe>
        </div>

        <script>
            const chatPopup = document.getElementById('chat-popup');
            const chatIframe = document.getElementById('chat-iframe');

            // This function opens the chat popup
            function openChat() {{
                chatPopup.style.display = 'flex';
            }}

            // We need a way for the iframe to tell the parent to close it
            window.addEventListener('message', event => {{
                if (event.data === 'close-chat') {{
                    chatPopup.style.display = 'none';
                }}
            }});
        </script>
    """, unsafe_allow_html=True)
