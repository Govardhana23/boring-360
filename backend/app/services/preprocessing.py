"""
Stage 1: Image Preprocessing Service

Responsibilities:
- Validate file formats and dimensions.
- Correct camera orientation using EXIF tags (crucial for smartphone portrait/landscape captures).
- Proportionally downscale oversized images to balance resolution and computational efficiency.
- Convert images into format suitable for feature extraction (BGR and Grayscale).
- Reject corrupted or unsupported image files.
"""

from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import cv2
import numpy as np
from PIL import Image, ImageOps

from backend.app.core.config import settings


class PreprocessingResult:
    def __init__(
        self,
        images_bgr: List[np.ndarray],
        images_gray: List[np.ndarray],
        filenames: List[str],
        metadata: List[Dict[str, Any]],
        errors: List[str],
        warnings: List[str],
    ):
        self.images_bgr = images_bgr
        self.images_gray = images_gray
        self.filenames = filenames
        self.metadata = metadata
        self.errors = errors
        self.warnings = warnings
        self.is_valid = len(errors) == 0 and len(images_bgr) >= settings.MIN_IMAGES_ABSOLUTE


def load_image_with_exif_correction(file_path: Path) -> np.ndarray:
    """
    Loads an image file, honors EXIF orientation metadata (preventing inverted/sideways
    smartphone photos), and returns a standard OpenCV BGR numpy array.
    """
    with Image.open(file_path) as pil_img:
        # Transpose image based on EXIF orientation tag
        corrected_pil = ImageOps.exif_transpose(pil_img)
        if corrected_pil.mode != "RGB":
            corrected_pil = corrected_pil.convert("RGB")
        rgb_array = np.array(corrected_pil)
        # Convert RGB to OpenCV BGR
        return cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)


def resize_image_aspect_ratio(
    img: np.ndarray, max_dimension: int = settings.MAX_IMAGE_DIMENSION
) -> Tuple[np.ndarray, float]:
    """
    Resizes an image proportionally so its largest dimension does not exceed max_dimension.
    Preserves exact aspect ratio.
    """
    h, w = img.shape[:2]
    max_side = max(h, w)
    if max_side <= max_dimension:
        return img, 1.0

    scale = max_dimension / float(max_side)
    new_w = int(round(w * scale))
    new_h = int(round(h * scale))
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized, scale


def preprocess_image_sequence(
    file_paths: List[Path],
    strict_count: bool = False,
    max_dimension: int = settings.MAX_IMAGE_DIMENSION
) -> PreprocessingResult:
    """
    Executes Stage 1 preprocessing on a sequence of uploaded image files.
    """
    images_bgr: List[np.ndarray] = []
    images_gray: List[np.ndarray] = []
    filenames: List[str] = []
    metadata: List[Dict[str, Any]] = []
    errors: List[str] = []
    warnings: List[str] = []

    # Sequence length verification
    num_files = len(file_paths)
    if num_files < settings.MIN_IMAGES_ABSOLUTE:
        errors.append(f"At least {settings.MIN_IMAGES_ABSOLUTE} images required for stitching. Provided: {num_files}.")
        return PreprocessingResult([], [], [], [], errors, warnings)

    if strict_count:
        if num_files < settings.MIN_IMAGES:
            errors.append(
                f"Smartphone panorama workflow requires at least {settings.MIN_IMAGES} overlapping photographs "
                f"(received {num_files})."
            )
            return PreprocessingResult([], [], [], [], errors, warnings)
        if num_files > settings.MAX_IMAGES:
            errors.append(
                f"Maximum allowed photographs is {settings.MAX_IMAGES} (received {num_files})."
            )
            return PreprocessingResult([], [], [], [], errors, warnings)
    else:
        if num_files < settings.MIN_IMAGES:
            warnings.append(
                f"Recommended smartphone capture is {settings.MIN_IMAGES}–{settings.MAX_IMAGES} photos for complete horizontal coverage. "
                f"Provided {num_files} photos; partial panorama will be generated."
            )
        elif num_files > settings.MAX_IMAGES:
            warnings.append(
                f"Provided {num_files} photos (> {settings.MAX_IMAGES}). Processing time will be extended."
            )

    for path in file_paths:
        fname = path.name
        ext = path.suffix.lower()

        # Format validation
        if ext not in settings.ALLOWED_EXTENSIONS:
            errors.append(f"Unsupported format '{ext}' in file '{fname}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}.")
            continue

        # File size verification
        try:
            fsize = path.stat().st_size
            if fsize == 0:
                errors.append(f"File '{fname}' is empty (0 bytes).")
                continue
            if fsize > settings.MAX_FILE_SIZE_BYTES:
                errors.append(f"File '{fname}' exceeds {settings.MAX_FILE_SIZE_BYTES // (1024*1024)}MB limit.")
                continue
        except Exception as e:
            errors.append(f"Cannot access file '{fname}': {str(e)}")
            continue

        # Integrity & EXIF load
        try:
            with Image.open(path) as test_img:
                test_img.verify()

            # Load corrected BGR
            bgr = load_image_with_exif_correction(path)
            orig_h, orig_w = bgr.shape[:2]

            if orig_w < settings.MIN_IMAGE_DIMENSION or orig_h < settings.MIN_IMAGE_DIMENSION:
                warnings.append(f"Image '{fname}' resolution ({orig_w}x{orig_h}) is very low for reliable feature matching.")

            # Resize if oversized
            scaled_bgr, scale = resize_image_aspect_ratio(bgr, max_dimension=max_dimension)
            cur_h, cur_w = scaled_bgr.shape[:2]

            # Grayscale conversion for feature extraction
            gray = cv2.cvtColor(scaled_bgr, cv2.COLOR_BGR2GRAY)

            images_bgr.append(scaled_bgr)
            images_gray.append(gray)
            filenames.append(fname)
            metadata.append({
                "filename": fname,
                "original_width": orig_w,
                "original_height": orig_h,
                "processed_width": cur_w,
                "processed_height": cur_h,
                "scale_factor": scale,
                "file_size": fsize
            })

        except Exception as e:
            errors.append(f"Failed to process image '{fname}': corrupted or unreadable ({str(e)}).")

    return PreprocessingResult(
        images_bgr=images_bgr,
        images_gray=images_gray,
        filenames=filenames,
        metadata=metadata,
        errors=errors,
        warnings=warnings
    )
