# ============================================================
# database.py - SQLite Database Helper
# Project: Online Payment Fraud Detection System
# 
# This file handles everything related to the database:
#   - Creating the transactions table
#   - Saving prediction results
#   - Fetching data for dashboard stats
# ============================================================

import sqlite3
import os
from datetime import datetime

# Database file will be created in the project root folder
DB_PATH = "transactions.db"


def get_connection():
    """
    Create and return a database connection.
    Using row_factory lets us access columns by name (like a dict).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # row['column'] instead of row[0]
    return conn


def init_db():
    """
    Create the transactions table if it doesn't already exist.
    Called once at app startup.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            amount            REAL    NOT NULL,
            transaction_type  TEXT    NOT NULL,
            sender_old_bal    REAL    NOT NULL,
            sender_new_bal    REAL    NOT NULL,
            receiver_old_bal  REAL    NOT NULL,
            receiver_new_bal  REAL    NOT NULL,
            prediction        TEXT    NOT NULL,
            confidence        REAL    NOT NULL,
            checked_at        TEXT    NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Database initialized.")


def save_transaction(data: dict) -> int:
    """
    Save a transaction check result to the database.
    Returns the ID of the newly inserted row.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO transactions
            (amount, transaction_type, sender_old_bal, sender_new_bal,
             receiver_old_bal, receiver_new_bal, prediction, confidence, checked_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["amount"],
        data["transaction_type"],
        data["sender_old_bal"],
        data["sender_new_bal"],
        data["receiver_old_bal"],
        data["receiver_new_bal"],
        data["prediction"],
        data["confidence"],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_transaction_by_id(tx_id: int):
    """
    Fetch a single transaction by its ID.
    Returns a dict-like Row object, or None if not found.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,))
    row = cursor.fetchone()
    conn.close()

    # Convert sqlite3.Row to a plain dict so Jinja2 can use it easily
    return dict(row) if row else None


def get_all_transactions(limit: int = 50):
    """
    Fetch the most recent transactions for the dashboard table.
    Returns a list of dicts, newest first.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM transactions
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_dashboard_stats() -> dict:
    """
    Calculate summary statistics for the dashboard.
    Returns counts, percentages, and per-type breakdowns.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Total transactions checked
    cursor.execute("SELECT COUNT(*) FROM transactions")
    total = cursor.fetchone()[0]

    # Fraud count
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE prediction = 'FRAUD'")
    fraud_count = cursor.fetchone()[0]

    # Safe count
    safe_count = total - fraud_count

    # Fraud rate percentage
    fraud_rate = round((fraud_count / total * 100), 1) if total > 0 else 0

    # Average confidence overall
    cursor.execute("SELECT AVG(confidence) FROM transactions")
    avg_conf_raw = cursor.fetchone()[0]
    avg_confidence = round(avg_conf_raw, 1) if avg_conf_raw else 0

    # Breakdown by transaction type
    cursor.execute("""
        SELECT transaction_type,
               COUNT(*) as total,
               SUM(CASE WHEN prediction = 'FRAUD' THEN 1 ELSE 0 END) as fraud
        FROM transactions
        GROUP BY transaction_type
        ORDER BY total DESC
    """)
    type_breakdown = [dict(r) for r in cursor.fetchall()]

    # Last 7 days daily counts (for the line chart)
    cursor.execute("""
        SELECT DATE(checked_at) as day,
               COUNT(*) as total,
               SUM(CASE WHEN prediction = 'FRAUD' THEN 1 ELSE 0 END) as fraud
        FROM transactions
        WHERE checked_at >= DATE('now', '-6 days')
        GROUP BY day
        ORDER BY day ASC
    """)
    daily_trend = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        "total":          total,
        "fraud_count":    fraud_count,
        "safe_count":     safe_count,
        "fraud_rate":     fraud_rate,
        "avg_confidence": avg_confidence,
        "type_breakdown": type_breakdown,
        "daily_trend":    daily_trend
    }
