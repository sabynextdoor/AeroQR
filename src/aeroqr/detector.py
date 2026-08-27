"""Background QR detector running six multi-scale processing strategies."""

from __future__ import annotations

import threading
import time

import cv2
import numpy as np

from aeroqr import config
from aeroqr.matcher import SeedMatcher


class QRWorker:
    """Detects QR codes in a dedicated background thread.

    The worker continuously scans the latest submitted frame through six
    scale levels and three pre-processing pipelines, keeping the main loop
    free for rendering and control.

    Attributes:
        frame: The latest frame submitted for processing (or ``None``).
    """

    def __init__(self, seed_matcher: SeedMatcher | None = None) -> None:
        self.detector = cv2.QRCodeDetector()
        self.seed_matcher = seed_matcher
        self._lock = threading.Lock()
        self._frame: np.ndarray | None = None
        self._result: tuple = (None, None, None, None)
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()

    def _try_detect(
        self, img: np.ndarray, scale: float = 1.0
    ) -> tuple[str | None, np.ndarray | None]:
        """Attempt detection, compensating point coordinates for scaling."""
        try:
            if scale != 1.0:
                height, width = img.shape[:2]
                scaled_img = cv2.resize(img, (int(width * scale), int(height * scale)))
                data, pts, _ = self.detector.detectAndDecode(scaled_img)
                if pts is not None and len(pts) > 0 and pts[0].shape[0] == 4:
                    return data or "", pts[0] / scale
            else:
                data, pts, _ = self.detector.detectAndDecode(img)
                if pts is not None and len(pts) > 0 and pts[0].shape[0] == 4:
                    return data or "", pts[0]
        except Exception:
            pass
        return None, None

    def _run(self) -> None:
        """Processing loop: gray → CLAHE → sharpen, across all scales → Otsu."""
        clahe = cv2.createCLAHE(
            clipLimit=config.CLAHE_CLIP_LIMIT, tileGridSize=config.CLAHE_TILE_GRID
        )
        sharpen_kernel = config.SHARPEN_KERNEL

        while self.running:
            with self._lock:
                frame = self._frame
            if frame is None:
                time.sleep(0.001)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            enhanced = clahe.apply(gray)
            sharpened = cv2.filter2D(gray, -1, sharpen_kernel)

            result: tuple = (None, None)
            match_info: dict | None = None
            orientation_info: dict | None = None

            for scale in config.DETECTION_SCALES:
                if result[1] is not None:
                    break

                for image in (gray, enhanced, sharpened):
                    data, pts = self._try_detect(image, scale)
                    if pts is not None:
                        result = (data, pts)
                        break

            if result[1] is None:
                _, thresh = cv2.threshold(
                    gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )
                data, pts = self._try_detect(thresh, config.OTSU_SCALE)
                if pts is not None:
                    result = (data, pts)

            if result[1] is not None and self.seed_matcher and result[0]:
                is_match, similarity = self.seed_matcher.compare_with_seed(result[0])
                if is_match:
                    match_info = {"is_match": True, "similarity": similarity}
                    orientation_info = self.seed_matcher.analyze_orientation(result[1])
                else:
                    match_info = {"is_match": False, "similarity": similarity}

            with self._lock:
                self._result = (result[0], result[1], match_info, orientation_info)
                self._frame = None

    def submit(self, frame: np.ndarray) -> None:
        """Queue a new frame for processing (dropped if the worker is busy)."""
        with self._lock:
            if self._frame is None:
                self._frame = frame

    def get(self) -> tuple:
        """Return ``(data, points, match_info, orientation_info)`` from the worker."""
        with self._lock:
            return self._result

    def stop(self) -> None:
        """Stop the background processing thread."""
        self.running = False
