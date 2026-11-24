"""
Stage 4: Homography Estimation with RANSAC Service

Theoretical Background:
1. Homography:
   A 3x3 projective transformation matrix H that maps 2D homogeneous coordinates from one
   planar perspective image plane to another:
       [x']       [h11  h12  h13]   [x]
       [y']  =  s [h21  h22  h23] * [y]
       [1 ]       [h31  h32  h33]   [1]
   Homography has 8 degrees of freedom, requiring a minimum of 4 non-collinear point correspondences.

2. RANSAC (RANdom SAmple Consensus):
   Feature match sets inevitably contain erroneous correspondences (outliers) caused by repetitive
   patterns, moving elements, or perspective changes. Standard least-squares estimation fails severely
   in the presence of even a single outlier.
   RANSAC solves this by iteratively:
     a) Randomly sampling a minimal subset of 4 point correspondences.
     b) Computing candidate homography H.
     c) Projecting all source points using candidate H and measuring Euclidean reprojection distance
        to destination points: ||dst_i - H * src_i||.
     d) Counting points whose reprojection error is below threshold (inliers).
     e) Returning the homography supported by the largest consensus set of inliers, followed by
        a final refinement step using all inliers.
"""

from typing import Tuple, Optional, Dict, Any, List
import cv2
import numpy as np

from backend.app.core.config import settings
from backend.app.services.feature_detection import ImageFeatures
from backend.app.services.feature_matching import MatchResult, extract_matched_coordinates


class HomographyResult:
    """
    Data container holding homography matrix, inlier masks, and diagnostic metrics.
    """
    def __init__(
        self,
        idx_src: int,
        idx_dst: int,
        filename_src: str,
        filename_dst: str,
        H: Optional[np.ndarray],
        inlier_mask: Optional[np.ndarray],
        inlier_count: int,
        inlier_ratio: float,
        is_valid: bool,
        reprojection_thresh: float,
        error_message: Optional[str] = None
    ):
        self.idx_src = idx_src
        self.idx_dst = idx_dst
        self.filename_src = filename_src
        self.filename_dst = filename_dst
        self.H = H
        self.inlier_mask = inlier_mask
        self.inlier_count = inlier_count
        self.inlier_ratio = inlier_ratio
        self.is_valid = is_valid
        self.reprojection_thresh = reprojection_thresh
        self.error_message = error_message


def is_homography_stable(
    H: np.ndarray,
    src_shape: Tuple[int, int],
    min_det_abs: float = 1e-4,
    max_area_ratio: float = 10.0,
    min_area_ratio: float = 0.1
) -> Tuple[bool, str]:
    """
    Validates geometric stability of candidate homography H to reject degenerate,
    inverted, or extreme perspective warps.
    """
    if H is None or H.shape != (3, 3):
        return False, "Homography matrix is None or incorrect shape."

    # Check determinant (non-singular)
    det = np.linalg.det(H)
    if np.isnan(det) or np.isinf(det) or abs(det) < min_det_abs:
        return False, f"Singular homography matrix (determinant: {det:.2e})."

    # Test corner transformation: project 4 image corners
    h, w = src_shape
    corners_src = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
    try:
        corners_dst = cv2.perspectiveTransform(corners_src, H).reshape(-1, 2)
    except Exception as e:
        return False, f"Perspective transform failed on corners: {str(e)}"

    # Check for NaN / Inf in transformed coordinates
    if np.any(np.isnan(corners_dst)) or np.any(np.isinf(corners_dst)):
        return False, "Projected corner coordinates contain NaN or Inf."

    # Check that projected polygon is convex and vertices are in consistent winding order
    # (cv2.isContourConvex checks if polygon is non-self-intersecting and convex)
    contour = corners_dst.reshape(-1, 1, 2).astype(np.int32)
    if not cv2.isContourConvex(contour):
        return False, "Projected image boundary forms a self-intersecting or non-convex polygon."

    # Area preservation sanity check
    orig_area = float(w * h)
    proj_area = cv2.contourArea(contour)
    if proj_area <= 0:
        return False, "Projected polygon has negative or zero area."

    area_ratio = proj_area / orig_area
    if area_ratio < min_area_ratio or area_ratio > max_area_ratio:
        return False, f"Extreme perspective magnification/shrinkage (area ratio: {area_ratio:.2f})."

    return True, "Stable transformation."


