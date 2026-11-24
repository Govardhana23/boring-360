import cv2
import numpy as np
from typing import Tuple, List, Optional


def get_feature_detector(method: str = "SIFT", max_features: int = 2500):
    """
    Factory for feature detectors: SIFT or ORB.
    SIFT is scale- and rotation-invariant with float descriptors.
    ORB is fast and binary.
    """
    if method.upper() == "SIFT":
        try:
            return cv2.SIFT_create(nfeatures=max_features)
        except Exception:
            return cv2.ORB_create(nfeatures=max_features)
    elif method.upper() == "ORB":
        return cv2.ORB_create(nfeatures=max_features)
    else:
        return cv2.SIFT_create(nfeatures=max_features)


def detect_and_compute_features(
    image_bgr: np.ndarray, method: str = "SIFT", max_features: int = 2500
) -> Tuple[List[cv2.KeyPoint], Optional[np.ndarray]]:
    """
    Extracts keypoints and descriptors from a BGR image.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    detector = get_feature_detector(method, max_features)
    keypoints, descriptors = detector.detectAndCompute(gray, None)
    return keypoints, descriptors


def draw_keypoints_preview(image_bgr: np.ndarray, keypoints: List[cv2.KeyPoint]) -> np.ndarray:
    """
    Draws rich keypoint circles for debugging/visualization.
    """
    return cv2.drawKeypoints(
        image_bgr,
        keypoints,
        None,
        color=(0, 255, 255),
        flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS
    )
