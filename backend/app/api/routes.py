"""
Boring 360 - Main API Routes
Implements:
- POST /api/stitch
- GET /api/panorama/{panorama_id}
- GET /api/panorama/{panorama_id}/viewer
- GET /api/jobs/{job_id}
- GET /api/health
- Plus sample dataset & gallery management endpoints
"""

import time
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone
import cv2

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, status, Query
from fastapi.responses import FileResponse, JSONResponse

from backend.app.core.config import settings
from backend.app.models.schemas import StitchResponse, JobStatusResponse, HealthResponse, PanoramaViewerConfig
from backend.app.services.stitching import run_orb_stitching_pipeline, FullStitchingResult
from backend.app.database import (
    save_job, get_job, save_panorama, get_panorama, list_panoramas, delete_panorama_record
)
from backend.app.utils.file_storage import (
    generate_unique_id, get_job_upload_dir, get_output_path, cleanup_job_files, delete_output_file
)
from backend.app.utils.logger import logger

router = APIRouter(tags=["panoramas"])


def _save_uploaded_files(files: List[UploadFile], target_dir: Path) -> List[Path]:
    """Helper to save uploaded files to a target directory."""
    saved_paths: List[Path] = []
    for file in files:
        safe_name = Path(file.filename or "image.jpg").name
        dest = target_dir / safe_name
        with open(dest, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_paths.append(dest)
    return saved_paths


def _save_stitched_output(result: FullStitchingResult, job_id: str, title: str) -> dict:
    """Helper to persist stitched panorama and its metadata."""
    pano_id = generate_unique_id("pano")
    pano_filename = f"{pano_id}.jpg"
    pano_path = get_output_path(pano_filename)

    final_img = result.panorama_image
    h, w = final_img.shape[:2]

    # Save high-quality JPEG
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

    now_str = datetime.now(timezone.utc).isoformat()
    pano_meta = {
        "panorama_id": pano_id,
        "job_id": job_id,
        "title": title or f"Panorama {pano_id}",
        "filename": pano_filename,
        "image_url": f"/api/panorama/{pano_id}",
        "thumbnail_url": f"/outputs/{thumb_filename}",
        "width": w,
        "height": h,
        "aspect_ratio": round(w / float(h), 2),
        "file_size_bytes": file_size,
        "input_image_count": result.images_processed,
        "usable_image_count": result.images_processed,
        "processing_time_seconds": result.processing_time,
        "is_full_360": result.is_full_360,
        "horizontal_fov": result.horizontal_fov,
        "vertical_fov": result.vertical_fov,
        "stitching_method": f"ORB + {result.matching_algorithm} + {result.alignment_algorithm}",
        "created_at": now_str,
        "diagnostics": {
            "keypoints": result.keypoints_detected,
            "pairwise_matches": result.pairwise_matches,
            "logs": result.logs,
            "warnings": result.warnings,
            "projection_type": result.projection_type
        }
    }
    save_panorama(pano_meta)
    return pano_meta


def run_async_stitching_worker(job_id: str, file_paths: List[Path], title: str):
    """Background worker for asynchronous jobs."""
    try:
        def update_progress(msg: str, pct: int):
            save_job(job_id, "processing", pct, msg)

        update_progress("Starting ORB feature detection...", 15)
        result = run_orb_stitching_pipeline(file_paths, strict_image_count=False, progress_callback=update_progress)

        if not result.success or result.panorama_image is None:
            save_job(job_id, "failed", 0, "Stitching failed", error=result.error_details or result.status_message)
            return

        update_progress("Encoding output panorama...", 90)
        meta = _save_stitched_output(result, job_id, title)

        save_job(
            job_id,
            "completed",
            100,
            "Panorama generated successfully",
            panorama_id=meta["panorama_id"],
            diagnostics=meta["diagnostics"]
        )
    except Exception as e:
        logger.exception(f"Error in background worker for job {job_id}: {str(e)}")
        save_job(job_id, "failed", 0, "Server error during processing", error=str(e))


@router.get("/health", response_model=HealthResponse)
def health_check():
    """
    Returns backend health information and OpenCV version.
    """
    return HealthResponse(
        status="healthy",
        service="Boring 360 Panorama Processing Engine",
        version="1.0.0",
        opencv_version=cv2.__version__
    )


@router.post("/stitch", response_model=StitchResponse)
async def stitch_images(
    files: List[UploadFile] = File(...),
    title: Optional[str] = Form("My Smartphone Panorama"),
    strict_count: bool = Query(False, description="Enforce strict 8-12 image count")
):
    """
    Core CV stitching endpoint:
    Accepts 8-12 overlapping smartphone photographs and executes genuine
    ORB -> BFMatcher (Hamming) -> RANSAC Homography -> Warping -> Blending.
    """
    num_files = len(files)
    if num_files < settings.MIN_IMAGES_ABSOLUTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"At least {settings.MIN_IMAGES_ABSOLUTE} images are required for stitching. Provided: {num_files}."
        )

    if strict_count:
        if num_files < settings.MIN_IMAGES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Smartphone panorama workflow requires 8–12 overlapping photographs. Provided: {num_files}."
            )
        if num_files > settings.MAX_IMAGES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum allowed photographs is 12. Provided: {num_files}."
            )

    job_id = generate_unique_id("job_sync")
    upload_dir = get_job_upload_dir(job_id)
    saved_paths = _save_uploaded_files(files, upload_dir)

    # Execute genuine CV stitching pipeline
    result: FullStitchingResult = run_orb_stitching_pipeline(saved_paths, strict_image_count=strict_count)

    if not result.success or result.panorama_image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error_details or result.status_message
        )

    # Save output and metadata
    meta = _save_stitched_output(result, job_id, title or "Boring 360 Panorama")
    inlier_counts = [m["inlier_count"] for m in result.pairwise_matches]

    return StitchResponse(
        success=True,
        panorama_id=meta["panorama_id"],
        panorama_url=f"/api/panorama/{meta['panorama_id']}",
        processing_time=result.processing_time,
        images_processed=result.images_processed,
        feature_algorithm=result.feature_algorithm,
        matching_algorithm=result.matching_algorithm,
        alignment_algorithm=result.alignment_algorithm,
        message="Panorama generated successfully",
        output_dimensions=[meta["width"], meta["height"]],
        horizontal_fov=result.horizontal_fov,
        vertical_fov=result.vertical_fov,
        projection_type=result.projection_type,
        inlier_counts=inlier_counts,
        warnings=result.warnings
    )


