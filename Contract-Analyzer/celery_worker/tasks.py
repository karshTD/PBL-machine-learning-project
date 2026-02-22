from celery import Celery
import os
import time

# --- Celery Configuration ---
BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery = Celery("tasks", broker=BROKER_URL, backend=RESULT_BACKEND)


@celery.task(name="tasks.process_document")
def process_document(filename: str) -> dict:
    """
    Dummy task that simulates document processing.
    Later, this will call: Parser → LangChain Chunker → Embedder → Agents
    """
    print(f"[Worker] Starting to process: {filename}")

    # Simulate Stage 1: Parsing (Layer 4 will replace this)
    time.sleep(2)
    print(f"[Worker] Stage 1 complete: Text extracted from {filename}")

    # Simulate Stage 2: Chunking + Embedding (Layer 4 + 5 will replace this)
    time.sleep(2)
    print(f"[Worker] Stage 2 complete: Document chunked and embedded")

    # Simulate Stage 3: AI Analysis (Layer 7 will replace this)
    time.sleep(2)
    print(f"[Worker] Stage 3 complete: Risk analysis done")

    # Dummy result — later this will be the real JSON risk report
    return {
        "filename": filename,
        "status": "analyzed",
        "risk_score": 7.4,
        "flagged_clauses": [
            {"clause": "Section 4.2 - Penalty clause", "risk": "HIGH"},
            {"clause": "Section 7.1 - Auto-renewal", "risk": "MEDIUM"},
        ],
        "summary": "This is a dummy result. Real AI analysis coming in Layer 7."
    }