import pytest
import numpy as np
import cv2

from backend.app.services.quality_assessment import (
    assess_single_image,
    compute_pairwise_overlap,
    calculate_blur_laplacian,
    calculate_brightness_metrics
)


def test_blur_detection():
    # 1. Sharp checkerboard / textured image
    sharp = np.zeros((400, 400, 3), dtype=np.uint8)
    for i in range(0, 400, 20):
        for j in range(0, 400, 20):
            if (i // 20 + j // 20) % 2 == 0:
                sharp[i:i+20, j:j+20] = 255

    # 2. Heavily blurred version
    blurry = cv2.GaussianBlur(sharp, (31, 31), 10)

    sharp_assessment = assess_single_image(sharp, "sharp.jpg", 10000)
    blurry_assessment = assess_single_image(blurry, "blurry.jpg", 10000)

    assert sharp_assessment.is_blurry is False
    assert blurry_assessment.is_blurry is True
    assert blurry_assessment.laplacian_variance < 100.0
    assert len(blurry_assessment.warnings) > 0
    assert any("sharpness" in w.lower() for w in blurry_assessment.warnings)


def test_exposure_detection():
    # 1. Underexposed image (near black)
    dark = np.ones((400, 400, 3), dtype=np.uint8) * 10
    dark_assessment = assess_single_image(dark, "dark.jpg", 10000)
    assert dark_assessment.is_underexposed is True
    assert any("underexposed" in w.lower() for w in dark_assessment.warnings)

    # 2. Overexposed image (near white)
    blown = np.ones((400, 400, 3), dtype=np.uint8) * 248
    blown_assessment = assess_single_image(blown, "blown.jpg", 10000)
    assert blown_assessment.is_overexposed is True
    assert any("highlight clipping" in w.lower() for w in blown_assessment.warnings)


def test_insufficient_overlap_detection():
    # Two completely disjoint / non-overlapping textured images
    img1 = np.zeros((300, 300, 3), dtype=np.uint8)
    img2 = np.zeros((300, 300, 3), dtype=np.uint8)
    # Different distinct patterns
    cv2.circle(img1, (150, 150), 80, (255, 255, 255), -1)
    cv2.rectangle(img2, (50, 50), (250, 250), (255, 255, 255), -1)

    score = compute_pairwise_overlap(img1, img2, "img1.jpg", "img2.jpg")
    # Low overlap should trigger warning
    assert score.sufficient_overlap is False
    assert score.warning is not None
