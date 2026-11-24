"""
Stage 5: Image Alignment and Perspective Warping Service

Theoretical Background:
In multi-image stitching, all input photographs must be projected into a unified coordinate system.
1. Reference Image Selection:
   Selecting the central image (anchor = N // 2) as the reference frame splits perspective distortion
   symmetrically left and right, cutting the maximum chain length in half compared to picking image 0.
2. Homography Chaining:
   Pairwise homographies H_{i -> i+1} are chained via matrix multiplication:
     - For images left of center (i < ref): H_{i -> ref} = H_{ref-1 -> ref} * ... * H_{i -> i+1}
     - For the center image (i == ref): H_{ref -> ref} = Identity(3x3)
     - For images right of center (i > ref): H_{i -> ref} = H_{ref+1 -> ref} * ... * H_{i -> i-1}
3. Coordinate Shift and Canvas Bounds:
   Projecting images can produce negative coordinates relative to the reference image frame.
   We transform the four bounding corners of every image by its cumulative homography, compute
   the global bounding envelope (min_x, max_x, min_y, max_y), and prepend a 2D translation matrix
   H_trans = [[1, 0, -min_x], [0, 1, -min_y], [0, 0, 1]] so the entire composite fits on a non-negative
   raster canvas of size (max_x - min_x) x (max_y - min_y).
4. Perspective Warping:
   Each image is transformed onto the global canvas using cv2.warpPerspective() with bilinear
   interpolation and constant zero borders.
"""

from typing import List, Tuple, Dict, Optional, Any
import cv2
import numpy as np

from backend.app.core.config import settings
from backend.app.services.feature_detection import ImageFeatures
from backend.app.services.feature_matching import MatchResult, match_orb_descriptors
from backend.app.services.homography import HomographyResult, estimate_homography_ransac


class AlignmentResult:
    """
    Data container holding the warped images, alpha masks, canvas dimensions,
    and alignment diagnostic metadata.
    """
    def __init__(
        self,
        success: bool,
        canvas_size: Tuple[int, int],  # (width, height)
        warped_images: List[np.ndarray],
        warped_masks: List[np.ndarray],
        cumulative_homographies: List[np.ndarray],
        reference_index: int,
        pairwise_homographies: List[HomographyResult],
        error_message: Optional[str] = None
    ):
        self.success = success
        self.canvas_size = canvas_size
        self.warped_images = warped_images
        self.warped_masks = warped_masks
        self.cumulative_homographies = cumulative_homographies
        self.reference_index = reference_index
        self.pairwise_homographies = pairwise_homographies
        self.error_message = error_message


def compute_adjacent_pairwise_homographies(
    features_list: List[ImageFeatures]
) -> Tuple[List[HomographyResult], Optional[str]]:
    """
    Computes RANSAC homographies between adjacent photographs in the sequence:
    Image i -> Image i+1.
    Detects disconnected pairs early.
    """
    n = len(features_list)
    pairwise_results: List[HomographyResult] = []

    for i in range(n - 1):
        feat_a = features_list[i]
        feat_b = features_list[i + 1]

        # Match A to B
        match_res = match_orb_descriptors(feat_a, feat_b)
        if not match_res.is_sufficient:
            # Try reverse matching B to A in case asymmetric keypoints helped
            match_res_rev = match_orb_descriptors(feat_b, feat_a)
            if match_res_rev.is_sufficient:
                homo_rev = estimate_homography_ransac(feat_b, feat_a, match_res_rev)
                if homo_rev.is_valid and homo_rev.H is not None:
                    # Invert H (B -> A) to get (A -> B)
                    try:
                        H_inv = np.linalg.inv(homo_rev.H)
                        homo_res = HomographyResult(
                            idx_src=i,
                            idx_dst=i + 1,
                            filename_src=feat_a.filename,
                            filename_dst=feat_b.filename,
                            H=H_inv,
                            inlier_mask=homo_rev.inlier_mask,
                            inlier_count=homo_rev.inlier_count,
                            inlier_ratio=homo_rev.inlier_ratio,
                            is_valid=True,
                            reprojection_thresh=homo_rev.reprojection_thresh
                        )
                        pairwise_results.append(homo_res)
                        continue
                    except Exception:
                        pass

            err = (
                f"Disconnected image sequence: cannot link '{feat_a.filename}' (shot {i+1}) "
                f"to '{feat_b.filename}' (shot {i+2}). Insufficient matching features ({match_res.match_count} matches). "
                f"Please ensure 25–40% consecutive photograph overlap."
            )
            return pairwise_results, err

        homo_res = estimate_homography_ransac(feat_a, feat_b, match_res)
        if not homo_res.is_valid:
            err = (
                f"Geometric alignment failed between '{feat_a.filename}' and '{feat_b.filename}': "
                f"{homo_res.error_message or 'RANSAC homography rejected'}. Check for camera rotation/parallax."
            )
            return pairwise_results, err

        pairwise_results.append(homo_res)

    return pairwise_results, None


