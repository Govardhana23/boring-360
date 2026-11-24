import sqlite3
import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "boring360.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            panorama_id TEXT,
            stage TEXT NOT NULL,
            progress_percent INTEGER NOT NULL,
            message TEXT,
            error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            diagnostics_json TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS panoramas (
            panorama_id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            image_url TEXT NOT NULL,
            thumbnail_url TEXT,
            width INTEGER NOT NULL,
            height INTEGER NOT NULL,
            aspect_ratio REAL NOT NULL,
            file_size_bytes INTEGER NOT NULL,
            input_image_count INTEGER NOT NULL,
            usable_image_count INTEGER NOT NULL,
            processing_time_seconds REAL NOT NULL,
            is_full_360 INTEGER NOT NULL,
            horizontal_fov REAL NOT NULL,
            vertical_fov REAL NOT NULL,
            stitching_method TEXT NOT NULL,
            created_at TEXT NOT NULL,
            diagnostics_json TEXT
        )
    """)
    conn.commit()
    conn.close()

# Ensure tables are initialized on import
init_db()


def save_job(job_id: str, stage: str, progress: int, message: str, error: Optional[str] = None, panorama_id: Optional[str] = None, diagnostics: Optional[Dict[str, Any]] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    diag_str = json.dumps(diagnostics) if diagnostics else None

    cursor.execute("SELECT job_id FROM jobs WHERE job_id = ?", (job_id,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE jobs
            SET stage = ?, progress_percent = ?, message = ?, error = ?, panorama_id = COALESCE(?, panorama_id), updated_at = ?, diagnostics_json = COALESCE(?, diagnostics_json)
            WHERE job_id = ?
        """, (stage, progress, message, error, panorama_id, now, diag_str, job_id))
    else:
        cursor.execute("""
            INSERT INTO jobs (job_id, panorama_id, stage, progress_percent, message, error, created_at, updated_at, diagnostics_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (job_id, panorama_id, stage, progress, message, error, now, now, diag_str))

    conn.commit()
    conn.close()


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    if d.get("diagnostics_json"):
        try:
            d["diagnostics"] = json.loads(d["diagnostics_json"])
        except Exception:
            d["diagnostics"] = None
    else:
        d["diagnostics"] = None
    return d


def save_panorama(meta: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    diag_str = json.dumps(meta.get("diagnostics")) if meta.get("diagnostics") else None
    cursor.execute("""
        INSERT OR REPLACE INTO panoramas (
            panorama_id, job_id, title, filename, image_url, thumbnail_url,
            width, height, aspect_ratio, file_size_bytes, input_image_count,
            usable_image_count, processing_time_seconds, is_full_360,
            horizontal_fov, vertical_fov, stitching_method, created_at, diagnostics_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        meta["panorama_id"], meta["job_id"], meta["title"], meta["filename"],
        meta["image_url"], meta.get("thumbnail_url"), meta["width"], meta["height"],
        meta["aspect_ratio"], meta["file_size_bytes"], meta["input_image_count"],
        meta["usable_image_count"], meta["processing_time_seconds"],
        1 if meta["is_full_360"] else 0, meta["horizontal_fov"], meta["vertical_fov"],
        meta["stitching_method"], meta["created_at"], diag_str
    ))
    conn.commit()
    conn.close()


def get_panorama(panorama_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM panoramas WHERE panorama_id = ?", (panorama_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["is_full_360"] = bool(d["is_full_360"])
    if d.get("diagnostics_json"):
        try:
            d["diagnostics"] = json.loads(d["diagnostics_json"])
        except Exception:
            d["diagnostics"] = None
    else:
        d["diagnostics"] = None
    return d


def list_panoramas(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM panoramas ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    res = []
    for row in rows:
        d = dict(row)
        d["is_full_360"] = bool(d["is_full_360"])
        if d.get("diagnostics_json"):
            try:
                d["diagnostics"] = json.loads(d["diagnostics_json"])
            except Exception:
                d["diagnostics"] = None
        res.append(d)
    return res


def delete_panorama_record(panorama_id: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM panoramas WHERE panorama_id = ?", (panorama_id,))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected
