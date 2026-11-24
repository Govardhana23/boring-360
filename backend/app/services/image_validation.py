import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from PIL import Image

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
MIN_IMAGES_GUIDED = 8
MAX_IMAGES_GUIDED = 12
MIN_IMAGES_ABSOLUTE = 2
MIN_IMAGE_DIMENSION = 400


class ImageValidationResult:
    def __init__(self, is_valid: bool, errors: List[str], warnings: List[str], valid_files: List[Path]):
        self.is_valid = is_valid
        self.errors = errors
        self.warnings = warnings
        self.valid_files = valid_files


def validate_uploaded_files(file_paths: List[Path]) -> ImageValidationResult:
    errors = []
    warnings = []
    valid_files = []

    if len(file_paths) < MIN_IMAGES_ABSOLUTE:
        errors.append(f"At least {MIN_IMAGES_ABSOLUTE} images are required for panorama stitching. Found {len(file_paths)}.")
        return ImageValidationResult(False, errors, warnings, valid_files)

    if len(file_paths) < MIN_IMAGES_GUIDED:
        warnings.append(
            f"Boring 360 recommended guided workflow uses {MIN_IMAGES_GUIDED}–{MAX_IMAGES_GUIDED} photographs for adequate 360-degree overlap. "
            f"Only {len(file_paths)} images provided; panorama may be partial or have missing coverage."
        )
    elif len(file_paths) > MAX_IMAGES_GUIDED:
        warnings.append(
            f"More than {MAX_IMAGES_GUIDED} images provided ({len(file_paths)}). Processing time will be longer and excessive overlap may increase memory usage."
        )

    for p in file_paths:
        fname = p.name
        ext = p.suffix.lower()

        # Extension check
        if ext not in ALLOWED_EXTENSIONS:
            errors.append(f"Unsupported format for '{fname}': '{ext}'. Allowed formats: JPG, JPEG, PNG, WEBP.")
            continue

        # File size check
        try:
            size = p.stat().st_size
            if size > MAX_FILE_SIZE_BYTES:
                errors.append(f"File '{fname}' exceeds the maximum allowed size of 20 MB ({size / (1024*1024):.1f} MB).")
                continue
            if size == 0:
                errors.append(f"File '{fname}' is empty (0 bytes).")
                continue
        except Exception as e:
            errors.append(f"Cannot read file '{fname}': {str(e)}")
            continue

        # Integrity & Dimension check
        try:
            with Image.open(p) as img:
                img.verify()  # Verify integrity
            # Reopen to check dimensions (verify() closes file)
            with Image.open(p) as img:
                w, h = img.size
                if w < MIN_IMAGE_DIMENSION or h < MIN_IMAGE_DIMENSION:
                    warnings.append(f"Image '{fname}' resolution ({w}x{h}) is very low; feature matching may be unreliable.")
            valid_files.append(p)
        except Exception as e:
            errors.append(f"Image '{fname}' is corrupted or cannot be decoded: {str(e)}")

    is_valid = len(errors) == 0 and len(valid_files) >= MIN_IMAGES_ABSOLUTE
    return ImageValidationResult(is_valid, errors, warnings, valid_files)
