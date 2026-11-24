# BORING 360 REST API Specification

Base URL: `http://localhost:8000/api`

---

## Endpoints

### 1. Health Check
`GET /api/health`

Returns service health status.

**Response `200 OK`**:
```json
{
  "status": "healthy",
  "service": "Boring 360 Panorama Processing Engine",
  "version": "1.0.0"
}
```

---

### 2. Create Panorama Job
`POST /api/panoramas`

Accepts multiple photograph files (`multipart/form-data`) and initiates background stitching.

**Request Form Data**:
- `files`: List of binary images (JPG, PNG, WEBP, up to 20MB each)
- `title`: String (optional, e.g. "Sunset Living Room")

**Response `200 OK`**:
```json
{
  "job_id": "job_a1b2c3d4e5f6",
  "stage": "queued",
  "progress_percent": 0,
  "message": "Upload received and queued for processing...",
  "created_at": "2026-11-24T12:00:00Z",
  "updated_at": "2026-11-24T12:00:00Z"
}
```

---

### 3. Get Job Status
`GET /api/jobs/{job_id}`

Retrieves current status, progress percentage, diagnostic warnings, and generated panorama ID.

**Response `200 OK`**:
```json
{
  "job_id": "job_a1b2c3d4e5f6",
  "panorama_id": "pano_9876543210ab",
  "stage": "completed",
  "progress_percent": 100,
  "message": "Panorama successfully generated!",
  "diagnostics": {
    "input_image_count": 8,
    "usable_image_count": 8,
    "stitching_method_used": "OpenCV Stitcher (PANORAMA)",
    "is_full_360": false,
    "horizontal_fov_degrees": 310.0,
    "vertical_fov_degrees": 50.0,
    "output_width": 4820,
    "output_height": 1540,
    "aspect_ratio": 3.13,
    "elapsed_time_seconds": 3.42,
    "warnings": []
  }
}
```

---

### 4. List Panoramas
`GET /api/panoramas`

Returns all stored panoramas ordered chronologically.

**Response `200 OK`**: Array of `PanoramaMetadata` objects.

---

### 5. Get Panorama Metadata
`GET /api/panoramas/{panorama_id}`

Returns complete metadata for a single panorama.

---

### 6. Get Panorama Image File
`GET /api/panoramas/{panorama_id}/image`

Serves the full-resolution stitched JPEG image file.

---

### 7. Get Panorama Viewer Configuration
`GET /api/panoramas/{panorama_id}/viewer`

Returns Pannellum-ready configuration JSON with accurate FOV geometry.

**Response `200 OK`**:
```json
{
  "panorama_id": "pano_9876543210ab",
  "image_url": "/api/panoramas/pano_9876543210ab/image",
  "type": "equirectangular",
  "is_full_360": false,
  "haov": 310.0,
  "vaov": 50.0,
  "v_offset": 0.0,
  "auto_rotate": -1.5,
  "compass": true,
  "hfov": 100.0,
  "min_hfov": 30.0,
  "max_hfov": 120.0,
  "title": "Living Room 360",
  "description": "Generated with OpenCV Stitcher (PANORAMA)"
}
```

---

### 8. Delete Panorama
`DELETE /api/panoramas/{panorama_id}`

Deletes panorama record from SQLite and cleans up generated output image files from disk.

---

### 9. Sample Dataset Endpoints
- `GET /api/sample-dataset`: Lists available pre-packaged test images.
- `POST /api/create-sample-panorama`: Automatically launches a stitching job using the 8-shot room sequence.