def align_and_warp_image_sequence(
    images_bgr: List[np.ndarray],
    features_list: List[ImageFeatures]
) -> AlignmentResult:
    """
    Executes Stage 5 alignment:
    1. Computes pairwise transformations between adjacent images.
    2. Designates central image as reference coordinate frame.
    3. Chains homographies to reference frame.
    4. Computes canvas bounding box and non-negative translation matrix.
    5. Warps images and valid pixel masks onto the canvas.
    """
    n = len(images_bgr)
    if n < settings.MIN_IMAGES_ABSOLUTE:
        return AlignmentResult(
            success=False,
            canvas_size=(0, 0),
            warped_images=[],
            warped_masks=[],
            cumulative_homographies=[],
            reference_index=0,
            pairwise_homographies=[],
            error_message=f"At least {settings.MIN_IMAGES_ABSOLUTE} images required for alignment."
        )

    # 1. Compute pairwise transformations: H_pairs[i] maps image i -> image i+1
    h_pairs, err = compute_adjacent_pairwise_homographies(features_list)
    if err or len(h_pairs) != (n - 1):
        return AlignmentResult(
            success=False,
            canvas_size=(0, 0),
            warped_images=[],
            warped_masks=[],
            cumulative_homographies=[],
            reference_index=0,
            pairwise_homographies=h_pairs,
            error_message=err or "Failed to compute complete pairwise homography chain."
        )

    # 2. Select central image as reference anchor
    ref_idx = n // 2

    # 3. Calculate cumulative homographies: H_cum[i] maps image i -> image ref_idx
    # Note: h_pairs[k].H maps image k -> image k+1.
    # Therefore, inverse of h_pairs[k].H maps image k+1 -> image k.
    H_cum: List[np.ndarray] = [np.eye(3, dtype=np.float64) for _ in range(n)]

    # Center image is reference frame
    H_cum[ref_idx] = np.eye(3, dtype=np.float64)

    # For images to the left of reference (ref_idx - 1 down to 0):
    # H_cum[k] = H_cum[k+1] * H_{k -> k+1}
    for k in range(ref_idx - 1, -1, -1):
        H_k_to_next = h_pairs[k].H
        if H_k_to_next is None:
            return AlignmentResult(
                success=False, canvas_size=(0, 0), warped_images=[], warped_masks=[],
                cumulative_homographies=[], reference_index=ref_idx, pairwise_homographies=h_pairs,
                error_message=f"Missing homography matrix at step {k}."
            )
        H_cum[k] = np.dot(H_cum[k + 1], H_k_to_next)

    # For images to the right of reference (ref_idx + 1 up to n - 1):
    # Since h_pairs[k-1].H maps (k-1) -> k, we invert it to map k -> (k-1):
    # H_{k -> k-1} = inv(H_{k-1 -> k})
    # H_cum[k] = H_cum[k-1] * H_{k -> k-1}
    for k in range(ref_idx + 1, n):
        H_prev_to_k = h_pairs[k - 1].H
        if H_prev_to_k is None:
            return AlignmentResult(
                success=False, canvas_size=(0, 0), warped_images=[], warped_masks=[],
                cumulative_homographies=[], reference_index=ref_idx, pairwise_homographies=h_pairs,
                error_message=f"Missing homography matrix at step {k-1}."
            )
        try:
            H_k_to_prev = np.linalg.inv(H_prev_to_k)
        except Exception as e:
            return AlignmentResult(
                success=False, canvas_size=(0, 0), warped_images=[], warped_masks=[],
                cumulative_homographies=[], reference_index=ref_idx, pairwise_homographies=h_pairs,
                error_message=f"Singular homography inversion at step {k}: {str(e)}"
            )
        H_cum[k] = np.dot(H_cum[k - 1], H_k_to_prev)

    # 4. Compute global canvas bounds by projecting corners of all images
    all_projected_corners: List[np.ndarray] = []
    for i in range(n):
        h, w = images_bgr[i].shape[:2]
        corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
        proj = cv2.perspectiveTransform(corners, H_cum[i])
        all_projected_corners.append(proj)

    all_corners_concat = np.concatenate(all_projected_corners, axis=0)
    min_x, min_y = np.int32(all_corners_concat.min(axis=0).ravel() - 0.5)
    max_x, max_y = np.int32(all_corners_concat.max(axis=0).ravel() + 0.5)

    canvas_w = max_x - min_x
    canvas_h = max_y - min_y

    # Check for excessive canvas size
    if canvas_w > settings.MAX_CANVAS_WIDTH or canvas_h > settings.MAX_CANVAS_HEIGHT:
        return AlignmentResult(
            success=False,
            canvas_size=(canvas_w, canvas_h),
            warped_images=[],
            warped_masks=[],
            cumulative_homographies=H_cum,
            reference_index=ref_idx,
            pairwise_homographies=h_pairs,
            error_message=(
                f"Transformation generated excessively large canvas ({canvas_w}x{canvas_h}px > "
                f"{settings.MAX_CANVAS_WIDTH}x{settings.MAX_CANVAS_HEIGHT}px limit). "
                f"Indicates severe cumulative perspective distortion or non-planar camera motion."
            )
        )

    if canvas_w <= 0 or canvas_h <= 0:
        return AlignmentResult(
            success=False, canvas_size=(0, 0), warped_images=[], warped_masks=[],
            cumulative_homographies=H_cum, reference_index=ref_idx, pairwise_homographies=h_pairs,
            error_message="Computed canvas dimensions are non-positive."
        )

    # 5. Translation matrix to offset minimum coordinates to (0, 0)
    H_trans = np.array([
        [1.0, 0.0, -float(min_x)],
        [0.0, 1.0, -float(min_y)],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)

    final_homographies: List[np.ndarray] = []
    warped_images: List[np.ndarray] = []
    warped_masks: List[np.ndarray] = []

    for i in range(n):
        img = images_bgr[i]
        h, w = img.shape[:2]

        H_final = np.dot(H_trans, H_cum[i])
        final_homographies.append(H_final)

        # Warp image
        warped_img = cv2.warpPerspective(
            img,
            H_final,
            (canvas_w, canvas_h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0)
        )
        warped_images.append(warped_img)

        # Warp binary mask to accurately define valid image footprint
        unit_mask = np.ones((h, w), dtype=np.uint8) * 255
        warped_mask = cv2.warpPerspective(
            unit_mask,
            H_final,
            (canvas_w, canvas_h),
            flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0
        )
        warped_masks.append(warped_mask)

    return AlignmentResult(
        success=True,
        canvas_size=(canvas_w, canvas_h),
        warped_images=warped_images,
        warped_masks=warped_masks,
        cumulative_homographies=final_homographies,
        reference_index=ref_idx,
        pairwise_homographies=h_pairs,
        error_message=None
    )
