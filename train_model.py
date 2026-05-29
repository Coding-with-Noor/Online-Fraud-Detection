# ============================================================
# train_model.py - Machine Learning Training Script
# Project: Online Payment Fraud Detection System
#
# What this script does:
#   1. Loads the PaySim dataset (CSV from Kaggle)
#   2. Cleans and preprocesses the data
#   3. Trains Random Forest + Logistic Regression
#   4. Evaluates both models (accuracy, report, confusion matrix)
#   5. Saves the best model + label encoder to disk
#   6. Generates and saves charts (confusion matrix, feature importance)
#
# Run this ONCE before starting the Flask app:
#   cd fraud_detection/
#   python model/train_model.py
# ============================================================

import os
import pickle
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")   # non-interactive backend (no GUI needed)
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection    import train_test_split
from sklearn.preprocessing      import LabelEncoder
from sklearn.ensemble           import RandomForestClassifier
from sklearn.linear_model       import LogisticRegression
from sklearn.metrics            import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score
)

# ============================================================
# STEP 0 — Configuration
# ============================================================

# Where the dataset CSV lives (download from Kaggle — see README)
DATASET_PATH = os.path.join("dataset", "fraud_dataset.csv")

# Where to save trained model files
MODEL_DIR    = "model"
MODEL_PATH   = os.path.join(MODEL_DIR, "fraud_model.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.pkl")

# Where to save charts (Flask will serve these as static files)
CHARTS_DIR   = os.path.join("static", "images")

os.makedirs(CHARTS_DIR, exist_ok=True)

# Columns we will use for training
# (matches what the Flask form sends)
FEATURE_COLS = [
    "amount",
    "type",           # will be encoded to a number
    "oldbalanceOrg",  # sender old balance
    "newbalanceOrig", # sender new balance
    "oldbalanceDest", # receiver old balance
    "newbalanceDest"  # receiver new balance
]
TARGET_COL = "isFraud"


# ============================================================
# STEP 1 — Load Dataset
# ============================================================

def load_data():
    """
    Load the CSV dataset.
    If the real Kaggle file isn't there, generate a small
    synthetic demo dataset so the script still runs.
    """
    if os.path.exists(DATASET_PATH):
        print(f"[Data] Loading dataset from {DATASET_PATH} ...")
        df = pd.read_csv(DATASET_PATH)
        print(f"[Data] Loaded {len(df):,} rows, {df.shape[1]} columns.")
    else:
        print("[Data] Dataset not found — generating synthetic demo data ...")
        print("[Data] (Download the real dataset from Kaggle: paysim1)")
        df = _generate_synthetic_data(n=50000)
        # Save it so subsequent runs are faster
        os.makedirs("dataset", exist_ok=True)
        df.to_csv(DATASET_PATH, index=False)
        print(f"[Data] Synthetic data saved to {DATASET_PATH}")

    return df


def _generate_synthetic_data(n: int = 50000) -> pd.DataFrame:
    """
    Create a realistic-looking synthetic dataset when the real
    Kaggle CSV isn't available.  Mirrors PaySim column names.
    """
    np.random.seed(42)

    tx_types = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]

    # Random transaction types
    types = np.random.choice(tx_types, size=n,
                             p=[0.22, 0.35, 0.04, 0.22, 0.17])

    amounts      = np.random.exponential(scale=50000, size=n).clip(1, 1e7)
    old_bal_orig = np.random.exponential(scale=80000, size=n).clip(0, 5e6)
    new_bal_orig = np.maximum(old_bal_orig - amounts * 0.9, 0)
    old_bal_dest = np.random.exponential(scale=60000, size=n).clip(0, 5e6)
    new_bal_dest = old_bal_dest + amounts * 0.8

    # Fraud label: only TRANSFER and CASH_OUT can be fraud
    is_fraud = np.zeros(n, dtype=int)
    fraud_mask = (
        np.isin(types, ["TRANSFER", "CASH_OUT"]) &
        (amounts > 200000) &
        (new_bal_orig < 1) &          # sender zeroed out
        (np.random.rand(n) < 0.35)    # ~35% of qualifying txns are fraud
    )
    is_fraud[fraud_mask] = 1

    df = pd.DataFrame({
        "step":            np.random.randint(1, 743, n),
        "type":            types,
        "amount":          amounts.round(2),
        "nameOrig":        [f"C{np.random.randint(1e9,9e9)}" for _ in range(n)],
        "oldbalanceOrg":   old_bal_orig.round(2),
        "newbalanceOrig":  new_bal_orig.round(2),
        "nameDest":        [f"M{np.random.randint(1e9,9e9)}" for _ in range(n)],
        "oldbalanceDest":  old_bal_dest.round(2),
        "newbalanceDest":  new_bal_dest.round(2),
        "isFraud":         is_fraud,
        "isFlaggedFraud":  np.zeros(n, dtype=int)
    })

    print(f"[Data] Synthetic stats: {is_fraud.sum():,} fraud / {n:,} total "
          f"({is_fraud.mean()*100:.2f}%)")
    return df


