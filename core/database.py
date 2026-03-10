"""
SQLite persistence — runs and saved reports.
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "hub.db"

def get_conn():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            doc_name    TEXT,
            task        TEXT,
            provider    TEXT,
            model       TEXT,
            prompt      TEXT,
            response    TEXT,
            latency_ms  INTEGER,
            input_tokens  INTEGER,
            output_tokens INTEGER
        );

        CREATE TABLE IF NOT EXISTS reports (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            doc_name    TEXT,
            summary     TEXT,
            full_json   TEXT
        );
    """)
    conn.commit()
    conn.close()

def log_run(doc_name, task, provider, model, prompt, response, latency_ms, input_tokens, output_tokens):
    conn = get_conn()
    conn.execute("""
        INSERT INTO runs (timestamp, doc_name, task, provider, model, prompt, response,
                          latency_ms, input_tokens, output_tokens)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (datetime.utcnow().isoformat(), doc_name, task, provider, model,
          prompt[:500], response[:2000], latency_ms, input_tokens, output_tokens))
    conn.commit()
    conn.close()

def save_report(doc_name, summary, full_data: dict):
    conn = get_conn()
    conn.execute("""
        INSERT INTO reports (timestamp, doc_name, summary, full_json)
        VALUES (?, ?, ?, ?)
    """, (datetime.utcnow().isoformat(), doc_name, summary, json.dumps(full_data)))
    conn.commit()
    conn.close()

def get_runs(limit=200):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM runs ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_reports(limit=50):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM reports ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_stats():
    conn = get_conn()
    stats = {}
    for row in conn.execute("""
        SELECT provider,
               COUNT(*) as calls,
               AVG(latency_ms) as avg_latency,
               SUM(input_tokens + output_tokens) as total_tokens
        FROM runs GROUP BY provider
    """).fetchall():
        stats[row["provider"]] = dict(row)
    conn.close()
    return stats
