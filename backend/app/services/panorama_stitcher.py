import cv2
import numpy as np
import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

from backend.app.services.image_blending import auto_crop_panorama, linear_feather_blend
from backend.app.services.image_alignment import cylindrical_warp
from backend.app.services.feature_detection import detect_and_compute_features
from backend.app.services.image_matching import match_features_knn, estimate_homography_ransac
from backend.app.utils.logger import logger


OPENCV_STITCHER_STATUS_CODES = {
    cv2.Stitcher_OK: "Success",
    cv2.Stitcher_ERR_NEED_MORE_IMGS: "Need more images / insufficient feature matches between pairs",
    cv2.Stitcher_ERR_HOMOGRAPHY_EST_FAIL: "Homography estimation failed (RANSAC could not find consistent geometric alignment)",
    cv2.Stitcher_ERR_CAMERA_PARAMS_ADJUST_FAIL: "Camera parameters adjustment failed (bundle adjustment optimization did not converge)",
}


class StitchingResult:
    def __init__(
        self,
        success: bool,
        panorama_image: Optional[np.ndarray],
        status_code: int,
        status_message: str,
        method_used: str,
        usable_image_count: int,
        total_image_count: int,
        elapsed_seconds: float,
        is_full_360: bool,
        horizontal_fov: float,
        vertical_fov: float,
        warnings: List[str],
        logs: List[str],
    ):
        self.success = success
        self.panorama_image = panorama_image
        self.status_code = status_code
        self.status_message = status_message
        self.method_used = method_used
        self.usable_image_count = usable_image_count
        self.total_image_count = total_image_count
        self.elapsed_seconds = elapsed_seconds
        self.is_full_360 = is_full_360
        self.horizontal_fov = horizontal_fov
        self.vertical_fov = vertical_fov
        self.warnings = warnings
        self.logs = logs


def estimate_panorama_geometry(
    pano_img: np.ndarray, num_images: int, has_loop_closure: bool = False
) -> Tuple[bool, float, float]:
    h, w = pano_img.shape[:2]
    aspect_ratio = w / float(h)

    approx_single_hfov = 65.0
    approx_single_vfov = 50.0

    estimated_hfov = min(360.0, approx_single_hfov + (num_images - 1) * 35.0)
    estimated_vfov = min(180.0, approx_single_vfov)

    is_full_360 = False

    if has_loop_closure and aspect_ratio >= 3.5 and num_images >= 8:
        is_full_360 = False
        estimated_hfov = 360.0
    elif aspect_ratio >= 3.0:
        estimated_hfov = min(360.0, aspect_ratio * 60.0)

    estimated_hfov = round(float(estimated_hfov), 1)
    estimated_vfov = round(float(estimated_vfov), 1)

    return is_full_360, estimated_hfov, estimated_vfov


