"""
Boring 360 - Configuration and Pipeline Parameters
"""
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"


class Settings(BaseModel):
    PROJECT_NAME: str = "Boring 360"
    API_V1_STR: str = "/api"
    
    # Storage
    UPLOADS_DIR: Path = UPLOADS_DIR
    OUTPUTS_DIR: Path = OUTPUTS_DIR
    
    # Image constraints
    MIN_IMAGES: int = 8
    MAX_IMAGES: int = 12
    MIN_IMAGES_ABSOLUTE: int = 2  # Allows running unit tests / custom sequences
    MAX_FILE_SIZE_BYTES: int = 25 * 1024 * 1024  # 25MB
    MAX_IMAGE_DIMENSION: int = 1920
    MIN_IMAGE_DIMENSION: int = 300
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".webp"}
    
    # ORB Feature Detector parameters
    # ORB stands for Oriented FAST and Rotated BRIEF
    ORB_N_FEATURES: int = 5000
    ORB_SCALE_FACTOR: float = 1.2
    ORB_N_LEVELS: int = 8
    ORB_EDGE_THRESHOLD: int = 31
    ORB_PATCH_SIZE: int = 31
    
    # Matching and RANSAC parameters
    MATCH_RATIO_THRESH: float = 0.75  # Lowe's ratio test
    RANSAC_REPROJ_THRESH: float = 5.0  # OpenCV RANSAC reprojection error in pixels
    MIN_INLIER_COUNT: int = 12  # Minimum inliers required for reliable homography
    MIN_INLIER_RATIO: float = 0.15  # Minimum ratio of inliers to good matches
    
    # Canvas constraints
    MAX_CANVAS_WIDTH: int = 16000
    MAX_CANVAS_HEIGHT: int = 8000


settings = Settings()
