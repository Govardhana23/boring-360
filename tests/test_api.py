import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app
import cv2

client = TestClient(app)
SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample-data"


def test_health_endpoint():
    """Verify health endpoint returns OpenCV version and system status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "opencv_version" in data
    assert data["opencv_version"] == cv2.__version__
    assert "ORB" in data["feature_detector"]


def test_sample_dataset_endpoint():
    """Verify sample dataset endpoint lists the 8 sample smartphone images."""
    response = client.get("/api/sample-dataset")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["count"] == 8
    assert len(data["files"]) == 8


def test_stitch_validation_rejects_single_image():
    """Verify POST /api/stitch rejects less than minimum images."""
    files = [("files", ("shot1.jpg", b"dummy image bytes", "image/jpeg"))]
    response = client.post("/api/stitch", files=files)
    assert response.status_code == 400
    assert "At least 2 images are required" in response.json()["detail"]


def test_stitch_strict_count_validation():
    """Verify strict count enforcement (8-12 images)."""
    sample_files = sorted(list(SAMPLE_DIR.glob("smartphone_shot_*.jpg")))
    # Send 4 images with strict_count=true
    files = [("files", (p.name, open(p, "rb").read(), "image/jpeg")) for p in sample_files[:4]]
    response = client.post("/api/stitch?strict_count=true", files=files)
    assert response.status_code == 400
    assert "requires 8–12" in response.json()["detail"]


def test_post_stitch_end_to_end_real_photos():
    """
    Verify POST /api/stitch executes genuine ORB computer vision stitching
    and returns required schema.
    """
    sample_files = sorted(list(SAMPLE_DIR.glob("smartphone_shot_*.jpg")))
    assert len(sample_files) == 8

    files = [("files", (p.name, open(p, "rb").read(), "image/jpeg")) for p in sample_files]
    response = client.post("/api/stitch", files=files, data={"title": "Test Living Room 360"})

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "panorama_id" in data
    assert "panorama_url" in data
    assert data["images_processed"] == 8
    assert data["processing_time"] > 0
    assert data["feature_algorithm"] == "ORB"
    assert data["matching_algorithm"] == "BFMatcher-Hamming"
    assert data["alignment_algorithm"] == "RANSAC-Homography"
    assert "output_dimensions" in data
    assert data["output_dimensions"][0] > 1200  # Wide panorama width

    pano_id = data["panorama_id"]

    # Test GET /api/panorama/{panorama_id} returns image
    img_resp = client.get(f"/api/panorama/{pano_id}")
    assert img_resp.status_code == 200
    assert img_resp.headers["content-type"] == "image/jpeg"
    assert len(img_resp.content) > 50000

    # Test GET /api/panorama/{panorama_id}/viewer returns Pannellum config
    viewer_resp = client.get(f"/api/panorama/{pano_id}/viewer")
    assert viewer_resp.status_code == 200
    viewer_data = viewer_resp.json()
    assert viewer_data["panorama_id"] == pano_id
    assert viewer_data["type"] == "equirectangular"
    assert "haov" in viewer_data
    assert "vaov" in viewer_data


def test_create_sample_panorama_job():
    """Verify asynchronous job creation endpoint."""
    response = client.post("/api/create-sample-panorama")
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["stage"] in ["queued", "processing", "completed"]

    job_id = data["job_id"]
    status_resp = client.get(f"/api/jobs/{job_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["job_id"] == job_id
