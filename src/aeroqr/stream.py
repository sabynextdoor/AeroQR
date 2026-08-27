"""Threaded webcam capture with automatic camera discovery."""

from __future__ import annotations

import threading
import time
from collections import deque

import cv2
import numpy as np

from aeroqr import config


class WebcamStream:
    """High-throughput webcam capture running in its own thread.

    Frames are read continuously in a background thread so the main loop never
    blocks on camera I/O. The stream also reports a rolling FPS estimate.

    Attributes:
        cam_fps: Rolling estimate of the camera's frame rate.
    """

    def __init__(self, camera_index: int = config.DEFAULT_CAMERA_INDEX) -> None:
        self.camera_index = camera_index
        print(f"\n📷 Trying to open camera index {camera_index}...")

        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            print("   Camera not found with DirectShow, trying default backend...")
            self.cap = cv2.VideoCapture(camera_index)

        if not self.cap.isOpened():
            print(f"❌ Could not open camera {camera_index}")
            print("   Available cameras:")
            for i in range(5):
                test_cap = cv2.VideoCapture(i)
                if test_cap.isOpened():
                    print(f"   - Camera index {i} is available")
                    test_cap.release()
            raise RuntimeError(f"No camera found at index {camera_index}")

        # Optimal capture properties for low latency
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, config.FRAME_FPS)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, config.CAPTURE_BUFFER_SIZE)
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, config.CAMERA_AUTOFOCUS)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*config.CAMERA_FOURCC))  # type: ignore[arg-type]

        self._lock = threading.Lock()
        self.running = True
        self.cam_fps = 0.0
        self._ftimes: deque = deque(maxlen=30)
        self._ret, self._frame = self.cap.read()

        threading.Thread(target=self._update, daemon=True).start()
        print(f"✅ Webcam {camera_index} initialized successfully!")

    def _update(self) -> None:
        """Continuously read frames and update the FPS estimate."""
        while self.running:
            timestamp = time.time()
            ret, frame = self.cap.read()
            with self._lock:
                self._ret, self._frame = ret, frame
                self._ftimes.append(timestamp)
                if len(self._ftimes) >= 2:
                    self.cam_fps = (len(self._ftimes) - 1) / (
                        self._ftimes[-1] - self._ftimes[0] + 1e-6
                    )

    def read(self) -> tuple[bool, np.ndarray | None, float]:
        """Return ``(success, frame, fps)``; the frame is a defensive copy."""
        with self._lock:
            if not self._ret or self._frame is None:
                return False, None, 0.0
            return True, self._frame.copy(), self.cam_fps

    def stop(self) -> None:
        """Stop the capture thread and release the camera."""
        self.running = False
        self.cap.release()
