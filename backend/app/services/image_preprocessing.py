import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image, ImageOps


def read_image_with_exif_orientation(image_path: Path) -> np.ndarray:
    """
    Reads an image using PIL to automatically correct EXIF orientation
    (critical for smartphone captures taken at various rotations),
    then converts to BGR numpy array for OpenCV.
    """
    with Image.open(image_path) as pil_img:
        # Transpose according to EXIF orientation tag
        corrected_pil = ImageOps.exif_transpose(pil_img)
        # Ensure RGB mode
        if corrected_pil.mode != "RGB":
            corrected_pil = corrected_pil.convert("RGB")
        rgb_arr = np.array(corrected_pil)
        # Convert RGB to BGR for OpenCV
        bgr_arr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)
        return bgr_arr


def resize_image_if_needed(img: np.ndarray, max_dim: int = 2048) -> Tuple[np.ndarray, float]:
    """
    Resizes image proportionally if its maximum dimension exceeds max_dim.
    Returns the resized image and the scale factor used.
    """
    h, w = img.shape[:2]
    max_side = max(h, w)
    if max_side <= max_dim:
        return img, 1.0

    scale = max_dim / float(max_side)
    new_w = int(round(w * scale))
    new_h = int(round(h * scale))
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized, scale


def preprocess_images_for_stitching(
    file_paths: List[Path], max_dimension: int = 1920
) -> Tuple[List[np.ndarray], List[dict]]:
    """
    Loads, corrects orientation, and scales all input images.
    Returns list of BGR numpy arrays and metadata for each.
    """
    processed_images = []
    metadata_list = []

    for path in file_paths:
        raw_bgr = read_image_with_exif_orientation(path)
        orig_h, orig_w = raw_bgr.shape[:2]
        scaled_bgr, scale = resize_image_if_needed(raw_bgr, max_dim=max_dimension)
        cur_h, cur_w = scaled_bgr.shape[:2]

        processed_images.append(scaled_bgr)
        metadata_list.append({
            "filename": path.name,
            "original_width": orig_w,
            "original_height": orig_h,
            "processed_width": cur_w,
            "processed_height": cur_h,
            "scale_factor": scale,
            "file_size": path.stat().st_size
        })

    return processed_images, metadata_list
