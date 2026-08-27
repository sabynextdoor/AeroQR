"""Drone control over a lightweight UDP command channel."""

from __future__ import annotations

import socket
import time
from typing import Union

from aeroqr import config

Point = Union[tuple[float, float], tuple[int, int]]


class DroneController:
    """Sends coarse navigation commands to a drone over UDP.

    Commands follow a simple text protocol (``ROTATE_LEFT <deg>``,
    ``MOVE_RIGHT <units>``, ``HOVER``, ``LAND`` ...) and are throttled by a
    cooldown to avoid overloading the flight controller.

    Attributes:
        drone_ip: Destination IP address of the drone's command socket.
        port: Destination UDP port.
        control_enabled: Master switch for command transmission.
    """

    def __init__(
        self,
        drone_ip: str = config.DEFAULT_DRONE_IP,
        port: int = config.DEFAULT_DRONE_PORT,
    ) -> None:
        self.drone_ip = drone_ip
        self.port = port
        self.connected = False
        self.sock: socket.socket | None = None
        self.control_enabled = False
        self.search_mode = True
        self.last_command_time = 0.0
        self.command_cooldown = config.COMMAND_COOLDOWN

    def connect(self) -> bool:
        """Open a UDP socket to the drone already set as driven by attributes."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(1)
            self.connected = True
            print(f"✓ Drone connected to {self.drone_ip}:{self.port}")
            return True
        except Exception as exc:  # pragma: no cover - network dependent
            print(f"✗ Drone connection failed: {exc}")
            return False

    def send_command(self, command: str) -> None:
        """Send a command if connected, enabled and outside the cooldown window."""
        if not self.connected or not self.control_enabled:
            return

        current_time = time.time()
        if current_time - self.last_command_time >= self.command_cooldown:
            self.last_command_time = current_time
            try:
                assert self.sock is not None
                self.sock.sendto(command.encode(), (self.drone_ip, self.port))
                print(f"  🚁 Drone: {command}")
            except Exception as exc:  # pragma: no cover - network dependent
                print(f"Command failed: {exc}")

    def search_for_qr(self) -> None:
        """Issue a pan command so the drone sweeps for the QR code."""
        if self.search_mode:
            self.send_command("ROTATE_RIGHT 20")

    def navigate_to_qr(
        self,
        qr_center: Point,
        frame_center: Point,
        orientation_info: dict | None = None,
    ) -> None:
        """Steer the drone towards the QR, then fix its rotation.

        Priority order:
        1. Fix QR rotation when the orientation error exceeds tolerance.
        2. Centre the QR horizontally.
        3. Centre the QR vertically.
        4. Hover once fully aligned.
        """
        if not self.control_enabled:
            return

        error_x = qr_center[0] - frame_center[0]
        error_y = qr_center[1] - frame_center[1]

        # PRIORITY 1: FIX QR ROTATION
        if orientation_info and not orientation_info.get("is_angle_ok", True):
            angle_diff = orientation_info.get("angle_diff", 0)
            rotation_amount = min(max(abs(angle_diff) // 5, 5), 30)

            if abs(angle_diff) > 5:
                if angle_diff > 0:
                    self.send_command(f"ROTATE_RIGHT {rotation_amount}")
                else:
                    self.send_command(f"ROTATE_LEFT {rotation_amount}")
                return

        # PRIORITY 2: CENTER
        if abs(error_x) > 60:
            move = min(abs(error_x) // 20, 25)
            if error_x > 0:
                self.send_command(f"MOVE_RIGHT {move}")
            else:
                self.send_command(f"MOVE_LEFT {move}")
            return

        if abs(error_y) > 60:
            move = min(abs(error_y) // 20, 25)
            if error_y > 0:
                self.send_command(f"MOVE_DOWN {move}")
            else:
                self.send_command(f"MOVE_UP {move}")
            return

        if self.search_mode:
            self.search_mode = False
            print("  ✓ QR aligned! Hovering...")
        self.send_command("HOVER")

    def land(self) -> None:
        """Command the drone to land."""
        self.send_command("LAND")

    def disconnect(self) -> None:
        """Release the socket and reset connection state."""
        self.control_enabled = False
        if self.sock:
            self.sock.close()
        self.sock = None
        self.connected = False
