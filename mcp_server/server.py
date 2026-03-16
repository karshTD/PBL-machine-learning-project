from flask import Flask, request, jsonify
import sqlite3
import joblib
import pandas as pd
import numpy as np
import os

app = Flask(__name__)

MODEL_PATH = "/app/stress_model.pkl"
DB_PATH = "/app/loans.db"

# Load model lazily — only when first request comes in
model = None

def get_model():
    global model
    if model is None:
        if not os.path.exists(MODEL_PATH):
            # Train on the fly if model doesn't exist
            import train_model
            train_model.run_ingestion() if hasattr(train_model, 'run_ingestion') else None
        model = joblib.load(MODEL_PATH)
    return model

print("[MCP] Server starting...")

# ── Tool 1: Predict Financial Stress ───────────────────────────
@app.route("/predict_stress", methods=["POST"])
def predict_stress():
    data = request.json
    try:
        m = get_model()
        employment_map = {"salaried": 0, "business": 1}
        employment_encoded = employment_map.get(
            data.get("employment_type", "salaried").lower(), 0
        )
        features = np.array([[
            data.get("age", 35),
            data.get("monthly_income", 50000),
            data.get("loan_amount", 500000),
            data.get("interest_rate", 10.0),
            data.get("tenure_years", 5),
            data.get("monthly_emi", 10000),
            data.get("dependents", 1),
            data.get("credit_score", 700),
            employment_encoded
        ]])
        prediction = m.predict(features)[0]
        probability = m.predict_proba(features)[0]
        return jsonify({
            "stress_level": "High" if prediction == 1 else "Low",
            "stress_probability": round(float(probability[1]), 3),
            "risk_flag": bool(prediction == 1)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ── Tool 2: Query Loan Database ─────────────────────────────────
@app.route("/query_loans", methods=["POST"])
def query_loans():
    """
    Input: SQL query string
    Output: query results as JSON
    """
    data = request.json
    query = data.get("query", "")

    # Safety check — only allow SELECT queries
    if not query.strip().upper().startswith("SELECT"):
        return jsonify({"error": "Only SELECT queries allowed"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query, conn)
        conn.close()

        return jsonify({
            "results": df.to_dict(orient="records"),
            "row_count": len(df)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ── Tool 3: Get Loan Statistics ─────────────────────────────────
@app.route("/loan_stats", methods=["GET"])
def loan_stats():
    """
    Returns summary statistics about the loan dataset
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM loans", conn)
        conn.close()

        high_stress = df[df["stress_level"] == "High"]
        low_stress = df[df["stress_level"] == "Low"]

        return jsonify({
            "total_loans": len(df),
            "high_stress_count": len(high_stress),
            "low_stress_count": len(low_stress),
            "avg_interest_rate_high_stress": round(high_stress["interest_rate"].mean(), 2),
            "avg_interest_rate_low_stress": round(low_stress["interest_rate"].mean(), 2),
            "avg_emi_high_stress": round(high_stress["monthly_emi"].mean(), 2),
            "avg_emi_low_stress": round(low_stress["monthly_emi"].mean(), 2),
            "high_stress_rate": round(len(high_stress) / len(df) * 100, 1)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000, debug=False)