def estimate_homography_ransac(
    features_src: ImageFeatures,
    features_dst: ImageFeatures,
    match_result: MatchResult,
    ransac_thresh: float = settings.RANSAC_REPROJ_THRESH,
    min_inliers: int = settings.MIN_INLIER_COUNT,
    min_inlier_ratio: float = settings.MIN_INLIER_RATIO
) -> HomographyResult:
    """
    Estimates homography matrix mapping features_src to features_dst using RANSAC.
    Performs rigorous validation of inlier counts, inlier ratios, and geometric stability.
    """
    matches = match_result.good_matches
    idx_src = features_src.image_index
    idx_dst = features_dst.image_index
    fn_src = features_src.filename
    fn_dst = features_dst.filename

    # At least 4 non-collinear point pairs required mathematically
    if len(matches) < 4:
        return HomographyResult(
            idx_src=idx_src,
            idx_dst=idx_dst,
            filename_src=fn_src,
            filename_dst=fn_dst,
            H=None,
            inlier_mask=None,
            inlier_count=0,
            inlier_ratio=0.0,
            is_valid=False,
            reprojection_thresh=ransac_thresh,
            error_message=f"Only {len(matches)} matches found between '{fn_src}' and '{fn_dst}' (minimum 4 required for homography)."
        )

    src_pts, dst_pts = extract_matched_coordinates(features_src, features_dst, matches)

    try:
        H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, ransac_thresh)
    except Exception as e:
        return HomographyResult(
            idx_src=idx_src,
            idx_dst=idx_dst,
            filename_src=fn_src,
            filename_dst=fn_dst,
            H=None,
            inlier_mask=None,
            inlier_count=0,
            inlier_ratio=0.0,
            is_valid=False,
            reprojection_thresh=ransac_thresh,
            error_message=f"cv2.findHomography RANSAC execution failed: {str(e)}"
        )

    if H is None or mask is None:
        return HomographyResult(
            idx_src=idx_src,
            idx_dst=idx_dst,
            filename_src=fn_src,
            filename_dst=fn_dst,
            H=None,
            inlier_mask=None,
            inlier_count=0,
            inlier_ratio=0.0,
            is_valid=False,
            reprojection_thresh=ransac_thresh,
            error_message=f"RANSAC could not find a geometrically consistent homography between '{fn_src}' and '{fn_dst}'."
        )

    inlier_count = int(np.sum(mask))
    inlier_ratio = inlier_count / float(len(matches)) if len(matches) > 0 else 0.0

    if inlier_count < min_inliers:
        return HomographyResult(
            idx_src=idx_src,
            idx_dst=idx_dst,
            filename_src=fn_src,
            filename_dst=fn_dst,
            H=H,
            inlier_mask=mask,
            inlier_count=inlier_count,
            inlier_ratio=inlier_ratio,
            is_valid=False,
            reprojection_thresh=ransac_thresh,
            error_message=(
                f"RANSAC inlier count ({inlier_count}) below minimum threshold ({min_inliers}) "
                f"between '{fn_src}' and '{fn_dst}'."
            )
        )

    if inlier_ratio < min_inlier_ratio:
        return HomographyResult(
            idx_src=idx_src,
            idx_dst=idx_dst,
            filename_src=fn_src,
            filename_dst=fn_dst,
            H=H,
            inlier_mask=mask,
            inlier_count=inlier_count,
            inlier_ratio=inlier_ratio,
            is_valid=False,
            reprojection_thresh=ransac_thresh,
            error_message=(
                f"RANSAC inlier ratio ({inlier_ratio:.1%}) below threshold ({min_inlier_ratio:.1%}) "
                f"between '{fn_src}' and '{fn_dst}'."
            )
        )

    # Stability validation
    stable, reason = is_homography_stable(H, features_src.image_shape)
    if not stable:
        return HomographyResult(
            idx_src=idx_src,
            idx_dst=idx_dst,
            filename_src=fn_src,
            filename_dst=fn_dst,
            H=H,
            inlier_mask=mask,
            inlier_count=inlier_count,
            inlier_ratio=inlier_ratio,
            is_valid=False,
            reprojection_thresh=ransac_thresh,
            error_message=f"Homography rejected due to instability: {reason}"
        )

    return HomographyResult(
        idx_src=idx_src,
        idx_dst=idx_dst,
        filename_src=fn_src,
        filename_dst=fn_dst,
        H=H,
        inlier_mask=mask,
        inlier_count=inlier_count,
        inlier_ratio=inlier_ratio,
        is_valid=True,
        reprojection_thresh=ransac_thresh,
        error_message=None
    )
