import os
import shutil
import uuid
from pathlib import Path
from typing import List, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def generate_unique_id(prefix: str = "") -> str:
    unique = uuid.uuid4().hex[:12]
    return f"{prefix}_{unique}" if prefix else unique


def get_job_upload_dir(job_id: str) -> Path:
    job_dir = UPLOADS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


def get_output_path(filename: str) -> Path:
    return OUTPUTS_DIR / filename


def cleanup_job_files(job_id: str):
    job_upload_dir = UPLOADS_DIR / job_id
    if job_upload_dir.exists():
        try:
            shutil.rmtree(job_upload_dir)
        except Exception:
            pass


def delete_output_file(filename: str) -> bool:
    target = OUTPUTS_DIR / filename
    if target.exists():
        try:
            target.unlink()
            return True
        except Exception:
            return False
    return False
