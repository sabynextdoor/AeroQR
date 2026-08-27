# AeroQR API

AeroQR is installable as a normal Python package and exposes a small public
API. The recommended way to use it programmatically is:

```python
from aeroqr.matcher import SeedMatcher
from aeroqr.detector import QRWorker
from aeroqr.tracker import SimpleTracker
from aeroqr.controller import DroneController
```

## aeroqr.cli

| Function      | Signature                                        | Description                         |
| ------------- | ------------------------------------------------ | ----------------------------------- |
| `main`        | `(argv: Sequence[str] | None = None) -> int`     | Console entry point.                |
| `build_parser`| `() -> argparse.ArgumentParser`                  | Builds the `aeroqr` CLI arguments.  |

The CLI is also available as `python -m aeroqr`. Run `aeroqr --help` for the
full list of flags.

## aeroqr.app

| Function | Signature | Description |
| -------- | --------- | ----------- |
| `run`    | `(camera_index: int | None = None, seed_path: str | None = None, connect_drone: bool | None = None, drone_ip: str | None = None) -> int` | Runs the full detection loop. Omitted arguments trigger the same interactive prompts as the CLI. |

## aeroqr.matcher.SeedMatcher

| Method | Description |
| ------ | ----------- |
| `load_seed_from_file(filepath) -> (bool, str)` | Loads and decodes a seed QR image. |
| `compare_with_seed(qr_data) -> (bool, float)` | Payload + similarity comparison. |
| `analyze_orientation(qr_corners) -> dict | None` | Angle error vs. the calibrated seed. |
| `auto_calibrate(qr_corners) -> bool` | Collects samples and locks the reference angle. |
| `reset()` | Clears seed + calibration state. |

**analyze_orientation output**

| Key               | Type   | Description                              |
| ----------------- | ------ | ---------------------------------------- |
| `current_angle`   | float  | Observed top-edge angle in degrees.      |
| `target_angle`    | float  | Calibrated seed angle.                   |
| `angle_diff`      | float  | Signed error in degrees (`-180..180`).   |
| `rotation_direction` | str \| None | `clockwise` / `counter-clockwise`. |
| `rotation_amount` | float  | Absolute error magnitude.                |
| `is_angle_ok`     | bool   | `True` when `|angle_diff| <= 10°`.       |

## aeroqr.detector.QRWorker

| Method | Description |
| ------ | ----------- |
| `submit(frame)` | Queues the latest frame for the background worker. |
| `get()` | Returns `(data, points, match_info, orientation_info)`. |
| `stop()` | Stops the worker thread. |

## aeroqr.stream.WebcamStream

| Method | Description |
| ------ | ----------- |
| `read() -> (bool, frame, fps)` | Returns the latest frame with a rolling FPS. |
| `stop()` | Releases the camera. |

## aeroqr.tracker.SimpleTracker

| Method | Description |
| ------ | ----------- |
| `update(pts) -> ndarray | None` | Smoothed corner estimate. |
| `reset()` | Clears tracking state. |

## aeroqr.controller.DroneController

| Method | Description |
| ------ | ----------- |
| `connect() -> bool` | Opens the UDP command socket. |
| `send_command(command: str)` | Throttled command transmission. |
| `navigate_to_qr(qr_center, frame_center, orientation_info)` | Priority: rotation → centering → hover. |
| `search_for_qr()` | Issues a pan command. |
| `land()` / `disconnect()` | Land / release resources. |

## aeroqr.utils

| Function | Description |
| -------- | ----------- |
| `order_points(pts) -> ndarray` | Orders corners TL, TR, BR, BL. |
| `is_valid_qr(pts, w, h) -> bool` | Geometric sanity check. |
| `draw_overlay(frame, pts, data, match, orient)` | Renders the full HUD. |
| `draw_rotation_arrow(frame, center, direction, deg)` | Rotation arrow overlay. |
| `load_seed_image_dialog() -> str | None` | Native file picker. |

## Environment variables

AeroQR does not require environment variables. All runtime parameters are
centralised in [`src/aeroqr/config.py`](../src/aeroqr/config.py) and can be
overridden at the CLI level with `--camera`, `--seed`, `--drone` and
`--drone-ip`.