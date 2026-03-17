# Contract Analyzer

An AI-powered tool that reads Indian loan contracts and tells borrowers exactly what's dangerous — in plain English.

Most people sign loan agreements without understanding what they're agreeing to. Predatory clauses like floating interest rates, forced arbitration, compound penal interest, and cross-collateralization are buried in dense legal language that nobody reads. This project fixes that.

---

## What It Does

Upload a PDF loan contract. The system:

1. Parses every clause in the document
2. Compares each clause against 50,000 real consumer complaints using semantic similarity
3. Predicts financial stress risk using a trained machine learning model
4. Generates a full legal-style risk report using an LLM

The result is a plain-English risk report that tells the borrower what's dangerous, what to negotiate, and what their rights are.

Built specifically for Indian loan contracts — car loans, two-wheeler loans, personal loans, and BNPL agreements.

---

## Demo

| Upload Screen | Processing | Risk Report |
|---|---|---|
| Drag and drop your PDF | Live 6-stage progress tracker | Flagged clauses + LLM report |

**Test result on synthetic car loan contract (BNPL_Car_Loan_Agreement_MITC.pdf):**
- 10 clauses flagged with similarity scores 0.55–0.62
- Overall risk level: HIGH
- Caught: perpetual data sharing, forced arbitration, compound penal interest, prepayment penalty, insurance bundling, unilateral term changes

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Layer 1: React Frontend  (Vite + React)            │
├─────────────────────────────────────────────────────┤
│  Layer 2: Flask API Gateway  (port 5000)            │
├─────────────────────────────────────────────────────┤
│  Layer 3: Async Task Queue  (Redis + Celery)        │
├─────────────────────────────────────────────────────┤
│  Layer 4: Document Pipeline                         │
│    PDF Parse → Chunk → Embed → FAISS Search         │
├─────────────────────────────────────────────────────┤
│  Layer 5: RAG System  (FAISS + 50k complaints)      │
├─────────────────────────────────────────────────────┤
│  Layer 6: MCP Server  (ML model + SQLite)           │
├─────────────────────────────────────────────────────┤
│  Layer 7: AI Orchestrator  (Groq LLM)               │
└─────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | React 18 + Vite |
| API Gateway | Flask (Python) |
| Async Queue | Redis + Celery |
| Containerization | Docker + Docker Compose |
| PDF Parser | Unstructured.io |
| Text Chunker | LangChain RecursiveCharacterTextSplitter |
| Embeddings | SentenceTransformers all-MiniLM-L6-v2 (384-dim) |
| Vector Database | FAISS |
| Complaints Dataset | CFPB — 50,000 rows |
| ML Model | scikit-learn RandomForestClassifier (97% accuracy) |
| Loan Database | SQLite (1,000 records) |
| LLM | Groq API — llama-3.3-70b-versatile |
| Language | Python 3.10 |

---

## Project Structure

```
contract_Analyzer/
├── .env                          # GROQ_API_KEY (not committed)
├── docker-compose.yml
├── uploads/                      # PDFs saved here on upload
├── data/                         # complaints.csv (not committed — 7GB)
├── flask_app/
│   ├── app.py                    # /upload and /status endpoints
│   ├── Dockerfile
│   └── requirements.txt
├── celery_worker/
│   ├── tasks.py                  # Main pipeline — all 6 stages
│   ├── ingest.py                 # One-time script — loads complaints into FAISS
│   ├── Dockerfile
│   └── requirements.txt
├── mcp_server/
│   ├── server.py                 # /predict_stress, /query_loans, /loan_stats
│   ├── train_model.py            # Trains RF model on container start
│   ├── loans.csv                 # 1,000 synthetic loan records
│   ├── Dockerfile
│   └── requirements.txt
└── frontend/
    ├── src/
    │   └── App.jsx               # Complete single-file React app
    ├── package.json
    └── vite.config.js
```

---

## Getting Started

### Prerequisites

- Docker Desktop (with WSL2 on Windows)
- Node.js 18+
- A Groq API key — get one free at [console.groq.com](https://console.groq.com)
- The CFPB complaints dataset (`complaints.csv`) placed in the `data/` folder

### 1. Configure environment

Create a `.env` file in the root folder:

```
GROQ_API_KEY=your_key_here
```

No spaces around the `=` sign.

### 2. Start the backend

```bash
docker compose up --build
```

This starts four services: Redis, Flask, Celery worker, and the MCP server. The ML model trains automatically when the MCP server container starts.

### 3. Build the FAISS complaints index

This only needs to be done once (or after a full container wipe):

```bash
docker exec -it contract_analyzer-celery_worker-1 python ingest.py
```

This takes 5–10 minutes to embed 50,000 complaint rows. Wait for it to complete before uploading any contracts.

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## How to Use

1. Open the app at `http://localhost:5173`
2. Drag and drop a PDF loan contract onto the upload area
3. Watch the 6-stage pipeline progress in real time
4. View the flagged clauses tab — each clause shows a similarity score and the matched consumer complaint
5. Switch to the Risk Report tab for the full LLM-generated legal analysis

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/upload` | Upload a PDF. Returns `task_id`. |
| GET | `/status/<task_id>` | Poll task status. Returns full result when complete. |
| GET | `/loan_stats` | Aggregate statistics from loan database |
| POST | `/predict_stress` | Run ML stress prediction on loan features |

---

## Pipeline Stages

| Stage | What Happens |
|---|---|
| 1 | `unstructured.io` extracts all elements from the PDF |
| 2 | LangChain splits text into 500-character chunks with 50-character overlap |
| 3 | SentenceTransformer encodes each chunk into a 384-dimensional vector |
| 4 | FAISS searches for the top 5 similar complaints per chunk (threshold: 0.3) |
| 5 | MCP server runs RandomForest stress prediction and returns loan statistics |
| 6 | Groq LLM generates a full legal risk report from the flagged clauses |

---

## Docker Services

| Service | Port | Role |
|---|---|---|
| redis | 6380 (external) | Message broker and result backend |
| flask | 5000 | API gateway |
| celery_worker | — | Background pipeline processor |
| mcp_server | 6000 | ML model and SQL query tools |

---

## ML Model Performance

The RandomForestClassifier was trained on 1,000 synthetic Indian loan records with features including age, income, loan amount, EMI, loan tenure, and credit score.

- **Accuracy:** 97% on held-out test set
- **Target:** `stress_level` (high / low)
- **Training:** Automatic on MCP server container startup via `train_model.py`

---

## Known Issues

- **Duplicate flagged clauses** — the same clause can appear multiple times in results if it matches multiple complaints. Fix in progress (deduplication in `tasks.py`).
- **`ingest.py` must be re-run after full container wipe** — FAISS index is stored inside the container by default. A volume mount fix is planned.

---

## Roadmap

- [x] Layer 3 — Async task queue (Redis + Celery)
- [x] Layer 4 — Document pipeline (parse, chunk, embed)
- [x] Layer 5 — RAG system (FAISS vector search)
- [x] Layer 6 — MCP server (ML model + SQLite)
- [x] Layer 7 — AI orchestrator (Groq LLM risk report)
- [x] Layer 1 — React frontend
- [ ] Deduplicate flagged clauses
- [ ] Persist FAISS index with Docker volume mount
- [ ] Layer 2 — JWT authentication
- [ ] Security hardening (rate limiting, Redis password, HTTPS)


---

## License

This project is for educational purposes.
