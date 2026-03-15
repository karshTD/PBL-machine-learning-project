def run():
    import pandas as pd
    import sqlite3
    import joblib
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score

    print("[Train] Loading loans.csv...")
    df = pd.read_csv("/app/loans.csv")

    print("[Train] Building SQLite database...")
    conn = sqlite3.connect("/app/loans.db")
    df.to_sql("loans", conn, if_exists="replace", index=False)
    conn.close()
    print(f"[Train] loans.db created with {len(df)} records")

    print("[Train] Training stress predictor...")
    df["employment_encoded"] = LabelEncoder().fit_transform(df["employment_type"])
    df["stress_encoded"] = (df["stress_level"] == "High").astype(int)

    features = [
        "age", "monthly_income", "loan_amount",
        "interest_rate", "tenure_years", "monthly_emi",
        "dependents", "credit_score", "employment_encoded"
    ]

    X = df[features]
    y = df["stress_encoded"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    accuracy = accuracy_score(y_test, model.predict(X_test))
    print(f"[Train] Model accuracy: {accuracy:.2%}")

    joblib.dump(model, "/app/stress_model.pkl")
    print("[Train] stress_model.pkl saved")
    print("[Train] ✅ Setup complete!")

if __name__ == "__main__":
    run()