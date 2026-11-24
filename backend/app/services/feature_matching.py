"""
Stage 3: Feature Matching Service

Theoretical Background:
Because ORB produces 256-bit binary descriptors, distance between feature vectors is measured
via Hamming distance (the count of bit positions in which the bits differ).
OpenCV's BFMatcher (Brute-Force Matcher) with cv2.NORM_HAMMING performs bitwise XOR and
popcount operations, which execute in hardware instructions on modern CPUs.

Lowe's Ratio Test:
For each keypoint in Image A, we find the two closest keypoint candidates (k=2) in Image B:
m (best match) and n (second-best match).
If m.distance < ratio_threshold * n.distance (typically 0.75), the match is considered distinctive
and unambiguous. If m and n have similar distances, the feature is repetitive or ambiguous (e.g.
grass, plain wall texture, repetitive brick patterns) and is rejected to avoid false correspondences.
"""

from typing import List, Tuple, Optional, Dict, Any
import cv2
import numpy as np

from backend.app.core.config import settings
from backend.app.services.feature_detection import ImageFeatures


class MatchResult:
    """
    Data container holding feature correspondence results between an image pair.
    """
    def __init__(
        self,
        idx_a: int,
        idx_b: int,
        filename_a: str,
        filename_b: str,
        good_matches: List[cv2.DMatch],
        raw_matches_count: int,
        kp_count_a: int,
        kp_count_b: int,
        is_sufficient: bool,
        error_message: Optional[str] = None
    ):
        self.idx_a = idx_a
        self.idx_b = idx_b
        self.filename_a = filename_a
        self.filename_b = filename_b
        self.good_matches = good_matches
        self.match_count = len(good_matches)
        self.raw_matches_count = raw_matches_count
        self.kp_count_a = kp_count_a
        self.kp_count_b = kp_count_b
        self.is_sufficient = is_sufficient
        self.error_message = error_message


def match_orb_descriptors(
    features_a: ImageFeatures,
    features_b: ImageFeatures,
    ratio_threshold: float = settings.MATCH_RATIO_THRESH
) -> MatchResult:
    """
    Matches binary ORB descriptors between Image A and Image B using BFMatcher with Hamming distance
    and filters out false correspondences using Lowe's ratio test.
    """
    des_a = features_a.descriptors
    des_b = features_b.descriptors
    
    kp_count_a = features_a.keypoint_count
    kp_count_b = features_b.keypoint_count

    # Guard: ensure both images have valid descriptors
    if des_a is None or len(des_a) < 2:
        return MatchResult(
            idx_a=features_a.image_index,
            idx_b=features_b.image_index,
            filename_a=features_a.filename,
            filename_b=features_b.filename,
            good_matches=[],
            raw_matches_count=0,
            kp_count_a=kp_count_a,
            kp_count_b=kp_count_b,
            is_sufficient=False,
            error_message=f"Image '{features_a.filename}' has insufficient feature descriptors ({len(des_a) if des_a is not None else 0})."
        )

    if des_b is None or len(des_b) < 2:
        return MatchResult(
            idx_a=features_a.image_index,
            idx_b=features_b.image_index,
            filename_a=features_a.filename,
            filename_b=features_b.filename,
            good_matches=[],
            raw_matches_count=0,
            kp_count_a=kp_count_a,
            kp_count_b=kp_count_b,
            is_sufficient=False,
            error_message=f"Image '{features_b.filename}' has insufficient feature descriptors ({len(des_b) if des_b is not None else 0})."
        )

    # Brute-force matcher using Hamming distance for binary descriptors
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    
    try:
        raw_matches = matcher.knnMatch(des_a, des_b, k=2)
    except Exception as e:
        return MatchResult(
            idx_a=features_a.image_index,
            idx_b=features_b.image_index,
            filename_a=features_a.filename,
            filename_b=features_b.filename,
            good_matches=[],
            raw_matches_count=0,
            kp_count_a=kp_count_a,
            kp_count_b=kp_count_b,
            is_sufficient=False,
            error_message=f"BFMatcher error: {str(e)}"
        )

    # Apply Lowe's ratio test
    good_matches: List[cv2.DMatch] = []
    for pair in raw_matches:
        if len(pair) == 2:
            m, n = pair
            if m.distance < ratio_threshold * n.distance:
                good_matches.append(m)

    min_required = settings.MIN_INLIER_COUNT
    is_sufficient = len(good_matches) >= min_required
    err_msg = None
    if not is_sufficient:
        err_msg = (
            f"Insufficient good matches between '{features_a.filename}' and '{features_b.filename}' "
            f"({len(good_matches)} < {min_required} required). Check camera overlap and visual texture."
        )

    return MatchResult(
        idx_a=features_a.image_index,
        idx_b=features_b.image_index,
        filename_a=features_a.filename,
        filename_b=features_b.filename,
        good_matches=good_matches,
        raw_matches_count=len(raw_matches),
        kp_count_a=kp_count_a,
        kp_count_b=kp_count_b,
        is_sufficient=is_sufficient,
        error_message=err_msg
    )


def extract_matched_coordinates(
    features_src: ImageFeatures,
    features_dst: ImageFeatures,
    matches: List[cv2.DMatch]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extracts matched (x, y) point coordinates for source and destination images.
    Returns: (src_pts, dst_pts) shaped (-1, 1, 2) ready for cv2.findHomography.
    """
    if len(matches) == 0:
        return np.empty((0, 1, 2), dtype=np.float32), np.empty((0, 1, 2), dtype=np.float32)

    src_pts = np.float32([features_src.keypoints[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([features_dst.keypoints[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
    return src_pts, dst_pts
