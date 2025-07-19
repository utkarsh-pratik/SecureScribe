# rag_pipeline.py

import streamlit as st
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# Local imports
from summarizer import summarize_note # We can reuse the text model for the final answer

@st.cache_resource
def get_embedding_model():
    """Loads and caches the sentence-transformer model."""
    return SentenceTransformer('all-MiniLM-L6-v2')

@st.cache_resource
def get_or_build_index(notes: list):
    """
    Creates vector embeddings for all notes. This is cached for the session.
    """
    st.info("Initializing AI Tutor knowledge base...")
    model = get_embedding_model()
    
    # We'll store both the embedding and the original text chunk
    note_chunks = []
    for note in notes:
        if note.get("content"):
            # Simple chunking by paragraph for better context
            for chunk in note["content"].split('\n\n'):
                if chunk.strip():
                    note_chunks.append({
                        "text": chunk,
                        "source_title": note["title"],
                        "embedding": model.encode(chunk)
                    })
    
    if not note_chunks:
        return None
        
    return note_chunks

def get_rag_response(query: str, index: list, top_k: int = 3) -> str:
    """
    Performs the full RAG pipeline: retrieves relevant context and generates an answer.
    """
    if not index:
        return "The knowledge base is empty. Please add some notes first."

    model = get_embedding_model()
    query_embedding = model.encode(query)

    # --- Retrieve Step ---
    # Calculate similarity between the query and all note chunks
    similarities = [
        cosine_similarity(query_embedding.reshape(1, -1), chunk['embedding'].reshape(1, -1))[0][0]
        for chunk in index
    ]
    
    # Get the indices of the top_k most similar chunks
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    # --- Augment Step ---
    # Combine the retrieved chunks into a single context string
    context = "\n\n---\n\n".join([index[i]['text'] for i in top_indices])
    
    # --- Generate Step ---
    # Create the final prompt for the LLM
    final_prompt = (
        "You are an expert AI assistant. Based ONLY on the following context from my personal notes, "
        "provide a clear and concise answer to my question. Do not use any external knowledge. "
        "If the answer is not contained within the provided context, say 'I could not find an answer in your notes.'\n\n"
        f"CONTEXT FROM NOTES:\n{context}\n\n"
        f"QUESTION:\n{query}\n\n"
        "ANSWER:"
    )

    # Use your existing summarizer function to get the final answer
    return summarize_note(final_prompt)
