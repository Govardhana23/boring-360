import pytest
import cv2
import numpy as np
from pathlib import Path

from backend.app.services.image_validation import validate_uploaded_files
from backend.app.services.image_preprocessing import preprocess_images_for_stitching
from backend.app.services.quality_assessment import assess_image_sequence_quality
from backend.app.services.panorama_stitcher import stitch_panorama_pipeline

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample-data"


def test_validation_guided_workflow():
    sample_files = sorted(list(SAMPLE_DIR.glob("smartphone_shot_*.jpg")))
    assert len(sample_files) == 8, f"Expected 8 sample files, found {len(sample_files)}"

    val_res = validate_uploaded_files(sample_files)
    assert val_res.is_valid is True
    assert len(val_res.valid_files) == 8
    assert len(val_res.errors) == 0


def test_quality_assessment():
    sample_files = sorted(list(SAMPLE_DIR.glob("smartphone_shot_*.jpg")))
    images_bgr, _ = preprocess_images_for_stitching(sample_files)
    filenames = [p.name for p in sample_files]
    sizes = [p.stat().st_size for p in sample_files]

    assessments, pairwise_scores, warnings = assess_image_sequence_quality(images_bgr, filenames, sizes)
    assert len(assessments) == 8
    for ass in assessments:
        assert ass.laplacian_variance > 50.0  # sharp textures
        assert ass.width == 800
        assert ass.height == 600

    # Verify pairwise overlaps have good matches
    assert len(pairwise_scores) >= 7
    for pair in pairwise_scores[:7]:
        assert pair.good_matches > 15, f"Low matches between {pair.image_a} and {pair.image_b}: {pair.good_matches}"


def test_stitching_pipeline():
    sample_files = sorted(list(SAMPLE_DIR.glob("smartphone_shot_*.jpg")))
    images_bgr, _ = preprocess_images_for_stitching(sample_files)
    filenames = [p.name for p in sample_files]

    result = stitch_panorama_pipeline(images_bgr, filenames)
    assert result.success is True
    assert result.panorama_image is not None
    assert result.panorama_image.shape[1] > 800  # Wide panorama canvas
    assert result.usable_image_count == 8
    assert result.horizontal_fov > 100.0  # Wide horizontal field of view
    print(f"\nStitched output: {result.panorama_image.shape[1]}x{result.panorama_image.shape[0]}, FOV: {result.horizontal_fov} deg, method: {result.method_used}")
