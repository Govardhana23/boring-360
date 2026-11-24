import cv2
import numpy as np
from pathlib import Path

SAMPLE_DIR = Path(__file__).resolve().parent
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)


def create_synthetic_room_panorama_sequence(num_shots: int = 8, shot_w: int = 800, shot_h: int = 600):
    """
    Creates a continuous rich cylindrical scene with architectural features,
    posters, furniture textures, lamps, brickwork, and distinct geometric patterns,
    then captures 8 overlapping perspective/cylindrical camera frames with ~35% overlap.
    """
    # Create continuous wide scene:
    # 8 shots with 35% overlap means total scene width is approx (1 + 0.65*(8-1)) * shot_w = 5.55 * shot_w
    step_x = int(shot_w * 0.65)
    total_w = shot_w + (num_shots - 1) * step_x + 200
    total_h = shot_h

    # Create scene canvas with realistic wall gradient
    scene = np.zeros((total_h, total_w, 3), dtype=np.uint8)
    for y in range(total_h):
        # subtle vertical lighting gradient
        val = int(210 - 45 * (y / float(total_h)))
        scene[y, :] = (val - 15, val, val + 10)  # warm interior wall

    # Draw wooden floor at the bottom
    floor_y = int(total_h * 0.75)
    scene[floor_y:, :] = (40, 70, 120)  # wood tone
    for x in range(0, total_w, 40):
        cv2.line(scene, (x, floor_y), (x + 30, total_h), (25, 45, 80), 2)
    cv2.line(scene, (0, floor_y), (total_w, floor_y), (15, 30, 60), 4)

    # Ceiling crown molding
    ceiling_y = int(total_h * 0.12)
    cv2.line(scene, (0, ceiling_y), (total_w, ceiling_y), (180, 190, 200), 3)

    # Add diverse objects across the continuous scene so SIFT/ORB find rich anchor points
    np.random.seed(42)

    # Architectural columns
    for x_col in range(150, total_w, 450):
        cv2.rectangle(scene, (x_col, ceiling_y), (x_col + 45, floor_y), (160, 170, 180), -1)
        cv2.rectangle(scene, (x_col - 5, ceiling_y - 10), (x_col + 50, ceiling_y), (130, 140, 150), -1)
        cv2.rectangle(scene, (x_col - 5, floor_y), (x_col + 50, floor_y + 15), (130, 140, 150), -1)

    # Framed paintings & posters
    for idx, x_frame in enumerate(range(260, total_w - 300, 380)):
        y_top = int(total_h * 0.22) + (idx % 2) * 20
        frame_w = 160
        frame_h = 130
        # Frame border
        cv2.rectangle(scene, (x_frame, y_top), (x_frame + frame_w, y_top + frame_h), (20, 30, 50), -1)
        cv2.rectangle(scene, (x_frame + 8, y_top + 8), (x_frame + frame_w - 8, y_top + frame_h - 8), (220, 230, 240), -1)

        # Drawing inside frame (geometric art)
        center_x = x_frame + frame_w // 2
        center_y = y_top + frame_h // 2
        color1 = ((idx * 60) % 200 + 30, (idx * 90) % 200 + 30, (idx * 130) % 200 + 30)
        color2 = (220 - color1[0], 220 - color1[1], 220 - color1[2])
        cv2.circle(scene, (center_x, center_y), 35, color1, -1)
        cv2.rectangle(scene, (center_x - 20, center_y - 20), (center_x + 20, center_y + 20), color2, 3)
        cv2.putText(scene, f"ART #{idx+1}", (x_frame + 16, y_top + frame_h - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (10, 10, 10), 1)

    # Wall lamps
    for x_lamp in range(100, total_w - 150, 400):
        y_lamp = int(total_h * 0.35)
        cv2.circle(scene, (x_lamp, y_lamp), 18, (80, 220, 255), -1)  # glowing warm bulb
        cv2.circle(scene, (x_lamp, y_lamp), 26, (120, 235, 255), 2)  # glow ring
        cv2.rectangle(scene, (x_lamp - 6, y_lamp + 18), (x_lamp + 6, y_lamp + 40), (40, 40, 45), -1)

    # Windows overlooking outdoors
    for x_win in range(480, total_w - 400, 750):
        y_win = int(total_h * 0.18)
        win_w = 210
        win_h = 240
        # Window frame
        cv2.rectangle(scene, (x_win, y_win), (x_win + win_w, y_win + win_h), (50, 60, 70), -1)
        # Sky & landscape inside window
        cv2.rectangle(scene, (x_win + 10, y_win + 10), (x_win + win_w - 10, y_win + win_h - 10), (240, 180, 120), -1) # blue sky
        # Mountains
        pts_mountain = np.array([
            [x_win + 10, y_win + win_h - 10],
            [x_win + 60, y_win + win_h - 80],
            [x_win + 120, y_win + win_h - 40],
            [x_win + 170, y_win + win_h - 100],
            [x_win + win_w - 10, y_win + win_h - 10]
        ], np.int32)
        cv2.fillPoly(scene, [pts_mountain], (60, 120, 50))
        # Window cross panes
        mid_x = x_win + win_w // 2
        mid_y = y_win + win_h // 2
        cv2.line(scene, (mid_x, y_win), (mid_x, y_win + win_h), (40, 50, 60), 4)
        cv2.line(scene, (x_win, mid_y), (x_win + win_w, mid_y), (40, 50, 60), 4)

    # Add natural fine high-frequency noise/texture so detectors find hundreds of natural keypoints
    noise = np.random.normal(0, 5, scene.shape).astype(np.int16)
    scene_textured = np.clip(scene.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Extract the 8 overlapping crops simulating rotating smartphone camera
    created_paths = []
    for shot_idx in range(num_shots):
        start_x = shot_idx * step_x
        crop = scene_textured[0:shot_h, start_x:start_x + shot_w].copy()

        # Add slight natural handheld smartphone camera variation:
        # 1. Subtle camera rotation (tilt by -0.8 to +0.8 degree)
        angle = np.sin(shot_idx * 0.9) * 0.6
        M_rot = cv2.getRotationMatrix2D((shot_w / 2, shot_h / 2), angle, 1.0)
        # 2. Subtle vertical hand jitter (-4 to +4 px)
        dy = int(np.cos(shot_idx * 1.2) * 5)
        M_rot[1, 2] += dy

        frame = cv2.warpAffine(crop, M_rot, (shot_w, shot_h), borderMode=cv2.BORDER_REFLECT)

        out_path = SAMPLE_DIR / f"smartphone_shot_{shot_idx + 1:02d}.jpg"
        cv2.imwrite(str(out_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 94])
        created_paths.append(out_path)
        print(f"Generated sample photo {shot_idx + 1}/{num_shots}: {out_path.name} ({shot_w}x{shot_h})")

    return created_paths


if __name__ == "__main__":
    create_synthetic_room_panorama_sequence()
