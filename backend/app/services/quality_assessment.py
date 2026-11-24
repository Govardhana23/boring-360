import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from backend.app.models.job import ImageQualityAssessment, PairwiseOverlapScore

BLUR_THRESHOLD_LAPLACIAN = 100.0
UNDEREXPOSURE_PIXEL_THRESH = 15
OVEREXPOSURE_PIXEL_THRESH = 240
UNDEREXPOSURE_PCT_WARN = 18.0
OVEREXPOSURE_PCT_WARN = 18.0
MIN_OVERLAP_MATCHES_WARN = 25


def calculate_blur_laplacian(gray: np.ndarray) -> float:
    """Computes Laplacian variance. Lower values (< 100) indicate significant blur."""
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = float(laplacian.var())
    return variance


def calculate_brightness_metrics(gray: np.ndarray) -> Tuple[float, float, float]:
    """
    Returns:
    (mean_brightness, underexposed_percent, overexposed_percent)
    """
    mean_val = float(np.mean(gray))
    total_pixels = gray.size
    under_count = np.count_nonzero(gray <= UNDEREXPOSURE_PIXEL_THRESH)
    over_count = np.count_nonzero(gray >= OVEREXPOSURE_PIXEL_THRESH)

    under_pct = float((under_count / total_pixels) * 100.0)
    over_pct = float((over_count / total_pixels) * 100.0)
    return mean_val, under_pct, over_pct


def assess_single_image(img_bgr: np.ndarray, filename: str, file_size: int) -> ImageQualityAssessment:
    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    lap_var = calculate_blur_laplacian(gray)
    is_blurry = lap_var < BLUR_THRESHOLD_LAPLACIAN

    mean_bright, under_pct, over_pct = calculate_brightness_metrics(gray)
    is_underexposed = under_pct > UNDEREXPOSURE_PCT_WARN or mean_bright < 40.0
    is_overexposed = over_pct > OVEREXPOSURE_PCT_WARN or mean_bright > 215.0

    warnings = []
    recommendations = []

    if is_blurry:
        warnings.append(f"Image '{filename}' has low sharpness (Laplacian variance: {lap_var:.1f}).")
        recommendations.append(f"Hold the smartphone steady or retake '{filename}' in better lighting to eliminate motion blur.")

    if is_underexposed:
        warnings.append(f"Image '{filename}' is underexposed ({under_pct:.1f}% shadow clipping, mean brightness {mean_bright:.1f}/255).")
        recommendations.append(f"Increase ambient illumination or tap the smartphone screen to meter for shadows on '{filename}'.")
    elif is_overexposed:
        warnings.append(f"Image '{filename}' has highlight clipping ({over_pct:.1f}% saturated pixels, mean brightness {mean_bright:.1f}/255).")
        recommendations.append(f"Lower camera exposure on '{filename}' to prevent washed-out skies/windows.")

    return ImageQualityAssessment(
        filename=filename,
        width=w,
        height=h,
        file_size_bytes=file_size,
        laplacian_variance=round(lap_var, 2),
        is_blurry=is_blurry,
        mean_brightness=round(mean_bright, 2),
        is_underexposed=is_underexposed,
        is_overexposed=is_overexposed,
        underexposed_percent=round(under_pct, 2),
        overexposed_percent=round(over_pct, 2),
        warnings=warnings,
        recommendations=recommendations,
    )


