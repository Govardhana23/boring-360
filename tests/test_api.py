import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_sample_dataset_endpoint():
    response = client.get("/api/sample-dataset")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["count"] == 8


def test_panoramas_validation_rejects_single_image():
    # Only 1 image provided
    files = [("files", ("test1.jpg", b"fake image bytes", "image/jpeg"))]
    response = client.post("/api/panoramas", files=files)
    assert response.status_code == 400
    assert "At least 2 images" in response.json()["detail"]


def test_create_sample_panorama_job():
    response = client.post("/api/create-sample-panorama")
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["stage"] in ["queued", "validating", "preprocessing"]

    job_id = data["job_id"]
    status_resp = client.get(f"/api/jobs/{job_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["job_id"] == job_id
