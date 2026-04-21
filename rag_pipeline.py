import os
import re
import faiss
import numpy as np
import pickle

# Suppress TensorFlow/oneDNN warnings before sentence-transformers loads
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["USE_TF"] = "0"

from sentence_transformers import SentenceTransformer

# ── Model (loaded once) ──────────────────────────────────────────────────────
_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


# ── 1. DOCUMENT LOADING ──────────────────────────────────────────────────────
def load_document(file_path: str) -> str:
    ext = file_path.rsplit(".", 1)[-1].lower()

    if ext == "txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

    elif ext == "pdf":
        import PyPDF2
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

    elif ext == "docx":
        import docx
        doc = docx.Document(file_path)
        text = "\n".join(p.text for p in doc.paragraphs)

    else:
        raise ValueError(f"Unsupported file type: {ext}")

    return clean_text(text)


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)          # collapse whitespace
    text = re.sub(r"[^\x00-\x7F]+", " ", text)  # remove non-ASCII
    return text.strip()


# ── 2. CHUNKING ──────────────────────────────────────────────────────────────
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


# ── 3 & 4. EMBEDDINGS + FAISS VECTOR DB ─────────────────────────────────────
def build_vector_store(chunks: list[str], store_dir: str = "vector_store") -> str:
    os.makedirs(store_dir, exist_ok=True)
    embedder = get_embedder()

    embeddings = embedder.encode(chunks, show_progress_bar=False)
    embeddings = np.array(embeddings, dtype="float32")

    # Normalise for cosine similarity
    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatIP(embeddings.shape[1])  # Inner-product == cosine after normalisation
    index.add(embeddings)

    faiss.write_index(index, os.path.join(store_dir, "index.faiss"))
    with open(os.path.join(store_dir, "chunks.pkl"), "wb") as f:
        pickle.dump(chunks, f)

    return store_dir


def load_vector_store(store_dir: str = "vector_store"):
    index = faiss.read_index(os.path.join(store_dir, "index.faiss"))
    with open(os.path.join(store_dir, "chunks.pkl"), "rb") as f:
        chunks = pickle.load(f)
    return index, chunks


# ── 5. RETRIEVAL ─────────────────────────────────────────────────────────────
def retrieve(query: str, index, chunks: list[str], top_k: int = 5) -> list[str]:
    embedder = get_embedder()
    query_vec = embedder.encode([query], show_progress_bar=False)
    query_vec = np.array(query_vec, dtype="float32")
    faiss.normalize_L2(query_vec)

    _, indices = index.search(query_vec, top_k)
    return [chunks[i] for i in indices[0] if i < len(chunks)]


# ── 6. AUGMENTATION ──────────────────────────────────────────────────────────
def build_context(retrieved_chunks: list[str]) -> str:
    return "\n\n---\n\n".join(retrieved_chunks)


# ── FULL PIPELINE (convenience) ──────────────────────────────────────────────
def process_syllabus(file_path: str, store_dir: str = "vector_store") -> str:
    """Load → clean → chunk → embed → store. Returns store_dir."""
    text = load_document(file_path)
    chunks = chunk_text(text)
    build_vector_store(chunks, store_dir)
    return store_dir


def get_context_for_query(query: str, store_dir: str = "vector_store", top_k: int = 5) -> str:
    """Load vector store → retrieve → return combined context string."""
    index, chunks = load_vector_store(store_dir)
    retrieved = retrieve(query, index, chunks, top_k=top_k)
    return build_context(retrieved)
