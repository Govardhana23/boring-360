"""
Integration Tests for Computer Vision Stitching Pipeline:
- Full end-to-end ORB stitching with 8 real overlapping smartphone photographs.
- Disconnected sequence rejection.
- Insufficient image count handling.
- Measurement of keypoints, matches, inliers, processing time, and canvas dimensions.
"""

import pytest
import numpy as np
import cv2
from pathlib import Path

from backend.app.services.stitching import run_orb_stitching_pipeline, FullStitchingResult

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample-data"


def test_end_to_end_orb_stitching_real_photos():
    """
    Runs the genuine ORB -> BFMatcher -> RANSAC Homography -> Perspective Warping -> Blending
    pipeline on the 8 smartphone photographs.
    """
    sample_files = sorted(list(SAMPLE_DIR.glob("smartphone_shot_*.jpg")))
    assert len(sample_files) == 8, f"Expected 8 sample files, found {len(sample_files)}"

    result: FullStitchingResult = run_orb_stitching_pipeline(sample_files)

    # 1. Pipeline success
    assert result.success is True, f"Stitching failed with error: {result.error_details}"
    assert result.panorama_image is not None
    assert result.status_message == "Panorama generated successfully"

    # 2. Dimensions and wide aspect ratio
    out_w, out_h = result.output_dimensions
    assert out_w > 1200, f"Expected wide panorama width > 1200, got {out_w}"
    assert out_w > out_h * 1.5, f"Expected panoramic aspect ratio, got {out_w}x{out_h}"

    # 3. Features and matching
    assert result.images_processed == 8
    assert len(result.keypoints_detected) == 8
    for count in result.keypoints_detected:
        assert count > 300, f"Low keypoint count: {count}"

    # 4. Pairwise matches and RANSAC inliers
    assert len(result.pairwise_matches) == 7
    for match_info in result.pairwise_matches:
        assert match_info["is_valid"] is True
        assert match_info["inlier_count"] >= 12, f"Low inlier count: {match_info}"

    # 5. Timing and algorithms
    assert result.processing_time > 0.0
    assert result.feature_algorithm == "ORB"
    assert result.matching_algorithm == "BFMatcher-Hamming"
    assert result.alignment_algorithm == "RANSAC-Homography"
    assert result.horizontal_fov > 90.0

    print(
        f"\n[ORB Stitching Success] Resolution: {out_w}x{out_h}px, "
        f"Processing time: {result.processing_time}s, "
        f"FOV: {result.horizontal_fov}°, Inliers: {[m['inlier_count'] for m in result.pairwise_matches]}"
    )


def test_stitching_handles_insufficient_images():
    """Verify rejection when fewer than minimum images provided."""
    sample_files = sorted(list(SAMPLE_DIR.glob("smartphone_shot_*.jpg")))
    # Pass only 1 image
    result = run_orb_stitching_pipeline(sample_files[:1])
    assert result.success is False
    assert "At least 2 images" in result.status_message


def test_stitching_detects_disconnected_sequence():
    """Verify rejection when images have no visual overlap (disconnected sequence)."""
    sample_files = sorted(list(SAMPLE_DIR.glob("smartphone_shot_*.jpg")))
    # Pair shot 1 and shot 8 which have no overlap
    disconnected = [sample_files[0], sample_files[7]]
    result = run_orb_stitching_pipeline(disconnected)
    assert result.success is False
    assert ("Disconnected" in result.status_message or "Insufficient" in result.status_message or "Alignment failed" in result.status_message)
