# ============================================================
# app.py - Main Flask Application
# Project: Online Payment Fraud Detection System
# Tech: Flask + SQLite + Scikit-learn (Random Forest)
# Author: Final Year Student Project
# ============================================================

import os
import pickle
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash

from database import init_db, save_transaction, get_all_transactions, \
                     get_dashboard_stats, get_transaction_by_id

# ---- App setup ----
app = Flask(__name__)
app.secret_key = "fraudguard_secret_2025"   # needed for flash messages

# ---- Path to saved ML model ----
MODEL_PATH   = os.path.join("model", "fraud_model.pkl")
ENCODER_PATH = os.path.join("model", "label_encoder.pkl")

# ---- Load the trained model at startup ----
model         = None
label_encoder = None

def load_model():
    """Load the trained Random Forest model from disk."""
    global model, label_encoder
    try:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        with open(ENCODER_PATH, "rb") as f:
            label_encoder = pickle.load(f)
        print("[Model] Loaded successfully.")
    except FileNotFoundError:
        print("[Model] WARNING: Model file not found. Run model/train_model.py first.")
        model         = None
        label_encoder = None

# ---- Transaction type options (must match training data) ----
TRANSACTION_TYPES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def home():
    """Homepage - project landing page."""
    return render_template("index.html")


@app.route("/predict", methods=["GET"])
def predict_page():
    """Show the fraud detection input form."""
    return render_template("predict.html", tx_types=TRANSACTION_TYPES)


@app.route("/predict", methods=["POST"])
def predict():
    """
    Handle form submission.
    1. Read + validate inputs
    2. Encode transaction type
    3. Run model.predict()
    4. Save to DB
    5. Redirect to result page
    """
    # --- Read form inputs ---
    try:
        amount           = float(request.form.get("amount", 0))
        tx_type          = request.form.get("transaction_type", "")
        sender_old_bal   = float(request.form.get("sender_old_bal", 0))
        sender_new_bal   = float(request.form.get("sender_new_bal", 0))
        receiver_old_bal = float(request.form.get("receiver_old_bal", 0))
        receiver_new_bal = float(request.form.get("receiver_new_bal", 0))
    except ValueError:
        flash("Please enter valid numeric values in all fields.", "danger")
        return redirect(url_for("predict_page"))

    if not tx_type or tx_type not in TRANSACTION_TYPES:
        flash("Please select a valid transaction type.", "danger")
        return redirect(url_for("predict_page"))

    if amount <= 0:
        flash("Transaction amount must be greater than zero.", "danger")
        return redirect(url_for("predict_page"))

    # --- Encode transaction type ---
    if label_encoder is not None:
        try:
            tx_type_encoded = int(label_encoder.transform([tx_type])[0])
        except Exception:
            tx_type_encoded = TRANSACTION_TYPES.index(tx_type)
    else:
        tx_type_encoded = TRANSACTION_TYPES.index(tx_type)

    # --- Build feature array ---
    # Order must match training: [amount, type, old_bal_orig, new_bal_orig, old_bal_dest, new_bal_dest]
    features = np.array([[
        amount,
        tx_type_encoded,
        sender_old_bal,
        sender_new_bal,
        receiver_old_bal,
        receiver_new_bal
    ]])

    # --- Make prediction ---
    if model is not None:
        prediction_raw = model.predict(features)[0]
        probabilities  = model.predict_proba(features)[0]
        is_fraud       = int(prediction_raw) == 1
        confidence     = round(float(probabilities[1 if is_fraud else 0]) * 100, 2)
        prediction     = "FRAUD" if is_fraud else "LEGITIMATE"
    else:
        # Fallback demo logic if model not trained yet
        is_fraud   = (tx_type in ["TRANSFER", "CASH_OUT"]) and (amount > 200000)
        confidence = 72.5 if is_fraud else 91.0
        prediction = "FRAUD" if is_fraud else "LEGITIMATE"
        flash("Note: ML model not loaded. Using demo fallback mode.", "warning")

    # --- Save result to database ---
    tx_id = save_transaction({
        "amount":            amount,
        "transaction_type":  tx_type,
        "sender_old_bal":    sender_old_bal,
        "sender_new_bal":    sender_new_bal,
        "receiver_old_bal":  receiver_old_bal,
        "receiver_new_bal":  receiver_new_bal,
        "prediction":        prediction,
        "confidence":        confidence
    })

    return redirect(url_for("result", tx_id=tx_id))


@app.route("/result/<int:tx_id>")
def result(tx_id):
    """Show prediction result for a specific transaction."""
    tx = get_transaction_by_id(tx_id)
    if not tx:
        flash("Transaction not found.", "danger")
        return redirect(url_for("predict_page"))
    return render_template("result.html", tx=tx)


@app.route("/dashboard")
def dashboard():
    """Admin dashboard with stats and charts."""
    stats  = get_dashboard_stats()
    recent = get_all_transactions(limit=20)
    return render_template("dashboard.html", stats=stats, recent=recent)


@app.route("/about")
def about():
    """About page."""
    return render_template("about.html")


@app.route("/api/stats")
def api_stats():
    """JSON endpoint for dashboard stats (for AJAX/Chart.js use)."""
    return jsonify(get_dashboard_stats())


# ============================================================
# STARTUP
# ============================================================
if __name__ == "__main__":
    os.makedirs("model", exist_ok=True)
    init_db()
    load_model()
    print("\n[FraudGuard] Running at http://127.0.0.1:5000\n")
    app.run(debug=True, port=5000)
