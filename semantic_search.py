import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import streamlit as st


# Load model once (efficient)
model = SentenceTransformer("all-MiniLM-L6-v2")

# Build FAISS index
def build_index(notes):
    if not notes:
        return None, [], []

    texts = [note["content"] for note in notes]
    embeddings = model.encode(texts, show_progress_bar=False)
    index = faiss.IndexFlatL2(embeddings[0].shape[0])
    index.add(np.array(embeddings))
    return index, embeddings, texts


# Search function
def semantic_search(query, index, texts, k=3):
    query_embedding = model.encode([query])
    D, I = index.search(np.array(query_embedding), k)
    return [(texts[i], D[0][rank]) for rank, i in enumerate(I[0])]
