"""SQLite audit log: every reviewer decision, with evidence and model version."""
import sqlite3
from datetime import datetime
import pandas as pd

DB = "audit_log.db"


def _conn():
    return sqlite3.connect(DB)


def init_db():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT, claim TEXT, status TEXT, reason TEXT, confidence REAL,
            evidence TEXT, source TEXT, decision TEXT, model_version TEXT)""")


def log_decision(result: dict, decision: str, model_version: str):
    with _conn() as c:
        c.execute(
            "INSERT INTO decisions (ts, claim, status, reason, confidence, "
            "evidence, source, decision, model_version) VALUES (?,?,?,?,?,?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), result["claim"],
             result["status"], result["reason"], result["confidence"],
             result["evidence"], result["source"], decision, model_version))


def load_decisions() -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql_query("SELECT * FROM decisions ORDER BY id DESC", c)