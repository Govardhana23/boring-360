from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class JobStage(str, Enum):
    QUEUED = "queued"
    VALIDATING = "validating"
    PREPROCESSING = "preprocessing"
    FEATURE_DETECTION = "feature_detection"
    FEATURE_MATCHING = "feature_matching"
    CAMERA_ALIGNMENT = "camera_alignment"
    IMAGE_WARPING = "image_warping"
    SEAM_BLENDING = "seam_blending"
    GENERATING_PANORAMA = "generating_panorama"
    COMPLETED = "completed"
    FAILED = "failed"


class ImageQualityAssessment(BaseModel):
    filename: str
    width: int
    height: int
    file_size_bytes: int
    laplacian_variance: float
    is_blurry: bool
    mean_brightness: float
    is_underexposed: bool
    is_overexposed: bool
    underexposed_percent: float
    overexposed_percent: float
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class PairwiseOverlapScore(BaseModel):
    image_a: str
    image_b: str
    keypoints_a: int
    keypoints_b: int
    good_matches: int
    estimated_overlap_percent: float
    sufficient_overlap: bool
    warning: Optional[str] = None


class JobDiagnostics(BaseModel):
    input_image_count: int = 0
    usable_image_count: int = 0
    image_assessments: List[ImageQualityAssessment] = Field(default_factory=list)
    pairwise_overlaps: List[PairwiseOverlapScore] = Field(default_factory=list)
    stitching_method_used: str = "OpenCV Built-in Stitcher (PANORAMA)"
    stitching_status_code: int = 0
    stitching_status_message: str = "Success"
    is_full_360: bool = False
    horizontal_fov_degrees: float = 0.0
    vertical_fov_degrees: float = 0.0
    output_width: int = 0
    output_height: int = 0
    aspect_ratio: float = 0.0
    elapsed_time_seconds: float = 0.0
    warnings: List[str] = Field(default_factory=list)
    log_messages: List[str] = Field(default_factory=list)


class JobStatusResponse(BaseModel):
    job_id: str
    panorama_id: Optional[str] = None
    stage: JobStage
    progress_percent: int
    message: str
    error: Optional[str] = None
    created_at: str
    updated_at: str
    diagnostics: Optional[JobDiagnostics] = None
