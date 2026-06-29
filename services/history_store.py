from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from supabase import create_client
except Exception:  # optional dependency path for constrained hosts
    create_client = None


class HistoryStore:
    def __init__(self, db_path: Path = Path("data/history.db")) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_sqlite()
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_key = os.getenv("SUPABASE_KEY", "")
        self.supabase_table = os.getenv("SUPABASE_TABLE", "leaflet_history")
        self.supabase = None
        if self.supabase_url and self.supabase_key and create_client:
            self.supabase = create_client(self.supabase_url, self.supabase_key)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_sqlite(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS catalogues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    retailer TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    validity TEXT,
                    source_label TEXT,
                    first_seen TEXT NOT NULL,
                    UNIQUE(retailer, url, file_hash)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_date TEXT NOT NULL,
                    new_count INTEGER NOT NULL,
                    old_count INTEGER NOT NULL,
                    generated_reports INTEGER NOT NULL DEFAULT 0
                )
                """
            )

    def seen_catalogue(self, retailer: str, url: str, file_hash: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM catalogues WHERE retailer = ? AND url = ? AND file_hash = ?",
                (retailer, url, file_hash),
            ).fetchone()
        return row is not None

    def add_catalogue(self, item: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO catalogues
                (retailer, title, url, file_hash, validity, source_label, first_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.get("retailer", ""),
                    item.get("title", ""),
                    item.get("url", ""),
                    item.get("file_hash", ""),
                    item.get("validity", ""),
                    item.get("source_label", ""),
                    now,
                ),
            )
        if self.supabase:
            self.supabase.table(self.supabase_table).upsert({**item, "first_seen": now}).execute()

    def record_scan(self, new_count: int, old_count: int, generated_reports: int = 0) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO scans (scan_date, new_count, old_count, generated_reports) VALUES (?, ?, ?, ?)",
                (datetime.now(timezone.utc).isoformat(), new_count, old_count, generated_reports),
            )

    def last_scan(self) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT scan_date, new_count, old_count, generated_reports FROM scans ORDER BY id DESC LIMIT 1"
            ).fetchone()
        if not row:
            return None
        return {"scan_date": row[0], "new_count": row[1], "old_count": row[2], "generated_reports": row[3]}

    def export_json(self) -> str:
        with self._connect() as conn:
            catalogues = [dict(zip(["retailer", "title", "url", "file_hash", "validity", "source_label", "first_seen"], row)) for row in conn.execute("SELECT retailer, title, url, file_hash, validity, source_label, first_seen FROM catalogues")]
            scans = [dict(zip(["scan_date", "new_count", "old_count", "generated_reports"], row)) for row in conn.execute("SELECT scan_date, new_count, old_count, generated_reports FROM scans")]
        return json.dumps({"catalogues": catalogues, "scans": scans}, ensure_ascii=False, indent=2)

    def import_json(self, payload: str) -> None:
        data = json.loads(payload)
        with self._connect() as conn:
            for item in data.get("catalogues", []):
                conn.execute(
                    """
                    INSERT OR IGNORE INTO catalogues
                    (retailer, title, url, file_hash, validity, source_label, first_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (item.get("retailer", ""), item.get("title", ""), item.get("url", ""), item.get("file_hash", ""), item.get("validity", ""), item.get("source_label", ""), item.get("first_seen", "")),
                )
