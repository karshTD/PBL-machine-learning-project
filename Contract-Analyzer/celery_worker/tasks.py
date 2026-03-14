from celery import Celery
import os

BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery = Celery("tasks", broker=BROKER_URL, backend=RESULT_BACKEND)

def load_rag():
    import faiss
    import pickle
    index_path = "/app/faiss_index.bin"
    metadata_path = "/app/faiss_metadata.pkl"
    if os.path.exists(index_path) and os.path.exists(metadata_path):
        index = faiss.read_index(index_path)
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)
        return index, metadata
    return None, None

@celery.task(name="tasks.process_document")
def process_document(filepath: str) -> dict:

    filename = os.path.basename(filepath)
    print(f"[Worker] Starting: {filename}")

    # ── Stage 1: Parse PDF ─────────────────────────────────────────
    from unstructured.partition.pdf import partition_pdf

    elements = partition_pdf(filepath)
    raw_text = "\n".join([str(el) for el in elements])
    print(f"[Worker] Parsed {len(elements)} elements from PDF")

    # ── Stage 2: Chunk with LangChain ──────────────────────────────
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_text(raw_text)
    print(f"[Worker] Split into {len(chunks)} chunks")

    # ── Stage 3: Embed with HuggingFace ────────────────────────────
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(chunks, show_progress_bar=False)
    print(f"[Worker] Generated {len(embeddings)} embeddings")

    # ── Stage 4: RAG - Search similar complaints ───────────────────
    print("[Worker] Running Stage 4: RAG Comparison")
    index, metadata = load_rag()
    rag_available = False
    flagged_clauses = []

    if index is not None and metadata is not None:
        rag_available = True
        print("[Worker] FAISS index loaded. Searching for matches...")
        import numpy as np
        
        chunk_embeddings = np.array(embeddings).astype('float32')
        k = 5
        # FAISS search returns squared L2 distances
        distances, indices = index.search(chunk_embeddings, k)
        
        for i, chunk in enumerate(chunks):
            for j in range(k):
                dist = distances[i][j]
                idx = indices[i][j]
                
                # Approximate cosine similarity from squared L2 distance 
                # for normalized vectors
                sim_score = 1.0 - (dist / 2.0)
                
                if sim_score > 0.3:
                    flagged_clauses.append({
                        "contract_chunk": chunk,
                       "similar_complaint": metadata[int(idx)]["text"][:300],
                        "product": metadata[int(idx)]["product"],
                        "issue": metadata[int(idx)]["issue"],
                        "similarity_score": float(sim_score)
                    })
        
        # Sort by similarity score descending
        flagged_clauses.sort(key=lambda x: x["similarity_score"], reverse=True)
        # Keep top 10
        flagged_clauses = flagged_clauses[:10]
        print(f"[Worker] Found {len(flagged_clauses)} flagged clauses.")
    else:
        print("[Worker] FAISS index not found. Skipping RAG.")

    # ── Return result ───────
    return {
        "filename": filename,
        "status": "parsed_embedded_and_rag_checked",
        "total_elements": len(elements),
        "total_chunks": len(chunks),
        "embedding_shape": list(embeddings.shape),
        "sample_chunk": chunks[0] if chunks else "",
        "rag_available": rag_available,
        "flagged_clauses": flagged_clauses,
        "message": "Processing complete with RAG check."
    }