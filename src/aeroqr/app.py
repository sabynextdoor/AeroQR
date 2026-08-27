"""End-to-end application orchestration: camera → detect → match → track → control."""

from __future__ import annotations

import time
import warnings

import cv2
import numpy as np

from aeroqr import config
from aeroqr.controller import DroneController
from aeroqr.detector import QRWorker
from aeroqr.matcher import SeedMatcher
from aeroqr.stream import WebcamStream
from aeroqr.tracker import SimpleTracker
from aeroqr.utils import draw_overlay, is_valid_qr, load_seed_image_dialog, order_points

warnings.filterwarnings("ignore")

BANNER = "=" * 60 + """
  ISRO IROUC 2026 — QR Drone Detector
  ✓ External webcam support
  ✓ Long-range QR detection
  ✓ Auto-calibration
  ✓ Drone rotation commands
  ✓ Terminal rotation instructions
""" + "=" * 60

HELP_TEXT = "Q:Quit  L:Load  R:Reset  D:Drone"


def _select_camera_index() -> int:
    """Prompt for a camera index, defaulting to the configured webcam."""
    print("📷 Available camera indices:")
    print("   Index 0 - Built-in laptop camera")
    print("   Index 1 - External USB webcam")
    print("   Index 2 - Second external camera")

    choice = input(
        f"\nSelect camera index (default {config.DEFAULT_CAMERA_INDEX} for external webcam): "
    ).strip()
    return int(choice) if choice else config.DEFAULT_CAMERA_INDEX


def _load_seed(seed_matcher: SeedMatcher, seed_path: str | None) -> None:
    """Load a seed image from a path or a file dialog."""
    if seed_path is None:
        print("\n📷 Please select a seed QR image...")
        try:
            seed_path = load_seed_image_dialog()
        except Exception:
            seed_path = input("Seed image path (or press Enter to skip): ").strip() or None

    if seed_path:
        success, message = seed_matcher.load_seed_from_file(seed_path)
        if success:
            print(f"✅ {message}")
            if seed_matcher.seed_features:
                print(f"   Reference orientation: {seed_matcher.seed_features['angle']:.1f}°")
        else:
            print(f"❌ {message}")
    else:
        print("⚠️  No seed loaded. Running without matching...")


def _connect_drone(
    drone: DroneController,
    connect_drone: bool | None,
    drone_ip: str | None,
) -> None:
    """Optionally establish a drone connection."""
    if connect_drone is None:
        print("\n🔌 Connect to drone? (y/n): ", end="")
        connect_drone = input().strip().lower() == "y"

    if connect_drone:
        if drone_ip is None or not drone_ip.strip():
            drone_ip = (
                input(f"   Enter drone IP (default {config.DEFAULT_DRONE_IP}): ").strip()
                or config.DEFAULT_DRONE_IP
            )
        drone.drone_ip = drone_ip
        if drone.connect():
            drone.control_enabled = True
            print("✅ Drone control enabled - will auto-rotate to match QR")
        else:
            print("❌ Drone connection failed - continuing without drone")


