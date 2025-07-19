# utils/chat_ui.py

import streamlit as st
from streamlit.components.v1 import html

def render_chat_ui():
    """
    Renders the floating chat button and the chat popup container.
    Uses session state to manage the open/closed state of the chat window.
    """
    # Define the CSS for the floating button and the chat popup
    st.markdown("""
        <style>
            /* Floating Action Button */
            .chat-button {
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 60px;
                height: 60px;
                background-color: #007bff;
                color: white;
                border-radius: 50%;
                border: none;
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 24px;
                cursor: pointer;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                z-index: 1000;
            }
            /* Chat Popup Container */
            .chat-popup {
                position: fixed;
                bottom: 100px;
                right: 30px;
                width: 400px;
                height: 600px;
                background-color: white;
                border-radius: 15px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
                display: flex;
                flex-direction: column;
                z-index: 999;
                transition: transform 0.3s ease-in-out, opacity 0.3s ease-in-out;
            }
            /* Header for the chat popup */
            .chat-header {
                padding: 15px;
                background-color: #007bff;
                color: white;
                border-top-left-radius: 15px;
                border-top-right-radius: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .chat-header h3 {
                margin: 0;
                color: white;
            }
            .close-btn {
                background: none;
                border: none;
                color: white;
                font-size: 20px;
                cursor: pointer;
            }
            /* Main chat area */
            .chat-area {
                flex-grow: 1;
                padding: 15px;
                overflow-y: auto;
            }
        </style>
    """, unsafe_allow_html=True)

    # JavaScript to handle the click events for opening and closing the chat
    # It communicates with Streamlit by setting a dummy session state variable
    js_code = """
    <script>
        function toggleChat() {
            // This function will be called by the button click
            // It sets a dummy value in session storage that Streamlit can't see,
            // then forces a rerun by clicking a hidden button.
            window.parent.document.dispatchEvent(new CustomEvent('toggle-chat-event'));
        }

        // Listen for the custom event and click the hidden button
        window.parent.document.addEventListener('toggle-chat-event', function() {
            const buttons = window.parent.document.querySelectorAll('button');
            buttons.forEach(button => {
                if (button.innerText === 'RERUN_CHAT_TOGGLE') {
                    button.click();
                }
            });
        });
    </script>
    """
    
    # The HTML for the floating button
    st.markdown(f"""
        <button class="chat-button" onclick="toggleChat()">
            🧠
        </button>
        {js_code}
    """, unsafe_allow_html=True)

    # A hidden button that the JavaScript will "click" to trigger a rerun
    if st.button("RERUN_CHAT_TOGGLE", key="hidden_chat_toggle", type="primary", use_container_width=False):
        st.session_state.chat_is_open = not st.session_state.get("chat_is_open", False)
        st.rerun()
