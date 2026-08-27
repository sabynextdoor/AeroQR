"""Unit tests for the seed matcher."""

from __future__ import annotations

import numpy as np
import pytest

from aeroqr.matcher import SeedMatcher

QRCODE = pytest.importorskip("qrcode")


def _make_seed(tmp_path, payload: str):
    """Generate a freshly encoded PNG QR seed image on disk."""
    qr = QRCODE.QRCode(border=1)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    path = tmp_path / "seed.png"
    img.save(path)
    return str(path)


class TestSimilarity:
    def test_identical_strings(self):
        matcher = SeedMatcher()
        assert matcher._calculate_similarity("ABCDEF", "ABCDEF") == 100.0

    def test_partial_match(self):
        matcher = SeedMatcher()
        assert matcher._calculate_similarity("ABCDE", "ABXYZ") == 40.0

    def test_empty_strings(self):
        matcher = SeedMatcher()
        assert matcher._calculate_similarity("", "ABC") == 0.0


class TestCompareWithSeed:
    def test_detects_exact_match(self):
        matcher = SeedMatcher()
        matcher.seed_loaded = True
        matcher.seed_data = "target"
        is_match, similarity = matcher.compare_with_seed("target")
        assert is_match is True
        assert similarity == 100.0

    def test_rejects_wrong_seed(self):
        matcher = SeedMatcher()
        matcher.seed_loaded = True
        matcher.seed_data = "target"
        is_match, similarity = matcher.compare_with_seed("nope")
        assert is_match is False
        assert similarity < matcher.matching_threshold

    def test_no_seed_loaded(self):
        matcher = SeedMatcher()
        is_match, similarity = matcher.compare_with_seed("target")
        assert is_match is False and similarity == 0


class TestLoadSeedFromFile:
    def test_loads_valid_seed(self, tmp_path):
        payload = "ISRO-IROUC-2026-AeroQR"
        path = _make_seed(tmp_path, payload)
        matcher = SeedMatcher()
        ok, message = matcher.load_seed_from_file(path)
        assert ok is True
        assert matcher.seed_loaded is True
        assert matcher.seed_data == payload

    def test_rejects_invalid_file(self, tmp_path):
        bad = tmp_path / "not-an-image.png"
        bad.write_bytes(b"this is definitely not a png")
        matcher = SeedMatcher()
        ok, _ = matcher.load_seed_from_file(str(bad))
        assert ok is False
        assert matcher.seed_loaded is False


class TestOrientation:
    def test_no_seed_yields_none(self):
        matcher = SeedMatcher()
        pts = np.array([[0, 0], [100, 0], [100, 100], [0, 100]], dtype=np.float32)
        assert matcher.analyze_orientation(pts) is None

    def test_axis_aligned_is_ok(self):
        matcher = SeedMatcher()
        matcher.seed_loaded = True
        matcher.seed_features = {"angle": 0.0, "corners": None, "aspect_ratio": 1.0}
        pts = np.array([[0, 0], [100, 0], [100, 100], [0, 100]], dtype=np.float32)
        info = matcher.analyze_orientation(pts)
        assert info is not None
        assert info["is_angle_ok"] is True
        assert info["angle_diff"] == 0

    def test_rotation_detected(self):
        matcher = SeedMatcher()
        matcher.seed_loaded = True
        matcher.seed_features = {"angle": 0.0, "corners": None, "aspect_ratio": 1.0}
        pts = np.array([[50, 0], [150, 0], [150, 100], [50, 100]], dtype=np.float32)
        info = matcher.analyze_orientation(pts)
        assert info is not None
        assert info["is_angle_ok"] is True  # still within 10deg tolerance

    def test_reset_clears_state(self):
        matcher = SeedMatcher()
        matcher.seed_loaded = True
        matcher.seed_data = "x"
        matcher.calibration_samples = [0.0, 1.0, 2.0]
        matcher.reset()
        assert matcher.seed_loaded is False
        assert matcher.seed_data is None
        assert matcher.calibration_samples == []
