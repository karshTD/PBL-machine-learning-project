from celery import Celery
import os

BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery = Celery("tasks", broker=BROKER_URL, backend=RESULT_BACKEND)


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

    # ── Return result (Layer 5 will store these in vector DB) ───────
    return {
        "filename": filename,
        "status": "parsed_and_embedded",
        "total_elements": len(elements),
        "total_chunks": len(chunks),
        "embedding_shape": list(embeddings.shape),
        "sample_chunk": chunks[0] if chunks else "",
        "message": "Ready for RAG. Vector storage coming in Layer 5."
    }