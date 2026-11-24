from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.models.job import JobDiagnostics


class PanoramaMetadata(BaseModel):
    panorama_id: str
    job_id: str
    title: str
    filename: str
    image_url: str
    thumbnail_url: Optional[str] = None
    width: int
    height: int
    aspect_ratio: float
    file_size_bytes: int
    input_image_count: int
    usable_image_count: int
    processing_time_seconds: float
    is_full_360: bool
    horizontal_fov: float
    vertical_fov: float
    stitching_method: str
    created_at: str
    diagnostics: Optional[JobDiagnostics] = None


class PanoramaViewerConfig(BaseModel):
    panorama_id: str
    image_url: str
    type: str = "equirectangular"  # equirectangular or partial
    is_full_360: bool
    haov: float = 360.0  # Horizontal angle of view
    vaov: float = 180.0  # Vertical angle of view
    v_offset: float = 0.0
    auto_rotate: float = -2.0  # Slow smooth auto-rotation
    compass: bool = True
    hfov: float = 100.0
    min_hfov: float = 40.0
    max_hfov: float = 120.0
    title: str
    description: str
