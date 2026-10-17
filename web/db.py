"""SQLite database management for user orders, licenses, and downloads."""

from __future__ import annotations

import secrets
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


DB_PATH = Path("data/marketplace.db")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def get_db(db_path: Path | str | None = None) -> sqlite3.Connection:
    target = Path(db_path if db_path is not None else DB_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | str | None = None) -> None:
    conn = get_db(db_path)
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                order_ref TEXT UNIQUE NOT NULL,
                tier TEXT NOT NULL, -- 'one_off' or 'subscription'
                amount_gbp INTEGER NOT NULL,
                status TEXT NOT NULL, -- 'paid', 'pending', 'cancelled'
                stripe_session_id TEXT,
                access_token TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                file_type TEXT NOT NULL, -- 'csv' or 'xlsx'
                downloaded_at TEXT NOT NULL,
                ip_address TEXT,
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
        """)


def create_or_get_customer(email: str, db_path: Path | str | None = None) -> int:
    conn = get_db(db_path)
    email = email.strip().lower()
    with conn:
        cur = conn.execute("SELECT id FROM customers WHERE email = ?", (email,))
        row = cur.fetchone()
        if row:
            return row["id"]
        cur = conn.execute("INSERT INTO customers (email, created_at) VALUES (?, ?)", (email, _now_iso()))
        return cur.lastrowid


def create_order(
    email: str,
    tier: str,
    amount_gbp: int,
    stripe_session_id: Optional[str] = None,
    status: str = "paid",
    db_path: Path | str | None = None,
) -> dict:
    customer_id = create_or_get_customer(email, db_path=db_path)
    order_ref = f"ORD-{secrets.token_hex(4).upper()}"
    access_token = secrets.token_urlsafe(32)
    conn = get_db(db_path)
    with conn:
        cur = conn.execute(
            """
            INSERT INTO orders (customer_id, order_ref, tier, amount_gbp, status, stripe_session_id, access_token, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (customer_id, order_ref, tier, amount_gbp, status, stripe_session_id, access_token, _now_iso()),
        )
        order_id = cur.lastrowid
    return {
        "id": order_id,
        "customer_id": customer_id,
        "order_ref": order_ref,
        "email": email,
        "tier": tier,
        "amount_gbp": amount_gbp,
        "status": status,
        "access_token": access_token,
    }


def verify_access_token(token: str, db_path: Path | str | None = None) -> Optional[dict]:
    if not token:
        return None
    conn = get_db(db_path)
    cur = conn.execute(
        """
        SELECT o.id, o.order_ref, o.tier, o.amount_gbp, o.status, o.access_token, o.created_at, c.email
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        WHERE o.access_token = ? AND o.status = 'paid'
        """,
        (token,),
    )
    row = cur.fetchone()
    if row:
        return dict(row)
    return None


def record_download(order_id: int, file_type: str, ip_address: str = "", db_path: Path | str | None = None) -> None:
    conn = get_db(db_path)
    with conn:
        conn.execute(
            "INSERT INTO downloads (order_id, file_type, downloaded_at, ip_address) VALUES (?, ?, ?, ?)",
            (order_id, file_type, _now_iso(), ip_address),
        )
