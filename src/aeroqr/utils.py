"""Drawing helpers, geometry utilities and the seed-image file dialog."""

from __future__ import annotations

import math

import cv2
import numpy as np


def order_points(pts: np.ndarray) -> np.ndarray:
    """Order four points as top-left, top-right, bottom-right, bottom-left.

    Uses the classic min/max sum and difference heuristic that works reliably
    for near-axis-aligned quadrilaterals such as detected QR codes.
    """
    pts = pts.astype(np.float32)
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1).ravel()
    return np.array(
        [
            pts[np.argmin(s)],  # top-left
            pts[np.argmin(diff)],  # top-right
            pts[np.argmax(s)],  # bottom-right
            pts[np.argmax(diff)],  # bottom-left
        ],
        dtype=np.float32,
    )


def is_valid_qr(pts: np.ndarray, frame_w: int, frame_h: int) -> bool:
    """Sanity-check a detection's geometry (size, ratio and frame bounds).

    Rejects detections that are too small, too large or excessively skewed to
    filter out spurious finds.
    """
    pts = np.asarray(pts, dtype=np.float32).copy()
    pts[:, 0] = np.clip(pts[:, 0], 0, frame_w - 1)
    pts[:, 1] = np.clip(pts[:, 1], 0, frame_h - 1)
    sides = [np.linalg.norm(pts[(i + 1) % 4] - pts[i]) for i in range(4)]
    mn, mx = min(sides), max(sides)

    if mn < 15 or mx > 1000:
        return False
    if mx / (mn + 1e-5) > 5.0:
        return False

    return True


def draw_rotation_arrow(
    frame: np.ndarray,
    center: tuple[int, int],
    direction: str | None,
    angle_diff: float,
) -> None:
    """Overlay an animated rotation arrow and angle instruction."""
    cx, cy = center
    radius = 70
    arrow_color = (0, 165, 255)

    if direction == "clockwise":
        cv2.ellipse(frame, (cx, cy), (radius, radius), 0, 0, 270, arrow_color, 3)
        end_angle = math.radians(270)
        tip_x = int(cx + radius * math.cos(end_angle))
        tip_y = int(cy + radius * math.sin(end_angle))
        cv2.arrowedLine(frame, (tip_x, tip_y), (tip_x - 20, tip_y - 20), arrow_color, 3, cv2.LINE_AA)
        text = f"ROTATE RIGHT {abs(angle_diff):.0f}°"
    else:
        cv2.ellipse(frame, (cx, cy), (radius, radius), 0, 270, 360, arrow_color, 3)
        end_angle = math.radians(270)
        tip_x = int(cx + radius * math.cos(end_angle))
        tip_y = int(cy + radius * math.sin(end_angle))
        cv2.arrowedLine(frame, (tip_x, tip_y), (tip_x + 20, tip_y - 20), arrow_color, 3, cv2.LINE_AA)
        text = f"ROTATE LEFT {abs(angle_diff):.0f}°"

    cv2.putText(
        frame, text, (cx - 70, cy - 60),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, arrow_color, 2,
    )


def draw_overlay(
    frame: np.ndarray,
    pts: np.ndarray,
    last_data: str,
    match_info: dict | None = None,
    orientation_info: dict | None = None,
) -> None:
    """Render the full detection overlay on a frame.

    Colors:
    * green  — matched with correct orientation
    * orange — matched but rotation required
    * red    — QR present but wrong seed
    * grey   — predicted position (QR temporarily lost)
    """
    p = pts.astype(np.int32)
    frame_h, frame_w = frame.shape[:2]

    if match_info and match_info.get("is_match", False):
        if orientation_info and not orientation_info.get("is_angle_ok", True):
            border_color = (0, 165, 255)
            fill_color = (0, 100, 150)
            marker_color = (0, 165, 255)
        else:
            border_color = (0, 255, 0)
            fill_color = (0, 150, 0)
            marker_color = (0, 255, 0)
    elif last_data:
        border_color = (0, 0, 255)
        fill_color = (0, 0, 150)
        marker_color = (0, 0, 255)
    else:
        border_color = (100, 100, 100)
        fill_color = (100, 100, 100)
        marker_color = (100, 100, 100)

    overlay = frame.copy()
    cv2.fillPoly(overlay, [p], fill_color)
    cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)

    for i in range(4):
        cv2.line(frame, tuple(p[i]), tuple(p[(i + 1) % 4]), border_color, 2, cv2.LINE_AA)

    dirs = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    for i, (sx, sy) in enumerate(dirs):
        x, y = int(p[i][0]), int(p[i][1])
        length = 20
        cv2.line(frame, (x, y), (x + sx * length, y), (255, 255, 255), 2, cv2.LINE_AA)
        cv2.line(frame, (x, y), (x, y + sy * length), (255, 255, 255), 2, cv2.LINE_AA)
        cv2.circle(frame, (x, y), 5, marker_color, -1, cv2.LINE_AA)
        cv2.circle(frame, (x, y), 8, (255, 255, 255), 1, cv2.LINE_AA)

    cx = int(np.mean(p[:, 0]))
    cy = int(np.mean(p[:, 1]))
    cv2.drawMarker(frame, (cx, cy), marker_color, cv2.MARKER_CROSS, 30, 2, cv2.LINE_AA)
    cv2.circle(frame, (cx, cy), 15, marker_color, 1, cv2.LINE_AA)
    cv2.circle(frame, (cx, cy), 3, marker_color, -1, cv2.LINE_AA)

    if orientation_info and not orientation_info.get("is_angle_ok", True):
        draw_rotation_arrow(
            frame,
            (cx, cy),
            orientation_info.get("rotation_direction", "clockwise"),
            orientation_info.get("rotation_amount", 0),
        )

    if last_data:
        if match_info and match_info.get("is_match", False):
            if orientation_info and not orientation_info.get("is_angle_ok", True):
                label = (
                    "⚠ ROTATE "
                    f"{orientation_info.get('rotation_direction', '').upper()} "
                    f"{orientation_info.get('rotation_amount', 0):.0f}° ⚠"
                )
                label_color = (0, 165, 255)
            else:
                label = f"✓ MATCHED: {last_data[:20]}"
                label_color = (0, 255, 0)
        else:
            label = f"QR: {last_data[:25]}"
            label_color = (0, 0, 255)

        tx = max(min(p[0][0], frame_w - 350), 6)
        ty = max(p[0][1] - 14, 65)
        (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 2)
        cv2.rectangle(frame, (tx - 5, ty - text_h - 6), (tx + text_w + 5, ty + 5), (0, 0, 0), -1)
        cv2.rectangle(frame, (tx - 5, ty - text_h - 6), (tx + text_w + 5, ty + 5), label_color, 1)
        cv2.putText(frame, label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.45, label_color, 2, cv2.LINE_AA)


def load_seed_image_dialog() -> str | None:
    """Open a native file dialog and return the selected image path."""
    from tkinter import Tk, filedialog

    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    file_path = filedialog.askopenfilename(
        title="Select Seed QR Image",
        filetypes=[
            ("Image files", "*.jpg *.jpeg *.png *.bmp"),
            ("All files", "*.*"),
        ],
    )

    root.destroy()
    return file_path if file_path else None
