# BORING 360 User & Capture Guide

Welcome to **BORING 360**, the intelligent platform for generating panoramic and immersive 360 experiences from smartphone photographs.

---

## 1. How To Capture Overlapping Smartphone Photographs

To achieve clean, seamless stitches without stitching errors or ghosting:

1. **Rotate on a Fixed Point**:
   - Stand firmly in one location.
   - Hold your smartphone at chest or eye level.
   - Pivot the camera around its own vertical axis. Do **not** pace in a circle around the room.

2. **Maintain 25%–40% Overlap**:
   - Each consecutive photograph must share roughly one-third of its view with the previous photo.
   - This provides the SIFT and ORB feature detectors with sufficient visual anchor points.

3. **Lock Exposure and White Balance**:
   - Tap and hold your smartphone screen to lock AE/AF (Auto Exposure / Auto Focus).
   - This prevents abrupt exposure jumps between adjacent frames.

4. **Capture Order**:
   - Rotate steadily in one direction (e.g. left to right).
   - Capture 8 to 12 overlapping images for a wide or full panoramic sweep.

5. **Avoid Dynamic Objects**:
   - Ensure people, pets, and moving vehicles are not in the overlap boundary.

---

## 2. Using the Boring 360 Web Studio

1. **Open the Studio**:
   - Navigate to `http://localhost:3000` in your web browser.
   - Check the top right status badge to confirm "OpenCV Core Ready".

2. **Upload Your Sequence**:
   - Click **New Panorama** in the navigation header.
   - Drag and drop your 8–12 photos into the upload zone or click to browse.
   - Check the thumbnail sequence. Use the left/right arrow buttons to arrange them in sequential rotational order.

3. **Try the Demo Sequence (Instant)**:
   - Click **"Load Sample 8-Shot Dataset"** on the upload page or dashboard to instantly load our pre-tested interior sequence.

4. **Generate Panorama**:
   - Click **"GENERATE PANORAMA"**.
   - Watch real-time execution across the 8 computer vision stages: Validation $\rightarrow$ Preprocessing $\rightarrow$ Feature Detection $\rightarrow$ Feature Matching $\rightarrow$ Camera Alignment $\rightarrow$ Warping $\rightarrow$ Seam Blending $\rightarrow$ Panorama Generation.

5. **Explore in 360°**:
   - Drag with your mouse or finger to look around.
   - Use the scroll wheel or toolbar buttons to zoom in and out.
   - Toggle smooth auto-rotation or go fullscreen.
   - Switch between **Interactive 360°** and **2D Flat Composite**.
   - Click **"Download JPEG"** to save the composite image locally.
