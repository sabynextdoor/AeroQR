"""Centralised configuration and tunable constants for the AeroQR system.

All detection, matching, tracking, camera and drone parameters live here so
that tuning the pipeline never requires touching the processing code.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "VERSION",
    "PROJECT_NAME",
    "DETECTION_SCALES",
    "CLAHE_CLIP_LIMIT",
    "CLAHE_TILE_GRID",
    "SHARPEN_KERNEL",
    "OTSU_SCALE",
    "MATCHING_THRESHOLD",
    "CALIBRATION_SAMPLES",
    "MAX_CALIBRATION_SAMPLES",
    "ANGLE_TOLERANCE",
    "ANGLE_MESSAGE_COOLDOWN",
    "SMOOTH_FACTOR",
    "LOSE_AFTER",
    "DEFAULT_CAMERA_INDEX",
    "FRAME_WIDTH",
    "FRAME_HEIGHT",
    "FRAME_FPS",
    "CAPTURE_BUFFER_SIZE",
    "CAMERA_AUTOFOCUS",
    "CAMERA_FOURCC",
    "DEFAULT_DRONE_IP",
    "DEFAULT_DRONE_PORT",
    "COMMAND_COOLDOWN",
    "WINDOW_TITLE",
]

VERSION = "1.0.0"
PROJECT_NAME = "AeroQR"

# ── Detection ──────────────────────────────────────────────────────
DETECTION_SCALES = (2.0, 1.5, 1.2, 1.0, 0.8, 0.6)
CLAHE_CLIP_LIMIT = 3.0
CLAHE_TILE_GRID = (8, 8)
SHARPEN_KERNEL = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
OTSU_SCALE = 1.0

# ── Seed matching ──────────────────────────────────────────────────
MATCHING_THRESHOLD = 85  # percentage similarity required for a positive match
CALIBRATION_SAMPLES = 5  # detections required to lock the reference angle
MAX_CALIBRATION_SAMPLES = 10
ANGLE_TOLERANCE = 10  # degrees of acceptable orientation error
ANGLE_MESSAGE_COOLDOWN = 1.5  # seconds between repeated terminal hints

# ── Tracking ───────────────────────────────────────────────────────
SMOOTH_FACTOR = 0.7
LOSE_AFTER = 30  # frames before a lost QR is considered gone

# ── Camera ─────────────────────────────────────────────────────────
DEFAULT_CAMERA_INDEX = 1  # 0 = laptop camera, 1 = external USB webcam
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FRAME_FPS = 30
CAPTURE_BUFFER_SIZE = 1
CAMERA_AUTOFOCUS = 1
CAMERA_FOURCC = "MJPG"

# ── Drone ──────────────────────────────────────────────────────────
DEFAULT_DRONE_IP = "192.168.1.100"
DEFAULT_DRONE_PORT = 8888
COMMAND_COOLDOWN = 0.3  # seconds between drone commands

# ── UI ─────────────────────────────────────────────────────────────
WINDOW_TITLE = "AeroQR — ISRO IROUC 2026 QR Drone Detector"
