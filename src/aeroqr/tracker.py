"""Lightweight point tracking with exponential smoothing (Kalman-style)."""

from __future__ import annotations

import numpy as np


class SimpleTracker:
    """Smooths QR corner coordinates to keep the overlay stable when the
    detector jitters between frames.

    Implements a first-order exponential moving average over the four
    detected corners. If the QR is briefly lost it keeps returning the last
    known estimate so the overlay does not flicker.
    """

    def __init__(self, smooth_factor: float = 0.7) -> None:
        self.smooth_factor = smooth_factor
        self.last_pts: np.ndarray | None = None
        self.has_track = False

    def update(self, pts: np.ndarray) -> np.ndarray | None:
        """Smooth a new set of points and return the updated estimate."""
        if pts is None:
            return None

        pts = pts.astype(np.float32)

        if not self.has_track:
            self.last_pts = pts
            self.has_track = True
            return pts

        smoothed = self.smooth_factor * pts + (1 - self.smooth_factor) * self.last_pts
        self.last_pts = smoothed
        return smoothed

    def reset(self) -> None:
        """Forget the previous track."""
        self.last_pts = None
        self.has_track = False
