

# Explainable Loan Stress Analysis System (PBL-I)

## Project Overview

This project implements an **explainable machine learning system** to analyze financial stress associated with loan and EMI commitments.
Instead of only calculating EMI, the system evaluates whether a borrower is under **Low, Medium, or High financial stress**, explains the reasoning behind the prediction, and supports comparative analysis between loan options.

The project is developed as part of **Project Based Learning – I (PBL-I)** and follows a structured, evaluation-oriented workflow.

---

## Problem Statement

Most borrowers rely on simple EMI calculators that do not evaluate long-term financial stress or explain loan risk.
There is a need for a system that:

* Considers multiple financial parameters
* Classifies financial stress levels
* Provides transparent, explainable decisions
* Assists in comparing loan alternatives

---

## Objectives

* Generate realistic loan and borrower data
* Validate financial stress logic through exploratory analysis
* Build an interpretable machine learning model
* Explain model predictions using feature importance and explainability methods
* Design a scalable architecture suitable for document-based inputs

---

## System Overview

The system follows a layered approach:

1. Financial data is collected or generated
2. Key features such as EMI ratio and income burden are computed
3. A machine learning model predicts stress level
4. The prediction is explained using interpretable techniques
5. The result can be extended to advisory and comparison use cases

This separation allows the ML logic to remain independent of user interfaces or document formats.

---

## Technology Stack

### Machine Learning & Backend

* Python 3.10
* NumPy
* Pandas
* Scikit-learn
* Matplotlib
* Seaborn
* SHAP (for explainability)

### Development Tools

* Jupyter Notebook
* Cursor (VS Code based)
* Git and GitHub

### Frontend (Planned / Future Scope)

* React.js
* JavaScript
* REST API using FastAPI

---

## Project Structure

```
PBL/
│
├── dataset/
│   └── loans.csv
│
├── notebooks/
│   ├── 01_data_generation.ipynb
│   ├── 02_eda_validation.ipynb
│   └── 03_ml_stress_prediction.ipynb
│
├── venv/
│
├── .vscode/
│   └── settings.json
│
└── README.md
```

---

## Notebook Breakdown

### 1. Data Generation

**`01_data_generation.ipynb`**

* Synthetic but realistic loan data generation
* EMI computation using standard financial formulas
* Stress classification based on EMI-to-income ratio
* Balanced class distribution for effective ML training
* Output saved as `loans.csv`

---

### 2. Exploratory Data Analysis (EDA)

**`02_eda_validation.ipynb`**

* Dataset sanity checks
* Stress level distribution analysis
* Validation of stress logic using EMI ratio
* Visual inspection of income vs EMI relationships

Purpose: to ensure that labels and patterns are logically correct before modeling.

---

### 3. Machine Learning and Explainability

**`03_ml_stress_prediction.ipynb`**

* Decision Tree classifier for interpretable modeling
* Stratified train-test split
* Model evaluation using precision, recall, and F1-score
* Feature importance analysis
* Clear explanation of which financial factors influence stress predictions

This notebook represents the core intelligence of the system.

---

## Explainability Focus

The project prioritizes **interpretability over black-box accuracy**.
Decision Trees and feature importance are used to ensure predictions can be explained in human terms, such as:

* High EMI relative to income increases stress
* Higher income reduces financial burden
* Loan amount and tenure influence long-term risk

This makes the system suitable for real-world financial reasoning and academic evaluation.

---

## Evaluation Criteria

* Logical correctness of stress classification
* Balanced model performance across all stress categories
* Interpretability of model decisions
* Alignment between financial domain knowledge and ML behavior

---

## Frontend and Document Integration (Future Scope)

Planned extensions include:

* Uploading loan or EMI documents (PDFs)
* Extracting financial information from documents
* Comparing multiple loan scenarios
* Providing actionable financial advice through a web interface

The ML system is designed to operate as a backend service that can be accessed through APIs by a frontend application.

---

## Limitations

* The dataset is synthetic and may not capture all real-world edge cases
* PDF document parsing is not yet implemented
* The project is designed as an academic prototype

---

## Future Enhancements

* Integration with real loan documents
* Advanced explainability using SHAP visualizations
* Web-based user interface
* Comparative loan recommendation engine

---

## Academic Context

This project is developed as part of **Project Based Learning – I (PBL-I)** and demonstrates:

* Problem identification and system design
* Use of modern engineering tools
* Data validation and model evaluation
* Explainable machine learning principles

---

## Key Takeaway

This project demonstrates how explainable machine learning can be applied to financial decision-making, emphasizing transparency, reasoning, and practical relevance rather than black-box predictions.

---

