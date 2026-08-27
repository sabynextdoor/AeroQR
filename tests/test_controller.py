"""Unit tests for the drone controller."""

from __future__ import annotations

from aeroqr.controller import DroneController


class TestDroneController:
    def test_guards_commands_when_disabled(self, monkeypatch):
        drone = DroneController()
        sent = []

        def fake_send(command):
            sent.append(command)

        monkeypatch.setattr(drone, "send_command", fake_send)
        drone.control_enabled = False
        drone.navigate_to_qr((100, 100), (320, 240), None)
        assert sent == []

    def test_rotation_takes_priority(self, monkeypatch):
        drone = DroneController()
        drone.control_enabled = True
        sent = []
        monkeypatch.setattr(drone, "send_command", lambda c: sent.append(c))
        orientation = {"is_angle_ok": False, "angle_diff": 20}
        drone.navigate_to_qr((330, 240), (320, 240), orientation)
        assert sent and sent[0].startswith("ROTATE_RIGHT")

    def test_hovers_when_aligned(self, monkeypatch):
        drone = DroneController()
        drone.control_enabled = True
        drone.search_mode = False
        sent = []
        monkeypatch.setattr(drone, "send_command", lambda c: sent.append(c))
        drone.navigate_to_qr((320, 240), (320, 240), {"is_angle_ok": True})
        assert sent == ["HOVER"]

    def test_connect_returns_flag(self):
        drone = DroneController()
        assert isinstance(drone.connect(), bool)
