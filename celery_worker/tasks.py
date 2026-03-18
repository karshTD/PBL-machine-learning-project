from celery import Celery
import os

BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery = Celery("tasks", broker=BROKER_URL, backend=RESULT_BACKEND)


def load_rag():
    import faiss
    import pickle
    index_path = "/app/faiss_data/faiss_index.bin"
    metadata_path = "/app/faiss_data/faiss_metadata.pkl"
    if os.path.exists(index_path) and os.path.exists(metadata_path):
        index = faiss.read_index(index_path)
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)
        return index, metadata
    return None, None


def generate_risk_report(filename, chunks, flagged_clauses, stress_analysis, loan_stats):
    """
    Layer 7 — AI Orchestrator
    Takes all pipeline outputs and generates a human-readable risk report
    """
    from groq import Groq

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    # ── Build context for the LLM ───────────────────────────────
    flagged_summary = "\n".join([
        f"- Clause: '{c['contract_chunk'][:150]}'\n"
        f"  Similar complaint: '{c['similar_complaint'][:150]}'\n"
        f"  Issue type: {c['issue']} | Product: {c['product']}\n"
        f"  Similarity score: {c['similarity_score']:.2f}"
        for c in flagged_clauses[:5]  # top 5 only to save tokens
    ])

    stress_summary = "\n".join([
        f"- Clause: '{s['clause'][:100]}'\n"
        f"  Stress level: {s['stress_level']} | Probability: {s['stress_probability']}"
        for s in stress_analysis
    ])

    prompt = f"""You are a financial contract risk analyst. Analyze this loan contract and generate a clear risk report.

CONTRACT FILE: {filename}
TOTAL CLAUSES ANALYZED: {len(chunks)}

FLAGGED CLAUSES (matched against {loan_stats.get('total_loans', 0)} historical complaints):
{flagged_summary}

FINANCIAL STRESS DATA:
- Total loans in database: {loan_stats.get('total_loans', 0)}
- High stress rate: {loan_stats.get('high_stress_rate', 0)}%
- Avg EMI high stress borrowers: ₹{loan_stats.get('avg_emi_high_stress', 0)}
- Avg EMI low stress borrowers: ₹{loan_stats.get('avg_emi_low_stress', 0)}

STRESS ANALYSIS PER CLAUSE:
{stress_summary}

Generate a structured risk report with:
1. Overall risk level (LOW/MEDIUM/HIGH/CRITICAL)
2. Top 3 most dangerous clauses with plain English explanation
3. Financial stress assessment
4. Specific recommendations for the borrower
5. Sections to negotiate or reject

Be direct, clear, and write for someone who is not a lawyer.
Keep the report under 400 words."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000
    )

    return response.choices[0].message.content


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
        distances, indices = index.search(chunk_embeddings, k)

        for i, chunk in enumerate(chunks):
            for j in range(k):
                dist = distances[i][j]
                idx = indices[i][j]
                sim_score = 1.0 - (dist / 2.0)

                if sim_score > 0.3:
                    flagged_clauses.append({
                        "contract_chunk": chunk,
                        "similar_complaint": metadata[int(idx)]["text"][:300],
                        "product": metadata[int(idx)]["product"],
                        "issue": metadata[int(idx)]["issue"],
                        "similarity_score": float(sim_score)
                    })

        flagged_clauses.sort(key=lambda x: x["similarity_score"], reverse=True)
        flagged_clauses = flagged_clauses[:10]
        print(f"[Worker] Found {len(flagged_clauses)} flagged clauses.")
    else:
        print("[Worker] FAISS index not found. Skipping RAG.")

    # ── Stage 5: MCP — Financial Stress Analysis ───────────────────
    import requests

    mcp_url = os.environ.get("MCP_SERVER_URL", "http://mcp_server:6000")
    stress_results = []
    loan_stats = {}

    try:
        stats_response = requests.get(f"{mcp_url}/loan_stats")
        loan_stats = stats_response.json()

        for clause in flagged_clauses[:3]:
            stress_response = requests.post(
                f"{mcp_url}/predict_stress",
                json={
                    "age": 35,
                    "monthly_income": 50000,
                    "loan_amount": 500000,
                    "interest_rate": 12.0,
                    "tenure_years": 5,
                    "monthly_emi": 11000,
                    "dependents": 1,
                    "credit_score": 700,
                    "employment_type": "salaried"
                }
            )
            stress_data = stress_response.json()
            stress_results.append({
                "clause": clause["contract_chunk"][:100],
                "stress_level": stress_data.get("stress_level"),
                "stress_probability": stress_data.get("stress_probability"),
                "risk_flag": stress_data.get("risk_flag")
            })

        print(f"[Worker] MCP stress analysis complete")

    except Exception as e:
        print(f"[Worker] MCP server unavailable: {e}")
        loan_stats = {}

    # ── Stage 6: Generate AI Risk Report ───────────────────────────
    print("[Worker] Running Stage 6: Generating AI risk report...")
    risk_report = ""
    try:
        risk_report = generate_risk_report(
            filename=filename,
            chunks=chunks,
            flagged_clauses=flagged_clauses,
            stress_analysis=stress_results,
            loan_stats=loan_stats
        )
        print("[Worker] Risk report generated successfully")
    except Exception as e:
        print(f"[Worker] Risk report generation failed: {e}")
        risk_report = "Risk report generation failed. Please try again."

    # ── Return final result ─────────────────────────────────────────
    return {
        "filename": filename,
        "status": "complete",
        "total_elements": len(elements),
        "total_chunks": len(chunks),
        "flagged_clauses": flagged_clauses,
        "stress_analysis": stress_results,
        "loan_stats": loan_stats,
        "rag_available": rag_available,
        "risk_report": risk_report,
        "message": "Analysis complete."
    }