"""Seed image matching, auto-calibration and QR orientation analysis."""

from __future__ import annotations

import math
import time

import cv2
import numpy as np

from aeroqr import config


class SeedMatcher:
    """Matches live detections against a reference (seed) QR image.

    Once a seed image is loaded, the matcher:
    * decodes the seed's payload for exact/partial string matching,
    * extracts the seed's geometric features (angle, corners, aspect ratio),
    * auto-calibrates the reference orientation from live detections, and
    * compares every new detection against the locked orientation.
    """

    def __init__(self) -> None:
        self.seed_image: np.ndarray | None = None
        self.seed_data: str | None = None
        self.seed_loaded = False
        self.seed_features: dict | None = None
        self.matching_threshold: float = config.MATCHING_THRESHOLD
        self.calibration_samples: list[float] = []
        self.is_calibrated = False
        self.calibrated_angle: float | None = None
        self.last_angle_message_time = 0.0
        self.message_cooldown: float = config.ANGLE_MESSAGE_COOLDOWN

    # ── Loading ────────────────────────────────────────────────────
    def load_seed_from_file(self, filepath: str) -> tuple[bool, str]:
        """Load and decode a seed QR image from disk.

        Returns:
            ``(True, message)`` on success, ``(False, message)`` on failure.
        """
        try:
            img = cv2.imread(filepath)
            if img is None:
                return False, "Could not read image file"

            img = cv2.resize(img, (400, 400))

            self.seed_image = img.copy()
            detector = cv2.QRCodeDetector()
            data, pts, _ = detector.detectAndDecode(img)

            if data and len(data) > 0:
                self.seed_data = data
                self.seed_loaded = True
                self._extract_seed_features(img, pts)
                return True, f"Loaded: {data[:50]}..."
            else:
                return False, "No QR code found in seed image"
        except Exception as exc:
            return False, f"Error: {str(exc)}"

    def _extract_seed_features(self, img: np.ndarray, qr_pts) -> None:
        if qr_pts is None or len(qr_pts) == 0:
            self.seed_features = None
            return

        corners = qr_pts[0].astype(np.float32)
        top_edge = corners[1] - corners[0]
        angle = math.degrees(math.atan2(top_edge[1], top_edge[0]))

        self.seed_features = {
            "angle": angle,
            "corners": corners,
            "aspect_ratio": self._calculate_aspect_ratio(corners),
        }

    @staticmethod
    def _calculate_aspect_ratio(corners: np.ndarray) -> float:
        top_edge = np.linalg.norm(corners[1] - corners[0])
        left_edge = np.linalg.norm(corners[3] - corners[0])
        return top_edge / left_edge if left_edge > 0 else 1.0

    # ── Auto-calibration ───────────────────────────────────────────
    def auto_calibrate(self, qr_corners: np.ndarray) -> bool:
        """Accumulate orientation samples and lock the reference angle.

        The reference angle is locked once ``CALIBRATION_SAMPLES`` detections
        have been collected. Send the full angle stability by using a median.
        """
        if qr_corners is None:
            return False

        corners = qr_corners.astype(np.float32)
        top_edge = corners[1] - corners[0]
        current_angle = math.degrees(math.atan2(top_edge[1], top_edge[0]))

        self.calibration_samples.append(current_angle)

        if len(self.calibration_samples) > config.MAX_CALIBRATION_SAMPLES:
            self.calibration_samples.pop(0)

        if (
            len(self.calibration_samples) >= config.CALIBRATION_SAMPLES
            and not self.is_calibrated
        ):
            self.calibrated_angle = np.median(self.calibration_samples)
            if self.seed_features:
                self.seed_features["angle"] = self.calibrated_angle
            self.is_calibrated = True
            print("\n✅ AUTO-CALIBRATION COMPLETE!")
            print(f"   Reference angle: {self.calibrated_angle:.1f}°\n")
            return True

        return False

    # ── Matching ───────────────────────────────────────────────────
    def compare_with_seed(self, qr_data: str) -> tuple[bool, float]:
        """Compare a decoded QR payload against the seed payload."""
        if not self.seed_loaded or not qr_data:
            return False, 0

        if qr_data == self.seed_data:
            return True, 100.0

        similarity = self._calculate_similarity(qr_data, self.seed_data)
        return similarity >= self.matching_threshold, similarity

    @staticmethod
    def _calculate_similarity(str1: str, str2: str) -> float:
        """Character-level similarity score in the range ``0..100``."""
        if not str1 or not str2:
            return 0

        max_len = max(len(str1), len(str2))
        if max_len == 0:
            return 100

        matches = sum(
            1 for i in range(min(len(str1), len(str2))) if str1[i] == str2[i]
        )
        return (matches / max_len) * 100

    # ── Orientation analysis ───────────────────────────────────────
    def analyze_orientation(self, qr_corners: np.ndarray) -> dict | None:
        """Compute the angular error between a detection and the seed.

        Returns a dictionary with ``current_angle``, ``target_angle``,
        ``angle_diff``, ``rotation_direction``, ``rotation_amount`` and
        ``is_angle_ok``, or ``None`` when orientation cannot be evaluated.
        """
        if not self.seed_loaded or qr_corners is None or self.seed_features is None:
            return None

        try:
            corners = qr_corners.astype(np.float32)
            top_edge = corners[1] - corners[0]
            current_angle = math.degrees(math.atan2(top_edge[1], top_edge[0]))

            angle_diff = (current_angle - self.seed_features["angle"] + 180) % 360 - 180
            is_angle_ok = abs(angle_diff) <= config.ANGLE_TOLERANCE

            rotation_direction = None
            rotation_amount = abs(angle_diff)

            if not is_angle_ok:
                rotation_direction = "clockwise" if angle_diff > 0 else "counter-clockwise"

                current_time = time.time()
                if current_time - self.last_angle_message_time >= self.message_cooldown:
                    self.last_angle_message_time = current_time
                    if angle_diff > 0:
                        instruction = "▶  Rotate QR CLOCKWISE"
                        command = "ROTATE_RIGHT"
                    else:
                        instruction = "◀  Rotate QR COUNTER-CLOCKWISE"
                        command = "ROTATE_LEFT"
                    amount = min(max(abs(angle_diff) // 5, 5), 30)
                    print("\n" + "=" * 50)
                    print("⚠️  ROTATION INSTRUCTION ⚠️")
                    print("=" * 50)
                    print(f"  Current QR angle: {current_angle:.1f}°")
                    print(f"  Target angle:     {self.seed_features['angle']:.1f}°")
                    print(f"  Difference:       {abs(angle_diff):.1f}°")
                    print(f"  {instruction} by {abs(angle_diff):.0f}°")
                    print(f"  ▶  Drone command: {command} {amount}°")
                    print("=" * 50 + "\n")

            return {
                "current_angle": current_angle,
                "target_angle": self.seed_features["angle"],
                "angle_diff": angle_diff,
                "rotation_direction": rotation_direction,
                "rotation_amount": rotation_amount,
                "is_angle_ok": is_angle_ok,
            }
        except Exception:
            return None

    def reset(self) -> None:
        """Clear the seed, calibration state and cached features."""
        self.seed_image = None
        self.seed_data = None
        self.seed_loaded = False
        self.seed_features = None
        self.calibration_samples = []
        self.is_calibrated = False
        self.calibrated_angle = None