# ============================================================
# STEP 2 — Preprocess
# ============================================================

def preprocess(df: pd.DataFrame):
    """
    Clean and prepare features for training.
    Returns: X (features), y (labels), fitted LabelEncoder
    """
    print("[Preprocess] Starting ...")

    # Drop rows with missing values (usually none in PaySim)
    df = df.dropna(subset=FEATURE_COLS + [TARGET_COL])

    # Keep only the columns we need
    X_raw = df[FEATURE_COLS].copy()
    y     = df[TARGET_COL].astype(int)

    # --- Encode 'type' column (string → integer) ---
    le = LabelEncoder()
    X_raw["type"] = le.fit_transform(X_raw["type"])

    print(f"[Preprocess] Label classes: {dict(zip(le.classes_, le.transform(le.classes_)))}")
    print(f"[Preprocess] Class balance — Fraud: {y.sum():,}  |  Safe: {(y==0).sum():,}")

    return X_raw.values, y.values, le


# ============================================================
# STEP 3 — Train Models
# ============================================================

def train_random_forest(X_train, y_train):
    """Train Random Forest classifier (our main model)."""
    print("\n[RF] Training Random Forest ...")

    rf = RandomForestClassifier(
        n_estimators=100,   # 100 decision trees
        max_depth=15,       # limit depth to avoid overfitting
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1           # use all CPU cores
    )
    rf.fit(X_train, y_train)
    print("[RF] Training complete.")
    return rf


def train_logistic_regression(X_train, y_train):
    """Train Logistic Regression model (for comparison)."""
    print("\n[LR] Training Logistic Regression ...")

    lr = LogisticRegression(
        max_iter=1000,      # more iterations for convergence
        random_state=42,
        solver="lbfgs"
    )
    lr.fit(X_train, y_train)
    print("[LR] Training complete.")
    return lr


# ============================================================
# STEP 4 — Evaluate
# ============================================================

def evaluate_model(name: str, model, X_test, y_test):
    """
    Print accuracy, classification report, ROC-AUC.
    Returns the accuracy score.
    """
    y_pred = model.predict(X_test)
    acc    = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred,
                                   target_names=["Legitimate", "Fraud"])

    try:
        auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    except Exception:
        auc = None

    print(f"\n{'='*50}")
    print(f"  {name} Results")
    print(f"{'='*50}")
    print(f"  Accuracy : {acc * 100:.2f}%")
    if auc:
        print(f"  ROC-AUC  : {auc:.4f}")
    print(f"\n{report}")

    return acc, y_pred


# ============================================================
# STEP 5 — Charts
# ============================================================

def save_confusion_matrix(name: str, y_test, y_pred, filename: str):
    """
    Save a styled confusion matrix heatmap as PNG.
    Used on the dashboard page.
    """
    cm = confusion_matrix(y_test, y_pred)

    fig, ax = plt.subplots(figsize=(5, 4))
    fig.patch.set_facecolor("#161b22")
    ax.set_facecolor("#161b22")

    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="YlOrRd",
        xticklabels=["Legitimate", "Fraud"],
        yticklabels=["Legitimate", "Fraud"],
        ax=ax,
        linewidths=0.5,
        linecolor="#30363d",
        annot_kws={"size": 13, "weight": "bold", "color": "white"}
    )

    ax.set_title(f"Confusion Matrix — {name}", color="white", pad=12, fontsize=12)
    ax.set_xlabel("Predicted",  color="#7d8590", labelpad=8)
    ax.set_ylabel("Actual",     color="#7d8590", labelpad=8)
    ax.tick_params(colors="white")

    # Style colorbar
    cbar = ax.collections[0].colorbar
    cbar.ax.tick_params(colors="white")

    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, filename)
    plt.savefig(out_path, dpi=120, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"[Chart] Confusion matrix saved → {out_path}")


