# BORING 360 Architecture Overview

**BORING 360** is an intelligent smartphone panorama generation and immersive visualization platform. It converts standard sequential smartphone photographs (8–12 shots) into wide cylindrical and spherical panoramas without requiring dedicated 360 hardware.

---

## 1. System Architecture

```mermaid
graph TD
    A[Smartphone Capture Sequence<br/>8-12 Overlapping Photos] --> B[React Frontend<br/>Vite + TypeScript + Tailwind]
    B -->|Multipart POST /api/panoramas| C[FastAPI Backend Engine]
    
    subgraph Computer Vision Core Pipeline
        C --> D[1. Image Validation & EXIF Correction]
        D --> E[2. Quality Assessment<br/>Laplacian Blur & Exposure Stats]
        E --> F[3. Feature Extraction<br/>SIFT / ORB Keypoints]
        F --> G[4. Pairwise Correspondence<br/>FLANN / BFMatcher & Lowe's Ratio]
        G --> H[5. Camera Bundle Adjustment & RANSAC]
        H --> I[6. Cylindrical / Spherical Warping]
        I --> J[7. Multi-Band Seam Blending & Gain Matching]
        J --> K[8. Black Border Auto-Cropping]
    end
    
    K --> L[High-Resolution Panorama JPEG + Thumbnail]
    L --> M[SQLite Database<br/>Metadata & FOV Diagnostics]
    M -->|GET /api/panoramas/{id}/viewer| N[Pannellum 360 Viewer]
    N -->|Interactive Navigation| B
```

---

## 2. Core Modules & Responsibilities

### Frontend (`frontend/`)
- **React 18 + TypeScript + Vite**: Responsive single-page application with dark navy/charcoal styling and cyan/teal accents.
- **Upload Workflow**: Drag-and-drop file ingestion, file format validation, sequence reordering, capture checklists, and 1-click sample dataset loader.
- **Processing Dashboard**: Real-time multi-stage status tracker showing OpenCV execution steps and live diagnostic log stream.
- **Results View**: Resolution metrics, megapixels calculation, processing duration, and quality warnings.
- **Pannellum 360 Viewer**: WebGL-accelerated interactive sphere/cylinder viewer with zoom, autorotation, fullscreen, and field-of-view configuration.

### Backend (`backend/app/`)
- **FastAPI + Uvicorn**: High-performance asynchronous REST API.
- **SQLite Database (`backend/app/database.py`)**: Persistent storage of panorama metadata, geometric field-of-view estimates, and detailed image quality diagnostics.
- **OpenCV Computer Vision Engine (`backend/app/services/`)**:
  - `image_validation.py`: Format, file size, dimension, and integrity validation.
  - `image_preprocessing.py`: EXIF orientation transposition and adaptive resolution scaling.
  - `quality_assessment.py`: Blur measurement via Laplacian variance $\text{Var}(\Delta I)$, exposure histogram clipping checks, and pairwise overlap scores.
  - `feature_detection.py`: SIFT (Scale-Invariant Feature Transform) and ORB feature extraction.
  - `image_matching.py`: FLANN and Brute-Force $k$-NN matcher with Lowe's ratio test ($d_1 / d_2 < 0.75$) and RANSAC homography estimation.
  - `image_alignment.py`: Cylindrical surface projection ($x' = f \tan(x/f)$) to avoid planar perspective divergence.
  - `image_blending.py`: Distance-transform weighted feathering, multi-band blending, and rectangular auto-cropping.
  - `panorama_stitcher.py`: Orchestrates primary OpenCV `Stitcher_PANORAMA` and `Stitcher_SCANS` modes with fallback to modular cylindrical sequential stitching.

---

## 3. Geometric Truthfulness & Field of View (FOV)

A critical principle of Boring 360 is **geometric truthfulness**:
1. Single-row smartphone captures taken while standing in place cover a wide horizontal angle ($\sim 180^\circ$ to $360^\circ$), but only a limited vertical angle ($\sim 45^\circ$ to $65^\circ$).
2. Unlike distorted consumer apps that stretch single-row captures into warped pseudo-spheres, Boring 360 calculates horizontal angle of view ($\text{haov}$) and vertical angle of view ($\text{vaov}$).
3. The Pannellum viewer is dynamically configured with these limits (`haov`, `vaov`, `vOffset`) so users experience a geometrically accurate panorama without zenith/nadir distortion.
