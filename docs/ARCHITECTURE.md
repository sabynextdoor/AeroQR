# AeroQR

## Overview

**AeroQR** is a real-time QR code detection and drone-orientation tracking
system developed for the **ISRO Innovation and Research Outreach Cell
(IROUC) 2026** challenge. It combines OpenCV QR detection with seed-image
matching, auto-calibration and a lightweight UDP drone control channel to
steer a drone into perfect alignment with a reference QR code.

## Project layout

```
AeroQR/
├── .github/                 # CI/CD workflows, issue & PR templates
├── docs/                    # Extended documentation (Markdown)
├── src/aeroqr/
│   ├── __init__.py          # Package metadata
│   ├── __main__.py          # python -m aeroqr entry point
│   ├── app.py               # End-to-end orchestration / main loop
│   ├── cli.py               # Command line interface
│   ├── config.py            # Centralised tunable parameters
│   ├── controller.py        # DroneController (UDP command channel)
│   ├── detector.py          # QRWorker (background multi-scale detection)
│   ├── matcher.py           # SeedMatcher (seed matching + calibration)
│   ├── stream.py            # WebcamStream (threaded capture)
│   ├── tracker.py           # SimpleTracker (exponential smoothing)
│   └── utils.py             # Geometry, validation, drawing, dialogs
├── tests/                   # pytest unit tests
├── pyproject.toml           # Build config, dependencies, tooling
├── requirements.txt         # Runtime dependencies
├── requirements-dev.txt     # Development dependencies
└── LICENSE                  # MIT license
```

## Architecture

```
                         ┌──────────────────────────────────────────┐
                         │              WebcamStream               │
                         │          (background capture)           │
                         └───────────────────┬──────────────────────┘
                                             │ frames @ 30+ FPS
                                             ▼
                         ┌──────────────────────────────────────────┐
                         │               QRWorker                   │
                         │  6 scales × {gray, CLAHE, sharpen, Otsu} │
                         │          (dedicated thread)              │
                         └───────────────────┬──────────────────────┘
                                             │ data + 4 corner points
                                             ▼
                         ┌──────────────────────────────────────────┐
                         │              SeedMatcher                 │
                         │  payload match ─ auto-calibrate ─ angle  │
                         └───────────────────┬──────────────────────┘
                                             │ match_info + orientation_info
                                             ▼
                         ┌──────────────────────────────────────────┐
                         │    SimpleTracker → UI overlay (cv2)      │
                         │                   │                      │
                         │                   ▼                      │
                         │        DroneController (UDP)             │
                         └──────────────────────────────────────────┘
```

The detection pipeline deliberately avoids frames being copied between
threads whenever possible: `WebcamStream` performs capture on its own thread,
`QRWorker` runs the detector on a separate thread and the main loop is
reserved for tracking, rendering and control.

## Data flow

1. **Capture** — `WebcamStream` continuously grabs frames in a background
   thread and reports a rolling FPS estimate.
2. **Detect** — `QRWorker` submits each frame through up to 6 scale levels
   × 4 pre-processing strategies (plain grayscale, CLAHE, sharpening, Otsu)
   until a QR code is found.
3. **Match** — `SeedMatcher` compares the decoded payload with the reference
   seed using exact or character-similarity matching.
4. **Calibrate** — after 5 detections the reference orientation is locked
   using the median of the observed angles.
5. **Orient** — the angle difference drives terminal hints and the animated
   rotation arrow.
6. **Track** — `SimpleTracker` smooths corner positions so the overlay is
   stable even when the detector jitters.
7. **Control** — `DroneController` translates rotation/centering errors into
   throttled UDP commands (`ROTATE_*`, `MOVE_*`, `HOVER`, `LAND`).

## Detection pipeline

| Stage          | Purpose                                   |
| -------------- | ----------------------------------------- |
| Grayscale      | Fast baseline scan                        |
| CLAHE          | Contrast normalisation for bad lighting   |
| Sharpen        | Edge enhancement for blurry codes         |
| Otsu           | Binary segmentation fallback              |
| Scale 2.0×-0.6×| Multi-scale window for near/far codes     |

Each frame is scanned in up to 18 scale×strategy combinations, which is why
the detector maintains 60+ FPS: the processing happens off the main loop.

## Failure & recovery modes

- **QR temporarily lost** — the tracker keeps the last known estimate (grey
  box) for `LOSE_AFTER` frames before declaring the code lost.
- **QR missing for 10+ frames** — with drone control enabled, the drone is
  commanded to search (`ROTATE_RIGHT 20`).
- **Camera disconnect** — the stream retries opening the camera; the app
  falls back to camera index 0 automatically.