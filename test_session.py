# test_session.py
import streamlit as st

st.title("Session State Test")

# Initialize the counter in session_state if it doesn't exist
if 'count' not in st.session_state:
    st.session_state.count = 0

# A button to increment the counter
if st.button('Increment Counter'):
    st.session_state.count += 1

st.header(f"Current Count: {st.session_state.count}")

st.info("INSTRUCTIONS: Click the 'Increment' button a few times. The count should go up. Then, refresh your browser page (press F5). The count should NOT reset to 0. If it does, there is an issue with your Streamlit environment.")