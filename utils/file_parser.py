# utils/file_parser.py

import streamlit as st
from PyPDF2 import PdfReader
from io import BytesIO

def parse_file(uploaded_file):
    """
    Parses an uploaded file (.txt or .pdf) and returns its text content.
    """
    if uploaded_file is None:
        return ""

    file_type = uploaded_file.type
    
    try:
        if file_type == "text/plain":
            # For .txt files, read as a string
            return uploaded_file.getvalue().decode("utf-8")
        
        elif file_type == "application/pdf":
            # For .pdf files, use PyPDF2 to extract text
            pdf_content = ""
            # PyPDF2 needs a file-like object, BytesIO works perfectly
            pdf_file = BytesIO(uploaded_file.getvalue())
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                pdf_content += page.extract_text() + "\n"
            return pdf_content
            
        else:
            return "Unsupported file type. Please upload a .txt or .pdf file."

    except Exception as e:
        st.error(f"Error parsing file: {e}")
        return ""