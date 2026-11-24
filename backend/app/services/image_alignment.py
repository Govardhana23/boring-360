import cv2
import numpy as np
from typing import Tuple, List, Optional


def cylindrical_warp(img: np.ndarray, focal_length: Optional[float] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Warps a planar image onto a cylinder.
    If focal_length is None, estimates f from image width (approx 50-70 degree FOV typical for smartphone).
    Returns (warped_image, mask).
    """
    h, w = img.shape[:2]
    if focal_length is None:
        # Typical smartphone wide camera FOV ~ 65-75 degrees -> f ~ w / (2 * tan(fov/2))
        focal_length = w * 0.9

    f = float(focal_length)
    cx = w / 2.0
    cy = h / 2.0

    # Create coordinate grid
    y_coords, x_coords = np.indices((h, w), dtype=np.float32)

    # Inverse mapping coordinates
    theta = (x_coords - cx) / f
    h_cyl = (y_coords - cy) / f

    x_plane = np.sin(theta)
    y_plane = h_cyl
    z_plane = np.cos(theta)

    x_orig = f * (x_plane / z_plane) + cx
    y_orig = f * (y_plane / z_plane) + cy

    warped = cv2.remap(
        img,
        x_orig.astype(np.float32),
        y_orig.astype(np.float32),
        cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0)
    )

    mask = 255 * np.ones((h, w), dtype=np.uint8)
    warped_mask = cv2.remap(
        mask,
        x_orig.astype(np.float32),
        y_orig.astype(np.float32),
        cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0
    )

    return warped, warped_mask


def warp_perspective_with_bounds(
    img: np.ndarray, H: np.ndarray, output_shape: Tuple[int, int]
) -> np.ndarray:
    """
    Applies homography transformation H to img.
    """
    h_out, w_out = output_shape
    return cv2.warpPerspective(img, H, (w_out, h_out), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