def save_feature_importance(rf_model, feature_names: list):
    """
    Bar chart of feature importances from the Random Forest.
    """
    importances = rf_model.feature_importances_
    indices     = np.argsort(importances)[::-1]
    sorted_names  = [feature_names[i] for i in indices]
    sorted_values = importances[indices]

    colors = ["#00d4aa", "#00b4d8", "#4ade80", "#f472b6", "#fb923c", "#fbbf24"]

    fig, ax = plt.subplots(figsize=(6, 4))
    fig.patch.set_facecolor("#161b22")
    ax.set_facecolor("#161b22")

    bars = ax.barh(sorted_names[::-1], sorted_values[::-1],
                   color=colors[::-1], edgecolor="none", height=0.55)

    # Add percentage labels on bars
    for bar, val in zip(bars, sorted_values[::-1]):
        ax.text(val + 0.005, bar.get_y() + bar.get_height()/2,
                f"{val*100:.1f}%", va="center", color="white", fontsize=9)

    ax.set_title("Feature Importance — Random Forest",
                 color="white", pad=10, fontsize=11)
    ax.set_xlabel("Importance Score", color="#7d8590", labelpad=6)
    ax.tick_params(colors="white", labelsize=9)
    ax.spines[:].set_color("#30363d")
    ax.set_xlim(0, max(sorted_values) * 1.25)

    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "feature_importance.png")
    plt.savefig(out_path, dpi=120, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"[Chart] Feature importance saved → {out_path}")


def save_model_comparison_chart(rf_acc: float, lr_acc: float):
    """
    Simple bar chart comparing both models side-by-side.
    """
    models  = ["Random Forest", "Logistic Regression"]
    scores  = [rf_acc * 100, lr_acc * 100]
    colors  = ["#00d4aa", "#a78bfa"]

    fig, ax = plt.subplots(figsize=(5, 3.5))
    fig.patch.set_facecolor("#161b22")
    ax.set_facecolor("#161b22")

    bars = ax.bar(models, scores, color=colors, width=0.45,
                  edgecolor="none", zorder=3)

    # Label bars
    for bar, sc in zip(bars, scores):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() - 2,
                f"{sc:.2f}%", ha="center", va="top",
                color="black", fontweight="bold", fontsize=11)

    ax.set_ylim(0, 105)
    ax.set_ylabel("Accuracy (%)", color="#7d8590", labelpad=6)
    ax.set_title("Model Accuracy Comparison", color="white", pad=10, fontsize=11)
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#30363d")
    ax.yaxis.grid(True, color="#30363d", zorder=0)

    plt.tight_layout()
    out_path = os.path.join(CHARTS_DIR, "model_comparison.png")
    plt.savefig(out_path, dpi=120, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"[Chart] Model comparison saved → {out_path}")


# ============================================================
# STEP 6 — Save Model to Disk
# ============================================================

def save_artifacts(model, label_encoder):
    """
    Pickle the trained model and label encoder.
    Flask loads these files at startup.
    """
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    with open(ENCODER_PATH, "wb") as f:
        pickle.dump(label_encoder, f)

    print(f"\n[Save] Model saved    → {MODEL_PATH}")
    print(f"[Save] Encoder saved  → {ENCODER_PATH}")


# ============================================================
# MAIN — Run everything in order
# ============================================================

if __name__ == "__main__":

    print("\n" + "="*55)
    print("  FraudGuard — ML Training Script")
    print("  Random Forest + Logistic Regression")
    print("="*55 + "\n")

    # 1. Load data
    df = load_data()

    # 2. Preprocess
    X, y, label_encoder = preprocess(df)

    # 3. Train/test split  (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\n[Split] Train: {len(X_train):,}  |  Test: {len(X_test):,}")

    # 4. Train both models
    rf_model = train_random_forest(X_train, y_train)
    lr_model = train_logistic_regression(X_train, y_train)

    # 5. Evaluate both
    rf_acc, rf_preds = evaluate_model("Random Forest",       rf_model, X_test, y_test)
    lr_acc, lr_preds = evaluate_model("Logistic Regression", lr_model, X_test, y_test)

    # 6. Save charts
    print("\n[Charts] Generating visualizations ...")
    save_confusion_matrix("Random Forest",       y_test, rf_preds, "cm_rf.png")
    save_confusion_matrix("Logistic Regression", y_test, lr_preds, "cm_lr.png")
    save_feature_importance(rf_model, FEATURE_COLS)
    save_model_comparison_chart(rf_acc, lr_acc)

    # 7. Save the best model (Random Forest wins)
    print("\n[Save] Saving Random Forest as the primary model ...")
    save_artifacts(rf_model, label_encoder)

    # 8. Final summary
    print("\n" + "="*55)
    print("  Training Complete! Summary:")
    print(f"  Random Forest Accuracy    : {rf_acc*100:.2f}%")
    print(f"  Logistic Regression Acc   : {lr_acc*100:.2f}%")
    print(f"  Charts saved to           : static/images/")
    print(f"  Model saved to            : model/fraud_model.pkl")
    print("\n  Next: Run  python app.py  to start the web app.")
    print("="*55 + "\n")