def custom_sequential_stitcher(images_bgr: List[np.ndarray], logs: List[str]) -> Tuple[bool, Optional[np.ndarray], str]:
    """
    Fallback modular cylindrical pipeline with non-destructive composition.
    """
    logs.append("[Custom Pipeline] Initiating modular cylindrical stitcher fallback...")
    n = len(images_bgr)
    if n < 2:
        return False, None, "Custom stitcher requires at least 2 images."

    cylindrical_images = []
    for img in images_bgr:
        warped, _ = cylindrical_warp(img)
        cylindrical_images.append(warped)

    accumulated = cylindrical_images[0]

    for i in range(1, n):
        curr_img = cylindrical_images[i]
        kp_acc, des_acc = detect_and_compute_features(accumulated, method="SIFT", max_features=2500)
        kp_curr, des_curr = detect_and_compute_features(curr_img, method="SIFT", max_features=2500)

        matches = match_features_knn(des_curr, des_acc, method="SIFT", ratio_threshold=0.75)
        if len(matches) < 8:
            logs.append(f"[Custom Pipeline] Image {i+1} has weak overlap with canvas ({len(matches)} matches). Skipping.")
            continue

        H, mask, inliers = estimate_homography_ransac(kp_curr, kp_acc, matches, ransac_reproj_thresh=4.0)
        if H is None or inliers < 8:
            logs.append(f"[Custom Pipeline] Homography rejected for image {i+1} (inliers: {inliers}).")
            continue

        h1, w1 = accumulated.shape[:2]
        h2, w2 = curr_img.shape[:2]

        corners_curr = np.float32([[0, 0], [w2, 0], [w2, h2], [0, h2]]).reshape(-1, 1, 2)
        corners_trans = cv2.perspectiveTransform(corners_curr, H)

        all_corners = np.concatenate((
            np.float32([[0, 0], [w1, 0], [w1, h1], [0, h1]]).reshape(-1, 1, 2),
            corners_trans
        ), axis=0)

        [x_min, y_min] = np.int32(all_corners.min(axis=0).ravel() - 0.5)
        [x_max, y_max] = np.int32(all_corners.max(axis=0).ravel() + 0.5)

        translation_dist = [-x_min, -y_min]
        H_trans = np.array([[1, 0, translation_dist[0]], [0, 1, translation_dist[1]], [0, 0, 1]], dtype=np.float32)

        out_w = max(10, min(14000, x_max - x_min))
        out_h = max(10, min(7000, y_max - y_min))

        warped_curr = cv2.warpPerspective(curr_img, H_trans.dot(H), (out_w, out_h))
        warped_acc = cv2.warpPerspective(accumulated, H_trans, (out_w, out_h))

        accumulated = linear_feather_blend(warped_acc, warped_curr)
        logs.append(f"[Custom Pipeline] Registered image {i+1}/{n} (composite: {out_w}x{out_h}).")

    cropped = auto_crop_panorama(accumulated)
    return True, cropped, "Custom stitching pipeline succeeded."


