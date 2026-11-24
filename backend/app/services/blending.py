"""
Stage 6: Image Blending and Seam Handling Service

Theoretical Background:
When multiple images are warped onto a shared canvas, seams between adjacent photographs can be
visible due to lighting differences (vignetting, auto-exposure changes) and slight geometric misalignment.
1. Exposure Compensation:
   In the mutual overlap zone between adjacent images, we compute the ratio of average luminance.
   A gentle gain compensation factor is applied to smooth out abrupt brightness jumps across exposures.
2. Distance-Transform Feather Blending:
   For each warped image mask, we compute the Euclidean distance transform (cv2.distanceTransform),
   giving each pixel a weight proportional to its distance from the image's outer edge:
     - Pixels deep inside an image's footprint have high weight.
     - Pixels near the boundary taper smoothly toward zero.
   At any pixel (x, y) on the canvas covered by multiple images, the blended color is:
     I_blend(x, y) = sum_i [ W_i(x, y) * I_i(x, y) ] / sum_i [ W_i(x, y) ]
   Where only a single image exists, W_i / sum(W) = 1.0, preserving 100% of the original sharp source pixels.
3. Auto-cropping:
   The warped perspective produces non-rectangular outer black boundaries. We detect the largest
   useful bounding crop rectangle that eliminates outer black padding while preserving maximum panorama width.
"""

from typing import List, Tuple, Optional
import cv2
import numpy as np


def compensate_exposure_gains(
    warped_images: List[np.ndarray],
    warped_masks: List[np.ndarray],
    max_gain_adjustment: float = 0.25
) -> List[np.ndarray]:
    """
    Computes pairwise luminance ratios in overlapping regions and applies
    gentle gain adjustment to eliminate exposure steps between smartphone frames.
    """
    n = len(warped_images)
    if n < 2:
        return warped_images

    compensated = [img.copy() for img in warped_images]

    # Convert to float for calculations
    for i in range(n - 1):
        mask_a = (warped_masks[i] > 128)
        mask_b = (warped_masks[i + 1] > 128)
        overlap = mask_a & mask_b

        overlap_count = np.count_nonzero(overlap)
        if overlap_count < 500:
            continue

        # Compute mean luminance in overlap
        gray_a = cv2.cvtColor(compensated[i], cv2.COLOR_BGR2GRAY)
        gray_b = cv2.cvtColor(compensated[i + 1], cv2.COLOR_BGR2GRAY)

        mean_a = float(np.mean(gray_a[overlap]))
        mean_b = float(np.mean(gray_b[overlap]))

        if mean_a > 10.0 and mean_b > 10.0:
            ratio = mean_a / mean_b
            # Clamp gain to prevent extreme over/under exposure
            clamped_gain = float(np.clip(ratio, 1.0 - max_gain_adjustment, 1.0 + max_gain_adjustment))
            
            # Apply half adjustment to b towards a
            blend_gain = 0.5 * (clamped_gain - 1.0) + 1.0
            compensated[i + 1] = np.clip(compensated[i + 1].astype(np.float32) * blend_gain, 0, 255).astype(np.uint8)

    return compensated


def multi_image_feather_blend(
    warped_images: List[np.ndarray],
    warped_masks: List[np.ndarray]
) -> np.ndarray:
    """
    Blends multiple warped images using distance transform weighting.
    Eliminates visible seams while preserving sharp details.
    """
    n = len(warped_images)
    if n == 0:
        return np.zeros((100, 100, 3), dtype=np.uint8)
    if n == 1:
        return warped_images[0]

    h, w = warped_images[0].shape[:2]

    # First perform exposure compensation across overlaps
    compensated_images = compensate_exposure_gains(warped_images, warped_masks)

    # Compute Euclidean distance transform for each mask
    weight_maps: List[np.ndarray] = []
    for mask in warped_masks:
        binary = (mask > 128).astype(np.uint8)
        if not np.any(binary):
            dist = np.zeros((h, w), dtype=np.float32)
        else:
            dist = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
        weight_maps.append(dist)

    # Sum of weights across all images
    sum_weights = np.zeros((h, w), dtype=np.float32)
    for dist in weight_maps:
        sum_weights += dist

    # Prevent division by zero
    valid_mask = sum_weights > 0
    safe_sum_weights = np.where(valid_mask, sum_weights, 1.0)

    # Accumulate blended color
    blended = np.zeros((h, w, 3), dtype=np.float32)
    for img, dist in zip(compensated_images, weight_maps):
        norm_weight = np.where(valid_mask, dist / safe_sum_weights, 0.0)
        norm_weight_3d = norm_weight[:, :, np.newaxis]
        blended += img.astype(np.float32) * norm_weight_3d

    blended_u8 = np.clip(blended, 0, 255).astype(np.uint8)
    return blended_u8


def auto_crop_panorama_borders(
    stitched: np.ndarray,
    content_threshold: int = 5,
    min_content_fraction: float = 0.05
) -> np.ndarray:
    """
    Crops black exterior margins while maintaining the full panorama extent.
    """
    if stitched is None or stitched.size == 0:
        return stitched

    gray = cv2.cvtColor(stitched, cv2.COLOR_BGR2GRAY)
    mask = (gray > content_threshold).astype(np.uint8)

    h, w = gray.shape
    col_counts = np.sum(mask, axis=0)
    row_counts = np.sum(mask, axis=1)

    valid_cols = np.where(col_counts > min_content_fraction * h)[0]
    valid_rows = np.where(row_counts > min_content_fraction * w)[0]

    if len(valid_cols) == 0 or len(valid_rows) == 0:
        return stitched

    x1, x2 = valid_cols[0], valid_cols[-1]
    y1, y2 = valid_rows[0], valid_rows[-1]

    # Ensure crop rectangle is substantial
    if (x2 - x1) > 200 and (y2 - y1) > 100:
        return stitched[y1:y2 + 1, x1:x2 + 1]

    return stitched