@router.post("/panoramas", response_model=JobStatusResponse)
async def create_panorama_job(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    title: Optional[str] = Form("My Smartphone Panorama")
):
    """
    Asynchronous panorama generation job creation.
    """
    if len(files) < settings.MIN_IMAGES_ABSOLUTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"At least {settings.MIN_IMAGES_ABSOLUTE} images are required to generate a panorama."
        )

    job_id = generate_unique_id("job")
    upload_dir = get_job_upload_dir(job_id)
    saved_paths = _save_uploaded_files(files, upload_dir)

    now_str = datetime.now(timezone.utc).isoformat()
    save_job(job_id, "queued", 0, "Upload received and queued for processing...")

    background_tasks.add_task(run_async_stitching_worker, job_id, saved_paths, title or "Panorama")

    return JobStatusResponse(
        job_id=job_id,
        stage="queued",
        progress_percent=0,
        message="Upload received and queued for processing...",
        created_at=now_str,
        updated_at=now_str
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Returns actual job status and progress.
    """
    row = get_job(job_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    return JobStatusResponse(
        job_id=row["job_id"],
        panorama_id=row.get("panorama_id"),
        stage=row["stage"],
        progress_percent=row["progress_percent"],
        message=row.get("message") or "",
        error=row.get("error"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        diagnostics=row.get("diagnostics")
    )


@router.get("/panorama/{panorama_id}")
@router.get("/panoramas/{panorama_id}/image")
async def get_panorama_image(panorama_id: str):
    """
    Returns the generated panorama image file.
    """
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


@router.get("/panorama/{panorama_id}/viewer", response_model=PanoramaViewerConfig)
@router.get("/panoramas/{panorama_id}/viewer", response_model=PanoramaViewerConfig)
async def get_panorama_viewer_config(panorama_id: str):
    """
    Returns configuration for Pannellum viewer.
    Accurately handles partial cylindrical FOV vs spherical.
    """
    r = get_panorama(panorama_id)
    if not r:
        raise HTTPException(status_code=404, detail=f"Panorama '{panorama_id}' not found.")

    is_full = r.get("is_full_360", False)
    hfov = r.get("horizontal_fov", 180.0)
    vfov = r.get("vertical_fov", 60.0)

    # For Pannellum:
    # haov and vaov constrain sphere rendering so partial panoramas don't distort or wrap awkwardly
    haov = 360.0 if is_full else min(360.0, max(60.0, hfov))
    vaov = 180.0 if is_full else min(180.0, max(45.0, vfov))

    return PanoramaViewerConfig(
        panorama_id=r["panorama_id"],
        image_url=f"/api/panorama/{r['panorama_id']}",
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
        title=r.get("title") or "Boring 360 Panorama",
        description=f"Generated with {r.get('stitching_method', 'ORB Pipeline')} • {r.get('width', 0)}x{r.get('height', 0)}px"
    )


@router.get("/panoramas")
async def get_all_panoramas(limit: int = 50):
    """Returns all created panoramas for gallery view."""
    return list_panoramas(limit=limit)


@router.get("/panoramas/{panorama_id}")
async def get_panorama_by_id(panorama_id: str):
    r = get_panorama(panorama_id)
    if not r:
        raise HTTPException(status_code=404, detail=f"Panorama '{panorama_id}' not found.")
    return r


@router.delete("/panoramas/{panorama_id}")
async def delete_panorama_endpoint(panorama_id: str):
    r = get_panorama(panorama_id)
    if not r:
        raise HTTPException(status_code=404, detail=f"Panorama '{panorama_id}' not found.")

    delete_output_file(r["filename"])
    if r.get("thumbnail_url"):
        delete_output_file(Path(r["thumbnail_url"]).name)
    cleanup_job_files(r["job_id"])
    delete_panorama_record(panorama_id)
    return {"status": "success", "message": f"Panorama '{panorama_id}' deleted."}


@router.get("/sample-dataset")
async def get_sample_dataset_info():
    sample_dir = Path(__file__).resolve().parent.parent.parent.parent / "sample-data"
    files = sorted(list(sample_dir.glob("smartphone_shot_*.jpg")))
    return {
        "status": "ready",
        "count": len(files),
        "files": [f.name for f in files],
        "description": "8 sequential overlapping indoor smartphone photographs with 35% overlap"
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

    now_str = datetime.now(timezone.utc).isoformat()
    save_job(job_id, "queued", 0, "Sample dataset loaded. Queued for stitching...")
    background_tasks.add_task(run_async_stitching_worker, job_id, saved_paths, "Sample Smartphone Panorama (8 Shots)")

    return JobStatusResponse(
        job_id=job_id,
        stage="queued",
        progress_percent=0,
        message="Sample dataset loaded. Queued for stitching...",
        created_at=now_str,
        updated_at=now_str
    )