def stitch_panorama_pipeline(
    images_bgr: List[np.ndarray], filenames: List[str], has_loop_closure: bool = False
) -> StitchingResult:
    """
    Main stitching pipeline combining OpenCV Stitcher with adaptive thresholds
    and modular cylindrical fallback.
    """
    start_time = time.time()
    logs = []
    warnings = []
    num_imgs = len(images_bgr)

    logs.append(f"[Stitcher] Processing sequence of {num_imgs} images.")

    stitched_pano = None
    status = -1
    status_msg = ""
    method_used = ""

    # Strategy 1: OpenCV Stitcher_PANORAMA with smartphone-calibrated confidence thresholds
    # Smartphones typically have handheld jitter where 0.20-0.35 produces optimal bundle adjustment.
    confidence_levels = [0.25, 0.30, 0.20, 0.35, 0.40]
    for conf in confidence_levels:
        logs.append(f"[Stitcher] Initializing OpenCV Stitcher_PANORAMA (confidence threshold: {conf})...")
        try:
            stitcher = cv2.Stitcher_create(cv2.Stitcher_PANORAMA)
            stitcher.setPanoConfidenceThresh(conf)
            curr_status, curr_pano = stitcher.stitch(images_bgr)
            if curr_status == cv2.Stitcher_OK and curr_pano is not None:
                h, w = curr_pano.shape[:2]
                if w >= h * 1.15:
                    stitched_pano = curr_pano
                    status = curr_status
                    status_msg = f"Success (OpenCV PANORAMA, conf={conf})"
                    method_used = f"OpenCV Stitcher (PANORAMA, conf={conf})"
                    logs.append(f"[Stitcher] Stitcher_PANORAMA succeeded: {w}x{h} px.")
                    break
                else:
                    logs.append(f"[Stitcher] Stitcher_PANORAMA produced portrait aspect ratio ({w}x{h}), continuing...")
            else:
                code_name = OPENCV_STITCHER_STATUS_CODES.get(curr_status, f"code {curr_status}")
                logs.append(f"[Stitcher] PANORAMA conf {conf} returned: {code_name}")
        except Exception as e:
            logs.append(f"[Stitcher] Stitcher_PANORAMA exception at conf {conf}: {str(e)}")

    # Strategy 2: If PANORAMA mode failed, try Stitcher_SCANS (affine mode)
    if stitched_pano is None:
        for conf in [0.25, 0.30, 0.20, 0.35]:
            logs.append(f"[Stitcher] Attempting OpenCV Stitcher_SCANS (confidence threshold: {conf})...")
            try:
                stitcher_scans = cv2.Stitcher_create(cv2.Stitcher_SCANS)
                stitcher_scans.setPanoConfidenceThresh(conf)
                curr_status, curr_pano = stitcher_scans.stitch(images_bgr)
                if curr_status == cv2.Stitcher_OK and curr_pano is not None:
                    h, w = curr_pano.shape[:2]
                    if w >= h * 1.15:
                        stitched_pano = curr_pano
                        status = curr_status
                        status_msg = f"Success (OpenCV SCANS, conf={conf})"
                        method_used = f"OpenCV Stitcher (SCANS, conf={conf})"
                        logs.append(f"[Stitcher] Stitcher_SCANS succeeded: {w}x{h} px.")
                        break
            except Exception as e:
                logs.append(f"[Stitcher] Stitcher_SCANS exception: {str(e)}")

    # Strategy 3: Custom Modular Cylindrical Fallback (only if OpenCV built-in failed completely)
    if stitched_pano is None:
        logs.append("[Stitcher] OpenCV built-in stitchers returned error. Running custom cylindrical fallback...")
        custom_ok, custom_pano, custom_msg = custom_sequential_stitcher(images_bgr, logs)
        if custom_ok and custom_pano is not None and custom_pano.shape[1] > custom_pano.shape[0] * 1.15:
            stitched_pano = custom_pano
            status = cv2.Stitcher_OK
            status_msg = "Success (Custom Cylindrical Fallback)"
            method_used = "Custom Cylindrical SIFT/RANSAC Pipeline"
        else:
            elapsed = time.time() - start_time
            logs.append("[Stitcher] All stitching strategies failed. Insufficient visual overlap or geometric alignment.")
            return StitchingResult(
                success=False,
                panorama_image=None,
                status_code=cv2.Stitcher_ERR_HOMOGRAPHY_EST_FAIL,
                status_message="Stitching failed: OpenCV could not find sufficient matching features or camera alignment between the input photographs.",
                method_used="None",
                usable_image_count=0,
                total_image_count=num_imgs,
                elapsed_seconds=round(elapsed, 2),
                is_full_360=False,
                horizontal_fov=0.0,
                vertical_fov=0.0,
                warnings=["Images appear to have insufficient overlap (< 20%), sudden perspective shift, or lack distinct visual texture."],
                logs=logs,
            )

    # Auto-crop black outer border margins
    logs.append("[Stitcher] Auto-cropping outer black margins while preserving full panorama span...")
    final_pano = auto_crop_panorama(stitched_pano)
    if final_pano is None or final_pano.size == 0:
        final_pano = stitched_pano

    # Estimate field of view
    is_full_360, hfov, vfov = estimate_panorama_geometry(final_pano, num_imgs, has_loop_closure)
    if not is_full_360:
        warnings.append(
            f"Result represents a partial cylindrical panorama (estimated {hfov}° horizontal × {vfov}° vertical FOV), "
            "not a full 360° × 180° spherical panorama. Viewer has been automatically configured with partial angles."
        )

    elapsed = time.time() - start_time
    logs.append(f"[Stitcher] Pipeline completed in {elapsed:.2f}s. Output dimensions: {final_pano.shape[1]}x{final_pano.shape[0]}.")

    return StitchingResult(
        success=True,
        panorama_image=final_pano,
        status_code=cv2.Stitcher_OK,
        status_message=status_msg,
        method_used=method_used,
        usable_image_count=num_imgs,
        total_image_count=num_imgs,
        elapsed_seconds=round(elapsed, 2),
        is_full_360=is_full_360,
        horizontal_fov=hfov,
        vertical_fov=vfov,
        warnings=warnings,
        logs=logs,
    )
