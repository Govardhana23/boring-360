"""
Boring 360 Pydantic API Schemas
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class StitchResponse(BaseModel):
    """
    Response returned by POST /api/stitch
    """
    success: bool
    panorama_id: str
    panorama_url: str
    processing_time: float = Field(..., description="Actual measured elapsed time in seconds")
    images_processed: int = Field(..., description="Actual number of images preprocessed and stitched")
    feature_algorithm: str = Field(default="ORB", description="Oriented FAST and Rotated BRIEF")
    matching_algorithm: str = Field(default="BFMatcher-Hamming", description="Brute-Force Matcher with Hamming distance")
    alignment_algorithm: str = Field(default="RANSAC-Homography", description="RANSAC Projective Homography Estimation")
    message: str
    output_dimensions: Optional[List[int]] = None
    horizontal_fov: Optional[float] = None
    vertical_fov: Optional[float] = None
    projection_type: Optional[str] = None
    inlier_counts: Optional[List[int]] = None
    warnings: Optional[List[str]] = None


class JobStatusResponse(BaseModel):
    """
    Response returned by GET /api/jobs/{job_id}
    """
    job_id: str
    stage: str
    progress_percent: int
    message: str
    panorama_id: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str
    diagnostics: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """
    Response returned by GET /api/health
    """
    status: str = "healthy"
    service: str = "Boring 360 Panorama Processing Engine"
    version: str = "1.0.0"
    opencv_version: str
    feature_detector: str = "OpenCV ORB (Oriented FAST and Rotated BRIEF)"
    matcher: str = "OpenCV BFMatcher (cv2.NORM_HAMMING)"
    alignment: str = "RANSAC Homography"


class PanoramaViewerConfig(BaseModel):
    """
    Response returned by GET /api/panorama/{panorama_id}/viewer for Pannellum
    """
    panorama_id: str
    image_url: str
    type: str = "equirectangular"
    is_full_360: bool = False
    haov: float = 360.0
    vaov: float = 180.0
    v_offset: float = 0.0
    auto_rotate: float = -1.5
    compass: bool = True
    hfov: float = 100.0
    min_hfov: float = 30.0
    max_hfov: float = 120.0
    title: str = "Boring 360 Panorama"
    description: Optional[str] = None
