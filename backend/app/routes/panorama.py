import asyncio
import os
import shutil
import time
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone
import cv2

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, status
from fastapi.responses import FileResponse, JSONResponse

from backend.app.models.job import (
    JobStage, JobStatusResponse, JobDiagnostics, ImageQualityAssessment, PairwiseOverlapScore
)
from backend.app.models.panorama import PanoramaMetadata, PanoramaViewerConfig
from backend.app.database import (
    save_job, get_job, save_panorama, get_panorama, list_panoramas, delete_panorama_record
)
from backend.app.services.image_validation import validate_uploaded_files
from backend.app.services.image_preprocessing import preprocess_images_for_stitching
from backend.app.services.quality_assessment import assess_image_sequence_quality
from backend.app.services.panorama_stitcher import stitch_panorama_pipeline
from backend.app.utils.file_storage import (
    generate_unique_id, get_job_upload_dir, get_output_path, cleanup_job_files, delete_output_file
)
from backend.app.utils.logger import logger

router = APIRouter(prefix="/api", tags=["panoramas"])


def run_stitching_job_task(job_id: str, file_paths: List[Path], title: str):
    """
    Background worker executing the real computer vision stitching stages.
    """
    logger.info(f"Starting stitching job {job_id} for {len(file_paths)} images.")
    diag = JobDiagnostics(input_image_count=len(file_paths))

    try:
        # Stage 1: Validation
        save_job(job_id, JobStage.VALIDATING.value, 10, "Validating input files and formats...")
        val_res = validate_uploaded_files(file_paths)
        if not val_res.is_valid:
            err_msg = "; ".join(val_res.errors)
            diag.warnings.extend(val_res.warnings)
            save_job(job_id, JobStage.FAILED.value, 10, "Validation failed", error=err_msg, diagnostics=diag.model_dump())
            return

        diag.warnings.extend(val_res.warnings)
        diag.log_messages.append(f"Validated {len(val_res.valid_files)} image files.")

        # Stage 2: Preprocessing
        save_job(job_id, JobStage.PREPROCESSING.value, 25, "Preprocessing images & correcting EXIF orientation...")
        images_bgr, meta_list = preprocess_images_for_stitching(val_res.valid_files, max_dimension=1920)
        diag.usable_image_count = len(images_bgr)
        diag.log_messages.append(f"Preprocessed {len(images_bgr)} images to optimal stitching resolution.")

        # Stage 3: Quality Assessment
        save_job(job_id, JobStage.FEATURE_DETECTION.value, 40, "Running AI quality assessment & detecting keypoints...")
        filenames = [p.name for p in val_res.valid_files]
        file_sizes = [p.stat().st_size for p in val_res.valid_files]
        assessments, pairwise_scores, qual_warnings = assess_image_sequence_quality(images_bgr, filenames, file_sizes)

        diag.image_assessments = assessments
        diag.pairwise_overlaps = pairwise_scores
        diag.warnings.extend(qual_warnings)
        diag.log_messages.append(f"Computed quality assessment for all {len(images_bgr)} images.")

        has_loop = False
        if len(pairwise_scores) > 0 and pairwise_scores[-1].image_a == filenames[-1] and pairwise_scores[-1].image_b == filenames[0]:
            has_loop = pairwise_scores[-1].good_matches >= 30

        # Stage 4 & 5: Feature Matching & Alignment
        save_job(job_id, JobStage.FEATURE_MATCHING.value, 55, "Matching features and estimating camera alignment...")
        time.sleep(0.3)

        save_job(job_id, JobStage.CAMERA_ALIGNMENT.value, 70, "Performing bundle adjustment and geometric alignment...")
        time.sleep(0.3)

        # Stage 6: Warping & Seam Blending
        save_job(job_id, JobStage.SEAM_BLENDING.value, 85, "Warping images and multi-band seam blending...")
        stitch_res = stitch_panorama_pipeline(images_bgr, filenames, has_loop_closure=has_loop)

        diag.log_messages.extend(stitch_res.logs)
        diag.warnings.extend(stitch_res.warnings)
        diag.stitching_method_used = stitch_res.method_used
        diag.stitching_status_code = stitch_res.status_code
        diag.stitching_status_message = stitch_res.status_message
        diag.elapsed_time_seconds = stitch_res.elapsed_seconds
        diag.is_full_360 = stitch_res.is_full_360
        diag.horizontal_fov_degrees = stitch_res.horizontal_fov
        diag.vertical_fov_degrees = stitch_res.vertical_fov

        if not stitch_res.success or stitch_res.panorama_image is None:
            err_msg = f"Stitching failed: {stitch_res.status_message}"
            save_job(job_id, JobStage.FAILED.value, 85, "Stitching failed", error=err_msg, diagnostics=diag.model_dump())
            return

        # Stage 7: Generating Final Panorama & Saving
        save_job(job_id, JobStage.GENERATING_PANORAMA.value, 95, "Encoding high-resolution panorama and generating metadata...")

        pano_id = generate_unique_id("pano")
        pano_filename = f"{pano_id}.jpg"
        pano_path = get_output_path(pano_filename)

        final_img = stitch_res.panorama_image
        h, w = final_img.shape[:2]
        diag.output_width = w
        diag.output_height = h
        diag.aspect_ratio = round(w / float(h), 2)

        # Save main panorama
        cv2.imwrite(str(pano_path), final_img, [cv2.IMWRITE_JPEG_QUALITY, 93])
        file_size = pano_path.stat().st_size

        # Create thumbnail
        thumb_filename = f"{pano_id}_thumb.jpg"
        thumb_path = get_output_path(thumb_filename)
        thumb_scale = 400.0 / float(w)
        thumb_w = 400
        thumb_h = max(100, int(h * thumb_scale))
        thumb_img = cv2.resize(final_img, (thumb_w, thumb_h), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(thumb_path), thumb_img, [cv2.IMWRITE_JPEG_QUALITY, 85])

        # Save metadata
        now_str = datetime.now(timezone.utc).isoformat()
        pano_meta = {
            "panorama_id": pano_id,
            "job_id": job_id,
            "title": title or f"Panorama {pano_id}",
            "filename": pano_filename,
            "image_url": f"/api/panoramas/{pano_id}/image",
            "thumbnail_url": f"/outputs/{thumb_filename}",
            "width": w,
            "height": h,
            "aspect_ratio": diag.aspect_ratio,
            "file_size_bytes": file_size,
            "input_image_count": len(file_paths),
            "usable_image_count": stitch_res.usable_image_count,
            "processing_time_seconds": stitch_res.elapsed_seconds,
            "is_full_360": stitch_res.is_full_360,
            "horizontal_fov": stitch_res.horizontal_fov,
            "vertical_fov": stitch_res.vertical_fov,
            "stitching_method": stitch_res.method_used,
            "created_at": now_str,
            "diagnostics": diag.model_dump(),
        }
        save_panorama(pano_meta)

        # Mark job completed
        save_job(
            job_id,
            JobStage.COMPLETED.value,
            100,
            "Panorama successfully generated!",
            panorama_id=pano_id,
            diagnostics=diag.model_dump()
        )
        logger.info(f"Job {job_id} successfully completed. Created panorama {pano_id}.")

    except Exception as e:
        logger.exception(f"Unexpected error during job {job_id}: {str(e)}")
        save_job(job_id, JobStage.FAILED.value, 0, "Server error during processing", error=str(e), diagnostics=diag.model_dump())


