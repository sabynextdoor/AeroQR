"""Unit tests for geometry helpers and validation."""

from __future__ import annotations

import numpy as np

from aeroqr.utils import is_valid_qr, order_points


def _square(x0, y0, side):
    return np.array(
        [[x0, y0], [x0 + side, y0], [x0 + side, y0 + side], [x0, y0 + side]],
        dtype=np.float32,
    )


class TestOrderPoints:
    def test_orders_clockwise(self):
        # Give points in a scrambled order: BR, TL, BL, TR
        scrambled = np.array(
            [[110, 110], [10, 10], [10, 110], [110, 10]], dtype=np.float32
        )
        ordered = order_points(scrambled)
        expected = np.array([[10, 10], [110, 10], [110, 110], [10, 110]], dtype=np.float32)
        np.testing.assert_allclose(ordered, expected)


class TestIsValidQr:
    def test_accepts_normal_qr(self):
        assert is_valid_qr(_square(100, 100, 100), 640, 480) is True

    def test_rejects_tiny_qr(self):
        assert is_valid_qr(_square(0, 0, 10), 640, 480) is False

    def test_rejects_oversized_qr(self):
        assert is_valid_qr(_square(0, 0, 1500), 2000, 2000) is False

    def test_clips_out_of_bounds_to_valid(self):
        assert is_valid_qr(_square(0, 0, 2000), 640, 480) is True

    def test_rejects_skewed_qr(self):
        skewed = np.array([[0, 0], [500, 0], [500, 40], [0, 40]], dtype=np.float32)
        assert is_valid_qr(skewed, 640, 480) is False
