import pandas as pd
import faiss
import numpy as np
import os
import pickle
from sentence_transformers import SentenceTransformer

CSV_PATH = "/data/complaints.csv"
FAISS_INDEX_PATH = "/app/faiss_data/faiss_index.bin"
FAISS_METADATA_PATH = "/app/faiss_data/faiss_metadata.pkl"
MAX_ROWS = 50000
BATCH_SIZE = 500
MODEL_NAME = "all-MiniLM-L6-v2"

def run_ingestion():
    print("[Ingest] Loading complaints CSV...")

    df = pd.read_csv(
        CSV_PATH,
        usecols=["Consumer complaint narrative", "Product", "Issue"],
        nrows=MAX_ROWS
    )
    df = df.dropna(subset=["Consumer complaint narrative"])
    df = df[df["Consumer complaint narrative"].str.strip() != ""]
    df = df.reset_index(drop=True)

    print(f"[Ingest] {len(df)} complaints with narratives found")

    texts = df["Consumer complaint narrative"].tolist()
    products = df["Product"].fillna("Unknown").tolist()
    issues = df["Issue"].fillna("Unknown").tolist()

    print("[Ingest] Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    print("[Ingest] Embedding complaints in batches...")
    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        embeddings = model.encode(batch, show_progress_bar=False)
        all_embeddings.append(embeddings)
        print(f"[Ingest] Processed {min(i + BATCH_SIZE, len(texts))}/{len(texts)}")

    all_embeddings = np.vstack(all_embeddings).astype("float32")

    print("[Ingest] Building FAISS index...")
    dimension = all_embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(all_embeddings)
    os.makedirs("/app/faiss_data", exist_ok=True)
    faiss.write_index(index, FAISS_INDEX_PATH)

    metadata = [
        {"text": texts[i], "product": products[i], "issue": issues[i]}
        for i in range(len(texts))
    ]
    with open(FAISS_METADATA_PATH, "wb") as f:
        pickle.dump(metadata, f)

    print(f"[Ingest] FAISS index saved — {index.ntotal} vectors")
    print("[Ingest] ✅ Ingestion complete!")

if __name__ == "__main__":
    run_ingestion()