def run(
    camera_index: int | None = None,
    seed_path: str | None = None,
    connect_drone: bool | None = None,
    drone_ip: str | None = None,
) -> int:
    """Run the AeroQR detection loop.

    Args:
        camera_index: Camera index to open. ``None`` triggers an interactive prompt.
        seed_path: Path to a seed QR image. ``None`` opens a file dialog.
        connect_drone: Whether to connect a drone. ``None`` triggers a prompt.
        drone_ip: Drone command endpoint IP. ``None`` uses the default.

    Returns:
        Process exit code (``0`` on clean shutdown).
    """
    print(BANNER + "\n")

    if camera_index is None:
        camera_index = _select_camera_index()

    seed_matcher = SeedMatcher()
    drone = DroneController()
    _load_seed(seed_matcher, seed_path)
    _connect_drone(drone, connect_drone, drone_ip)

    print("\n🎥 Starting webcam...")
    print("\n💡 TIPS FOR BEST DETECTION:")
    print("   - Hold QR code facing the camera")
    print("   - Ensure good lighting")
    print("   - Avoid extreme angles (>45°)")
    print("   - System auto-calibrates after 5 detections\n")

    try:
        cam = WebcamStream(camera_index)
    except Exception:
        print(f"\n❌ Failed to open camera {camera_index}")
        print("   Trying camera index 0 as fallback...")
        cam = WebcamStream(0)

    worker = QRWorker(seed_matcher)
    tracker = SimpleTracker()

    last_data = ""
    last_match_info = None
    last_orientation = None
    lost_frames = 0
    display_pts = None
    no_qr_count = 0
    detection_count = 0

    print("\n✅ Ready! Point your webcam at a QR code...\n")

    try:
        while True:
            ret, frame, cam_fps = cam.read()
            if not ret or frame is None:
                print("⚠️  Webcam error - trying to reconnect...")
                time.sleep(1)
                continue

            frame_h, frame_w = frame.shape[:2]

            worker.submit(frame)
            data, raw_pts, match_info, orientation_info = worker.get()

            if match_info and match_info.get("is_match", False):
                last_match_info = match_info
                last_orientation = orientation_info
                no_qr_count = 0
                detection_count += 1

                if raw_pts is not None and not seed_matcher.is_calibrated:
                    seed_matcher.auto_calibrate(raw_pts)

            if raw_pts is not None:
                ordered = order_points(raw_pts.astype(np.float32))
                if is_valid_qr(ordered, frame_w, frame_h):
                    display_pts = tracker.update(ordered)
                    lost_frames = 0
                    no_qr_count = 0

                    if drone.control_enabled and display_pts is not None:
                        cx = int(np.mean(display_pts[:, 0]))
                        cy = int(np.mean(display_pts[:, 1]))
                        drone.navigate_to_qr((cx, cy), (frame_w // 2, frame_h // 2), orientation_info)
                        drone.search_mode = False

                    if data and data != last_data:
                        if match_info and match_info.get("is_match", False):
                            print(f"\n✅ QR MATCHED! [#{detection_count}]")
                            print(f"   Data: {data}")
                            if orientation_info:
                                print(
                                    f"   Angle: {orientation_info['current_angle']:.1f}° "
                                    f"(target: {orientation_info['target_angle']:.1f}°)"
                                )
                        else:
                            print(f"\n📱 QR Detected: {data}")
                        last_data = data
            else:
                lost_frames += 1
                no_qr_count += 1

                if drone.control_enabled and no_qr_count > 10:
                    drone.search_for_qr()
                    drone.search_mode = True

                if lost_frames >= config.LOSE_AFTER:
                    if display_pts is not None:
                        print("\n⚠️  QR lost - searching...")
                    display_pts = None
                    last_data = ""
                    last_match_info = None
                    last_orientation = None
                    tracker.reset()

            # Draw UI
            if display_pts is not None:
                draw_overlay(frame, display_pts, last_data, last_match_info, last_orientation)

                if last_match_info and last_match_info.get("is_match", False):
                    if last_orientation and not last_orientation.get("is_angle_ok", True):
                        status = "⚠️  ADJUSTING ROTATION"
                        color = (0, 165, 255)
                    else:
                        status = "✅ QR MATCHED"
                        color = (0, 255, 0)
                else:
                    status = "QR LOCKED"
                    color = (0, 0, 255)
            else:
                if drone.control_enabled and drone.search_mode:
                    status = "🔍 SEARCHING FOR QR..."
                    color = (0, 165, 255)
                else:
                    status = "SCANNING..."
                    color = (160, 160, 160)

            cv2.rectangle(frame, (0, 0), (frame_w, 50), (0, 0, 0), -1)
            cv2.putText(frame, status, (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)

            if seed_matcher.seed_loaded:
                seed_short = seed_matcher.seed_data[:25] + "..."
                cv2.putText(
                    frame, f"SEED: {seed_short}", (frame_w - 280, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 200, 100), 1, cv2.LINE_AA,
                )

                if last_orientation:
                    angle_diff = last_orientation.get("angle_diff", 0)
                    if abs(angle_diff) > 5:
                        cv2.putText(
                            frame, f"ANGLE ERROR: {abs(angle_diff):.1f}°", (frame_w - 280, 45),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 165, 255), 1, cv2.LINE_AA,
                        )

            if drone.control_enabled:
                cv2.putText(
                    frame, "DRONE: ACTIVE", (frame_w - 150, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1, cv2.LINE_AA,
                )

            cv2.putText(
                frame, f"{cam_fps:.0f} FPS", (frame_w - 80, 45),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 200, 100), 1, cv2.LINE_AA,
            )
            cv2.putText(
                frame, HELP_TEXT, (12, frame_h - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1, cv2.LINE_AA,
            )

            cv2.imshow(config.WINDOW_TITLE, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                if drone.control_enabled:
                    drone.land()
                break
            elif key == ord("l"):
                _load_seed(seed_matcher, None)
                lost_frames = config.LOSE_AFTER + 1
                last_match_info = None
                last_orientation = None
            elif key == ord("r"):
                seed_matcher.reset()
                last_match_info = None
                last_orientation = None
                detection_count = 0
                print("\n🔄 Seed matcher reset\n")
            elif key == ord("d"):
                drone.control_enabled = not drone.control_enabled
                if drone.control_enabled:
                    drone.search_mode = True
                    print("\n🚁 Drone control ENABLED - auto-rotation active\n")
                else:
                    print("\n🚁 Drone control DISABLED\n")
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user.")
    finally:
        worker.stop()
        cam.stop()
        drone.disconnect()
        cv2.destroyAllWindows()
        print("\n👋 Detector closed.")

    return 0
