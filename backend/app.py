from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber
import io
import re

app = Flask(__name__)
CORS(app) # Allow React to talk to this server

# ==========================================
# 1. THE "RISK ENGINE" (Logic)
# ==========================================
def analyze_risk(text):
    """
    Scans the contract text for known 'Trap' keywords
    and calculates a score.
    """
    risk_score = 0
    triggered_clauses = []
    
    # 1. Define the "Bad Words" and their weight (Severity)
    # (In the future, XGBoost will learn these weights automatically)
    risk_keywords = {
        "Arbitration": {"weight": 30, "msg": "Arbitration Clause: You cannot sue in court; you must use a private judge."},
        "Prepayment Penalty": {"weight": 25, "msg": "Prepayment Penalty: You will be fined if you pay off the loan early."},
        "Variable Rate": {"weight": 25, "msg": "Variable Interest Rate: Your payments can increase at any time."},
        "Balloon Payment": {"weight": 20, "msg": "Balloon Payment: You owe a huge lump sum at the end."},
        "Waive": {"weight": 10, "msg": "Waiver of Rights: You are giving up certain legal protections."},
        "Indemnification": {"weight": 10, "msg": "Indemnification: You might have to pay for the lender's legal mistakes."}
    }

    # 2. Scan the text
    # We use 'set' to avoid counting the same word 50 times
    found_keywords = set() 
    
    for keyword, info in risk_keywords.items():
        # Regex search (ignore case)
        if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
            risk_score += info['weight']
            triggered_clauses.append(info['msg'])
            found_keywords.add(keyword)

    # 3. Cap the score at 100
    if risk_score > 100:
        risk_score = 100
    if risk_score == 0:
        risk_score = 10 # Base risk for any contract

    # 4. Determine the Label
    if risk_score > 75:
        level = "High"
    elif risk_score > 40:
        level = "Medium"
    else:
        level = "Low"

    return risk_score, level, triggered_clauses

# ==========================================
# 2. THE API ROUTE (Connection)
# ==========================================
@app.route('/api/analyze', methods=['POST'])
def analyze_contract():
    print("Received connection...")

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    filename = file.filename

    try:
        # A. Read the PDF (Using pdfplumber)
        # We open the file stream directly without saving to disk
        with pdfplumber.open(file) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
        
        print(f"Extracted {len(full_text)} characters from {filename}")

        # B. Run the Risk Engine
        score, level, warnings = analyze_risk(full_text)

        # C. Create the Explanation
        if len(warnings) > 0:
            explanation = "⚠️ " + " ".join(warnings)
        else:
            explanation = "✅ This contract looks standard. No high-risk keywords found."

        # D. Send Result back to React
        return jsonify({
            "status": "success",
            "filename": filename,
            "risk_score": score,
            "risk_level": level,
            "explanation": explanation
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to process PDF"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)