import cv2
import numpy as np
from typing import Tuple, List, Optional


def match_features_knn(
    des_a: np.ndarray, des_b: np.ndarray, method: str = "SIFT", ratio_threshold: float = 0.75
) -> List[cv2.DMatch]:
    """
    Finds verified feature correspondences using FLANN or BFMatcher with Lowe's ratio test.
    """
    if des_a is None or des_b is None or len(des_a) < 2 or len(des_b) < 2:
        return []

    if method.upper() == "SIFT":
        # FLANN matcher for float descriptors
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        try:
            flann = cv2.FlannBasedMatcher(index_params, search_params)
            matches = flann.knnMatch(des_a, des_b, k=2)
        except Exception:
            bf = cv2.BFMatcher(cv2.NORM_L2)
            matches = bf.knnMatch(des_a, des_b, k=2)
    else:
        # BFMatcher with Hamming distance for binary descriptors (ORB)
        bf = cv2.BFMatcher(cv2.NORM_HAMMING)
        matches = bf.knnMatch(des_a, des_b, k=2)

    good_matches = []
    for pair in matches:
        if len(pair) == 2:
            m, n = pair
            if m.distance < ratio_threshold * n.distance:
                good_matches.append(m)

    return good_matches


def estimate_homography_ransac(
    kp_a: List[cv2.KeyPoint],
    kp_b: List[cv2.KeyPoint],
    matches: List[cv2.DMatch],
    ransac_reproj_thresh: float = 4.0
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], int]:
    """
    Computes homography matrix H from image A to image B using RANSAC.
    Returns (H, inlier_mask, inlier_count).
    """
    if len(matches) < 4:
        return None, None, 0

    pts_a = np.float32([kp_a[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    pts_b = np.float32([kp_b[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

    H, mask = cv2.findHomography(pts_a, pts_b, cv2.RANSAC, ransac_reproj_thresh)
    inliers = int(np.sum(mask)) if mask is not None else 0
    return H, mask, inliers
