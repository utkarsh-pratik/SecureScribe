# utils/chat_ui.py

import streamlit as st
from rag_pipeline import get_rag_response

def render_chat_dialog(vector_index):
    """
    Renders the chat dialog and handles the RAG interaction.
    """
    # Initialize chat history if it doesn't exist
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display previous messages
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle new user input
    if prompt := st.chat_input("Ask a question about your notes..."):
        # Add user message to history and display it
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get the AI's response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                if vector_index is not None:
                    response = get_rag_response(prompt, vector_index)
                else:
                    response = "I can't answer questions until you have at least one note."
                st.markdown(response)
        
        # Add AI response to history
        st.session_state.chat_history.append({"role": "assistant", "content": response})
