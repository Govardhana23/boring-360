# BORING 360 – Intelligent Smartphone Panorama Generation Platform

> **Capture Reality. Experience Everywhere.**

BORING 360 is an end-to-end computer vision product that transforms 8–12 regular overlapping smartphone photographs into immersive panoramic experiences with interactive 360° navigation.

Unlike UI-only demonstrations or mockups, Boring 360 incorporates real OpenCV stitching pipelines (bundle adjustment, SIFT/ORB keypoints, RANSAC homography, multi-band seam blending, auto-cropping), AI-assisted capture quality analysis, and an interactive WebGL Pannellum 360 viewer.

---

## 🌟 Key Features

- **Guided Smartphone Capture Workflow**: Drag-and-drop ingestion of 8–12 photos, automatic EXIF orientation correction, sequence reordering, and format validation (JPG, JPEG, PNG, WEBP up to 20MB).
- **Dual Computer Vision Stitching Engine**:
  - Primary: OpenCV built-in `Stitcher_PANORAMA` and `Stitcher_SCANS` with bundle adjustment.
  - Fallback: Modular cylindrical projection, SIFT feature matching with Lowe's ratio test, RANSAC homography estimation, and distance-feathered seam blending.
- **AI-Assisted Quality Assessment**:
  - Blur detection via Laplacian variance $\text{Var}(\Delta I)$.
  - Exposure assessment with shadow and highlight clipping detection.
  - Pairwise overlap feature match counting and actionable retake suggestions.
- **Geometric Truthfulness**:
  - Automatically differentiates between full $360^\circ \times 180^\circ$ spherical coverage and single-row partial cylindrical panoramas.
  - Computes accurate Horizontal ($\text{haov}$) and Vertical ($\text{vaov}$) angles of view to prevent artificial sphere distortion.
- **Interactive 360 Viewer**: Powered by Pannellum with mouse dragging, zoom, auto-rotation, fullscreen, and compass.
- **1-Click Sample Dataset**: Built-in 8-shot indoor room dataset to test and demonstrate full stitching locally with zero setup.

---

## 🏗️ Architecture & Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Lucide React, Framer Motion |
| **Backend** | Python 3.11+, FastAPI, Uvicorn, Pydantic v2 |
| **Computer Vision** | OpenCV (`opencv-python-headless`), NumPy, Pillow |
| **360 Viewer** | Pannellum (WebGL) |
| **Data Storage** | SQLite (`boring360.db`) with persistent job and metadata records |

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python**: 3.11 or higher
- **Node.js**: v18 or higher (with npm)

### 1. Clone & Setup Repository
```bash
git clone https://github.com/your-org/boring-360.git
cd boring-360
```

### 2. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
The FastAPI backend will start at `http://localhost:8000`. You can test health at `http://localhost:8000/api/health` and view OpenAPI documentation at `http://localhost:8000/docs`.

### 3. Frontend Setup
In a second terminal:
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
Open your browser at `http://localhost:3000`.

---

## 🧪 Automated Testing

Boring 360 includes automated unit and integration tests covering the stitcher pipeline, image quality diagnostics, and REST API endpoints:

```bash
# Run all tests
backend\.venv\Scripts\python -m pytest tests/ -v
```

### Test Suite Summary:
1. `tests/test_stitcher.py`:
   - Validates the 8-shot guided workflow dataset.
   - Evaluates quality assessment on realistic textures.
   - Executes real OpenCV stitching pipeline to confirm high-resolution panorama generation and FOV calculation.
2. `tests/test_quality.py`:
   - Verifies Laplacian variance blur thresholding.
   - Tests underexposure and overexposure warnings.
   - Tests insufficient overlap detection between disjoint image pairs.
3. `tests/test_api.py`:
   - Tests `/api/health`, `/api/sample-dataset`, `/api/create-sample-panorama`, and validation error handling on invalid image counts.

---

## 📸 Guided Capture Best Practices

1. **Stationary Viewpoint**: Stand in one spot and rotate the smartphone around its optical camera center.
2. **25%–40% Overlap**: Ensure each photograph shares about one third of the frame with the previous shot.
3. **Locked Exposure**: Lock AE/AF on your smartphone to maintain consistent brightness across all frames.
4. **Left-to-Right Sequence**: Capture shots sequentially in a steady rotational sweep.

---

## ⚠️ Known Limitations & Future Roadmap

### Known Limitations
- **Single-Row Vertical Coverage**: A single-row rotation captures a wide horizontal FOV ($\sim 180^\circ$ to $360^\circ$) but does not cover the zenith (ceiling) or nadir (ground). Boring 360 communicates this limitation honestly and configures Pannellum with calibrated angular bounds.
- **Dynamic Foreground Objects**: Fast-moving people or vehicles across overlap seams can cause ghosting artifacts.

### Future Roadmap
- **Multi-Row Spherical Capture**: Support upper, middle, and lower row capture sequences for complete $360^\circ \times 180^\circ$ full sphere synthesis.
- **Deep Feature Matching**: Optional local neural matching using SuperPoint / LightGlue for challenging textureless surfaces (e.g. blank walls).
- **Virtual Reality / Gyroscope Navigation**: Device orientation controls on mobile web browsers.
- **Multi-Scene Virtual Tours**: Linking multiple stitched panoramas with interactive hotspots.

---

## 📄 License
MIT License. Built for seamless smartphone computer vision panorama generation.