def compute_pairwise_overlap(
    img_a_bgr: np.ndarray, img_b_bgr: np.ndarray, name_a: str, name_b: str
) -> PairwiseOverlapScore:
    """
    Estimates overlap between adjacent images using ORB / SIFT features and FLANN / BFMatcher.
    """
    gray_a = cv2.cvtColor(img_a_bgr, cv2.COLOR_BGR2GRAY)
    gray_b = cv2.cvtColor(img_b_bgr, cv2.COLOR_BGR2GRAY)

    # Use SIFT if available, otherwise ORB
    try:
        detector = cv2.SIFT_create(nfeatures=1500)
        norm_type = cv2.NORM_L2
    except Exception:
        detector = cv2.ORB_create(nfeatures=1500)
        norm_type = cv2.NORM_HAMMING

    kp_a, des_a = detector.detectAndCompute(gray_a, None)
    kp_b, des_b = detector.detectAndCompute(gray_b, None)

    num_kp_a = len(kp_a) if kp_a is not None else 0
    num_kp_b = len(kp_b) if kp_b is not None else 0

    if des_a is None or des_b is None or num_kp_a < 10 or num_kp_b < 10:
        return PairwiseOverlapScore(
            image_a=name_a,
            image_b=name_b,
            keypoints_a=num_kp_a,
            keypoints_b=num_kp_b,
            good_matches=0,
            estimated_overlap_percent=0.0,
            sufficient_overlap=False,
            warning=f"Insufficient distinct features detected between '{name_a}' and '{name_b}'."
        )

    matcher = cv2.BFMatcher(norm_type)
    matches = matcher.knnMatch(des_a, des_b, k=2)

    # Lowe's ratio test
    good = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good.append(m)

    good_count = len(good)
    min_kp = min(num_kp_a, num_kp_b)
    overlap_ratio = (good_count / float(min_kp)) if min_kp > 0 else 0.0
    estimated_overlap_pct = min(100.0, overlap_ratio * 150.0)  # normalized heuristic

    sufficient = good_count >= MIN_OVERLAP_MATCHES_WARN
    warning = None
    if not sufficient:
        warning = (
            f"Only {good_count} verified feature matches between '{name_a}' and '{name_b}'. "
            f"Overlap appears below recommended 25-40% range."
        )

    return PairwiseOverlapScore(
        image_a=name_a,
        image_b=name_b,
        keypoints_a=num_kp_a,
        keypoints_b=num_kp_b,
        good_matches=good_count,
        estimated_overlap_percent=round(estimated_overlap_pct, 1),
        sufficient_overlap=sufficient,
        warning=warning,
    )


def assess_image_sequence_quality(
    images_bgr: List[np.ndarray], filenames: List[str], file_sizes: List[int]
) -> Tuple[List[ImageQualityAssessment], List[PairwiseOverlapScore], List[str]]:
    """
    Runs comprehensive quality assessment on the entire input sequence.
    """
    assessments = []
    global_warnings = []

    # Check orientation consistency
    aspect_ratios = [img.shape[1] / float(img.shape[0]) for img in images_bgr]
    is_all_landscape = all(ar > 1.1 for ar in aspect_ratios)
    is_all_portrait = all(ar < 0.9 for ar in aspect_ratios)
    if not (is_all_landscape or is_all_portrait):
        global_warnings.append(
            "Mixed image orientations detected (some portrait, some landscape). "
            "For optimal panorama stitching, capture all photographs in consistent orientation (preferably landscape)."
        )

    for img, fname, size in zip(images_bgr, filenames, file_sizes):
        ass = assess_single_image(img, fname, size)
        assessments.append(ass)

    # Pairwise overlap checks between consecutive images
    pairwise_scores = []
    for i in range(len(images_bgr) - 1):
        score = compute_pairwise_overlap(
            images_bgr[i], images_bgr[i + 1], filenames[i], filenames[i + 1]
        )
        pairwise_scores.append(score)
        if score.warning:
            global_warnings.append(score.warning)

    # Also check loop-closure overlap between last and first image (to see if full 360 circle was captured)
    if len(images_bgr) >= 4:
        closure_score = compute_pairwise_overlap(
            images_bgr[-1], images_bgr[0], filenames[-1], filenames[0]
        )
        if closure_score.good_matches >= 30:
            closure_score.warning = "Potential full-circle loop closure detected between start and end captures."
        pairwise_scores.append(closure_score)

    return assessments, pairwise_scores, global_warnings