@router.post("/panoramas", response_model=JobStatusResponse)
async def create_panorama_job(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    title: Optional[str] = Form("My Smartphone Panorama")
):
    if len(files) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 images are required to generate a panorama."
        )

    job_id = generate_unique_id("job")
    upload_dir = get_job_upload_dir(job_id)
    saved_paths: List[Path] = []

    for file in files:
        safe_name = Path(file.filename or "image.jpg").name
        dest = upload_dir / safe_name
        with open(dest, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_paths.append(dest)

    save_job(job_id, JobStage.QUEUED.value, 0, "Upload received and queued for processing...")

    # Spawn background worker
    background_tasks.add_task(run_stitching_job_task, job_id, saved_paths, title or "Panorama")

    now_str = datetime.now(timezone.utc).isoformat()
    return JobStatusResponse(
        job_id=job_id,
        stage=JobStage.QUEUED,
        progress_percent=0,
        message="Upload received and queued for processing...",
        created_at=now_str,
        updated_at=now_str
    )


@router.get("/sample-dataset")
async def get_sample_dataset_info():
    sample_dir = Path(__file__).resolve().parent.parent.parent.parent / "sample-data"
    files = sorted(list(sample_dir.glob("smartphone_shot_*.jpg")))
    return {
        "status": "ready",
        "count": len(files),
        "files": [f.name for f in files],
        "description": "8 sequential overlapping indoor smartphone photographs"
    }


@router.post("/create-sample-panorama", response_model=JobStatusResponse)
async def create_sample_panorama(background_tasks: BackgroundTasks):
    sample_dir = Path(__file__).resolve().parent.parent.parent.parent / "sample-data"
    files = sorted(list(sample_dir.glob("smartphone_shot_*.jpg")))
    if not files:
        raise HTTPException(status_code=404, detail="Sample dataset not found on server.")

    job_id = generate_unique_id("job_sample")
    upload_dir = get_job_upload_dir(job_id)
    saved_paths: List[Path] = []

    for f in files:
        dest = upload_dir / f.name
        shutil.copyfile(f, dest)
        saved_paths.append(dest)

    save_job(job_id, JobStage.QUEUED.value, 0, "Sample dataset loaded. Queued for stitching...")
    background_tasks.add_task(run_stitching_job_task, job_id, saved_paths, "Sample Indoor Living Space 360")

    now_str = datetime.now(timezone.utc).isoformat()
    return JobStatusResponse(
        job_id=job_id,
        stage=JobStage.QUEUED,
        progress_percent=0,
        message="Sample dataset loaded. Queued for stitching...",
        created_at=now_str,
        updated_at=now_str
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    row = get_job(job_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    diag = None
    if row.get("diagnostics"):
        try:
            diag = JobDiagnostics(**row["diagnostics"])
        except Exception:
            diag = None

    return JobStatusResponse(
        job_id=row["job_id"],
        panorama_id=row.get("panorama_id"),
        stage=row["stage"],
        progress_percent=row["progress_percent"],
        message=row.get("message") or "",
        error=row.get("error"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        diagnostics=diag
    )


@router.get("/panoramas", response_model=List[PanoramaMetadata])
async def get_all_panoramas(limit: int = 50):
    rows = list_panoramas(limit=limit)
    res = []
    for r in rows:
        diag = None
        if r.get("diagnostics"):
            try:
                diag = JobDiagnostics(**r["diagnostics"])
            except Exception:
                diag = None
        res.append(PanoramaMetadata(
            panorama_id=r["panorama_id"],
            job_id=r["job_id"],
            title=r["title"],
            filename=r["filename"],
            image_url=r["image_url"],
            thumbnail_url=r.get("thumbnail_url"),
            width=r["width"],
            height=r["height"],
            aspect_ratio=r["aspect_ratio"],
            file_size_bytes=r["file_size_bytes"],
            input_image_count=r["input_image_count"],
            usable_image_count=r["usable_image_count"],
            processing_time_seconds=r["processing_time_seconds"],
            is_full_360=r["is_full_360"],
            horizontal_fov=r["horizontal_fov"],
            vertical_fov=r["vertical_fov"],
            stitching_method=r["stitching_method"],
            created_at=r["created_at"],
            diagnostics=diag
        ))
    return res


@router.get("/panoramas/{panorama_id}", response_model=PanoramaMetadata)
async def get_panorama_by_id(panorama_id: str):
    r = get_panorama(panorama_id)
    if not r:
        raise HTTPException(status_code=404, detail=f"Panorama '{panorama_id}' not found.")

    diag = None
    if r.get("diagnostics"):
        try:
            diag = JobDiagnostics(**r["diagnostics"])
        except Exception:
            diag = None

    return PanoramaMetadata(
        panorama_id=r["panorama_id"],
        job_id=r["job_id"],
        title=r["title"],
        filename=r["filename"],
        image_url=r["image_url"],
        thumbnail_url=r.get("thumbnail_url"),
        width=r["width"],
        height=r["height"],
        aspect_ratio=r["aspect_ratio"],
        file_size_bytes=r["file_size_bytes"],
        input_image_count=r["input_image_count"],
        usable_image_count=r["usable_image_count"],
        processing_time_seconds=r["processing_time_seconds"],
        is_full_360=r["is_full_360"],
        horizontal_fov=r["horizontal_fov"],
        vertical_fov=r["vertical_fov"],
        stitching_method=r["stitching_method"],
        created_at=r["created_at"],
        diagnostics=diag
    )


@router.get("/panoramas/{panorama_id}/image")
async def get_panorama_image(panorama_id: str):
    r = get_panorama(panorama_id)
    if not r:
        raise HTTPException(status_code=404, detail=f"Panorama '{panorama_id}' not found.")

    target_file = get_output_path(r["filename"])
    if not target_file.exists():
        raise HTTPException(status_code=404, detail="Panorama image file missing on disk.")

    return FileResponse(
        path=str(target_file),
        media_type="image/jpeg",
        filename=r["filename"]
    )


@router.get("/panoramas/{panorama_id}/viewer", response_model=PanoramaViewerConfig)
async def get_panorama_viewer_config(panorama_id: str):
    r = get_panorama(panorama_id)
    if not r:
        raise HTTPException(status_code=404, detail=f"Panorama '{panorama_id}' not found.")

    is_full = r["is_full_360"]
    hfov = r["horizontal_fov"]
    vfov = r["vertical_fov"]

    # For Pannellum:
    # If full 360: haov=360, vaov=180
    # If partial: haov and vaov constrain sphere rendering so it doesn't wrap awkwardly!
    haov = 360.0 if is_full else min(360.0, max(60.0, hfov))
    vaov = 180.0 if is_full else min(180.0, max(45.0, vfov))

    return PanoramaViewerConfig(
        panorama_id=r["panorama_id"],
        image_url=r["image_url"],
        type="equirectangular",
        is_full_360=is_full,
        haov=haov,
        vaov=vaov,
        v_offset=0.0,
        auto_rotate=-1.5,
        compass=True,
        hfov=min(100.0, haov * 0.8),
        min_hfov=30.0,
        max_hfov=min(120.0, haov),
        title=r["title"],
        description=f"Generated with {r['stitching_method']} • {r['width']}x{r['height']}px"
    )


@router.delete("/panoramas/{panorama_id}")
async def delete_panorama_endpoint(panorama_id: str):
    r = get_panorama(panorama_id)
    if not r:
        raise HTTPException(status_code=404, detail=f"Panorama '{panorama_id}' not found.")

    # Delete output files
    delete_output_file(r["filename"])
    if r.get("thumbnail_url"):
        thumb_name = Path(r["thumbnail_url"]).name
        delete_output_file(thumb_name)

    # Delete job upload files
    cleanup_job_files(r["job_id"])

    # Remove record from database
    delete_panorama_record(panorama_id)
    return {"status": "success", "message": f"Panorama '{panorama_id}' deleted."}
