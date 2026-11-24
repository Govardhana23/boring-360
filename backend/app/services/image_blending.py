import cv2
import numpy as np
from typing import Tuple, List, Optional


def auto_crop_panorama(stitched: np.ndarray, tolerance: int = 5) -> np.ndarray:
    """
    Trims black outer borders around the stitched panorama canvas
    while preserving the full panorama width and height.
    """
    if stitched is None or stitched.size == 0:
        return stitched

    gray = cv2.cvtColor(stitched, cv2.COLOR_BGR2GRAY)
    mask = (gray > tolerance).astype(np.uint8)

    # Calculate row and column content density
    h, w = gray.shape
    col_counts = np.sum(mask, axis=0)
    row_counts = np.sum(mask, axis=1)

    # Keep columns and rows where at least 5% of pixels have valid image content
    valid_cols = np.where(col_counts > 0.05 * h)[0]
    valid_rows = np.where(row_counts > 0.05 * w)[0]

    if len(valid_cols) == 0 or len(valid_rows) == 0:
        return stitched

    x1, x2 = valid_cols[0], valid_cols[-1]
    y1, y2 = valid_rows[0], valid_rows[-1]

    # Ensure cropped area is meaningful
    if (x2 - x1) > 100 and (y2 - y1) > 100:
        return stitched[y1:y2 + 1, x1:x2 + 1]

    return stitched


def linear_feather_blend(img_base: np.ndarray, img_warp: np.ndarray) -> np.ndarray:
    """
    Blends two registered images on a shared canvas.
    Non-overlapping regions retain 100% of their source pixels.
    Only the mutual overlap seam is smoothly feathered, preventing ghosting and double exposure.
    """
    gray_base = cv2.cvtColor(img_base, cv2.COLOR_BGR2GRAY)
    gray_warp = cv2.cvtColor(img_warp, cv2.COLOR_BGR2GRAY)

    mask_base = (gray_base > 2).astype(np.uint8)
    mask_warp = (gray_warp > 2).astype(np.uint8)

    # Overlap region where both images have valid content
    overlap = cv2.bitwise_and(mask_base, mask_warp)
    only_base = cv2.subtract(mask_base, overlap)
    only_warp = cv2.subtract(mask_warp, overlap)

    output = np.zeros_like(img_base)

    # 1. Non-overlapping areas take 100% of the respective image
    output[only_base > 0] = img_base[only_base > 0]
    output[only_warp > 0] = img_warp[only_warp > 0]

    # 2. Overlapping seam region is smoothly feathered
    if np.any(overlap > 0):
        dist_base = cv2.distanceTransform(mask_base, cv2.DIST_L2, 5)
        dist_warp = cv2.distanceTransform(mask_warp, cv2.DIST_L2, 5)

        sum_dist = dist_base + dist_warp
        sum_dist[sum_dist == 0] = 1.0

        w_base = dist_base / sum_dist
        w_warp = dist_warp / sum_dist

        w_base_3d = np.repeat(w_base[:, :, np.newaxis], 3, axis=2)
        w_warp_3d = np.repeat(w_warp[:, :, np.newaxis], 3, axis=2)

        blended_seam = (
            img_base.astype(np.float32) * w_base_3d + img_warp.astype(np.float32) * w_warp_3d
        )
        blended_seam = np.clip(blended_seam, 0, 255).astype(np.uint8)

        overlap_3d = np.repeat(overlap[:, :, np.newaxis], 3, axis=2) > 0
        output[overlap_3d] = blended_seam[overlap_3d]

    return output
