from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber
import re

app = Flask(__name__)
# KEEP THIS! It allows the connection to work.
CORS(app, resources={r"/*": {"origins": "*"}})

def analyze_risk(text):
    risk_score = 0
    triggered_clauses = []
    
    # Simple keyword dictionary
    risk_keywords = {
        "Arbitration": {"weight": 30, "msg": "Arbitration Clause: You cannot sue in court."},
        "Prepayment Penalty": {"weight": 25, "msg": "Prepayment Penalty: Fines for paying early."},
        "Variable Rate": {"weight": 25, "msg": "Variable Interest Rate: Payments can increase."},
        "Balloon Payment": {"weight": 20, "msg": "Balloon Payment: Huge lump sum due at end."},
        "Waive": {"weight": 10, "msg": "Waiver of Rights: You are giving up legal protections."}
    }

    # Scan text
    for keyword, info in risk_keywords.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
            risk_score += info['weight']
            triggered_clauses.append(info['msg'])

    # Cap score
    if risk_score > 100: risk_score = 100
    if risk_score == 0: risk_score = 10

    # Determine level
    if risk_score > 75: level = "High"
    elif risk_score > 40: level = "Medium"
    else: level = "Low"

    return risk_score, level, triggered_clauses

@app.route('/api/analyze', methods=['POST'])
def analyze_contract():
    print("Received file...") # Debug print

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    filename = file.filename

    try:
        with pdfplumber.open(file) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
        
        # Run the logic
        score, level, warnings = analyze_risk(full_text)
        
        if len(warnings) > 0:
            explanation = "⚠️ Risks Found: " + " ".join(warnings)
        else:
            explanation = "✅ Looks safe. No risky keywords found."

        return jsonify({
            "status": "success",
            "filename": filename,
            "risk_score": score,
            "risk_level": level,
            "explanation": explanation
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to read PDF"}), 500

if __name__ == '__main__':
    # We keep use_reloader=False to prevent the crash you saw earlier
    app.run(debug=True, use_reloader=False, port=5000, host='0.0.0.0')
