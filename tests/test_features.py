"""
Unit Tests for Computer Vision Feature Pipeline:
- Stage 1: Preprocessing (EXIF rotation, aspect resize)
- Stage 2: ORB Feature Detection (Oriented FAST & Rotated BRIEF)
- Stage 3: BFMatcher with Hamming Distance and Lowe's Ratio Test
- Stage 4: RANSAC Homography Estimation and Stability Verification
"""

import pytest
import numpy as np
import cv2
from pathlib import Path
from PIL import Image

from backend.app.services.preprocessing import (
    load_image_with_exif_correction,
    resize_image_aspect_ratio,
    preprocess_image_sequence
)
from backend.app.services.feature_detection import (
    create_orb_detector,
    extract_orb_features,
    ImageFeatures
)
from backend.app.services.feature_matching import (
    match_orb_descriptors,
    MatchResult
)
from backend.app.services.homography import (
    estimate_homography_ransac,
    is_homography_stable
)

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample-data"


def test_orb_detector_creation_and_config():
    """Verify ORB detector initializes with configured parameters."""
    detector = create_orb_detector(n_features=3000)
    assert detector is not None
    assert detector.getMaxFeatures() == 3000


def test_orb_feature_extraction_on_sample_image():
    """Verify ORB extracts distinctive keypoints and binary descriptors."""
    sample_files = sorted(list(SAMPLE_DIR.glob("smartphone_shot_*.jpg")))
    assert len(sample_files) > 0, "Sample dataset missing"

    bgr = cv2.imread(str(sample_files[0]))
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    feats: ImageFeatures = extract_orb_features(gray, image_index=0, filename=sample_files[0].name, n_features=2500)

    assert feats.keypoint_count > 200, f"Expected >200 keypoints, got {feats.keypoint_count}"
    assert feats.has_descriptors is True
    assert feats.descriptors is not None
    # ORB descriptors must be 256 bits = 32 bytes of uint8
    assert feats.descriptors.shape[1] == 32
    assert feats.descriptors.dtype == np.uint8


def test_orb_handles_blank_or_textureless_image():
    """Verify ORB handles blank low-contrast images without crashing."""
    blank = np.zeros((400, 400), dtype=np.uint8)
    feats = extract_orb_features(blank, image_index=0, filename="blank.jpg")
    assert feats.keypoint_count == 0 or feats.descriptors is None or len(feats.descriptors) == 0


def test_bfmatcher_hamming_and_ratio_test():
    """Verify BFMatcher with Hamming distance finds correct correspondences."""
    sample_files = sorted(list(SAMPLE_DIR.glob("smartphone_shot_*.jpg")))
    img1_gray = cv2.imread(str(sample_files[0]), cv2.IMREAD_GRAYSCALE)
    img2_gray = cv2.imread(str(sample_files[1]), cv2.IMREAD_GRAYSCALE)

    f1 = extract_orb_features(img1_gray, 0, sample_files[0].name)
    f2 = extract_orb_features(img2_gray, 1, sample_files[1].name)

    match_res: MatchResult = match_orb_descriptors(f1, f2, ratio_threshold=0.80)

    assert match_res.is_sufficient is True
    assert match_res.match_count > 30, f"Expected >30 matches, found {match_res.match_count}"
    assert match_res.error_message is None


def test_ransac_homography_estimation():
    """Verify RANSAC estimates accurate transformation between overlapping frames."""
    sample_files = sorted(list(SAMPLE_DIR.glob("smartphone_shot_*.jpg")))
    img1_gray = cv2.imread(str(sample_files[0]), cv2.IMREAD_GRAYSCALE)
    img2_gray = cv2.imread(str(sample_files[1]), cv2.IMREAD_GRAYSCALE)

    f1 = extract_orb_features(img1_gray, 0, sample_files[0].name)
    f2 = extract_orb_features(img2_gray, 1, sample_files[1].name)

    match_res = match_orb_descriptors(f1, f2)
    homo_res = estimate_homography_ransac(f1, f2, match_res)

    assert homo_res.is_valid is True
    assert homo_res.H is not None
    assert homo_res.H.shape == (3, 3)
    assert homo_res.inlier_count >= 15
    assert homo_res.inlier_ratio >= 0.20


def test_homography_stability_rejection():
    """Verify degenerate or singular homographies are rejected."""
    # Singular matrix
    singular_H = np.zeros((3, 3))
    stable, reason = is_homography_stable(singular_H, (600, 800))
    assert stable is False

    # Identity matrix (stable)
    identity_H = np.eye(3)
    stable, reason = is_homography_stable(identity_H, (600, 800))
    assert stable is True


def test_aspect_ratio_resizing():
    """Verify proportional resizing preserves exact aspect ratio."""
    test_img = np.zeros((1200, 2400, 3), dtype=np.uint8)
    resized, scale = resize_image_aspect_ratio(test_img, max_dimension=1200)

    h, w = resized.shape[:2]
    assert w == 1200
    assert h == 600
    assert abs((w / h) - (2400 / 1200)) < 1e-4
