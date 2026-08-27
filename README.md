<div align="center">

# AeroQR

### Real-time QR detection, seed matching & drone-orientation tracking

*Built for the **ISRO Innovation and Research Outreach Cell (IROUC) 2026** challenge*

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.5%2B-5C3EE8?logo=opencv&logoColor=white)](https://opencv.org/)
[![NumPy](https://img.shields.io/badge/NumPy-1.21%2B-013243?logo=numpy&logoColor=white)](https://numpy.org/)

[![Build](https://img.shields.io/github/actions/workflow/status/sabynextdoor/AeroQR/ci.yml?branch=main&label=CI&logo=github)](https://github.com/sabynextdoor/AeroQR/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/sabynextdoor/AeroQR?sort=semver&logo=github)](https://github.com/sabynextdoor/AeroQR/releases)
[![PyPI](https://img.shields.io/pypi/v/aeroqr?logo=pypi&logoColor=white)](https://pypi.org/project/aeroqr/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)]()

[![Stars](https://img.shields.io/github/stars/sabynextdoor/AeroQR?logo=github)](https://github.com/sabynextdoor/AeroQR/stargazers)
[![Forks](https://img.shields.io/github/forks/sabynextdoor/AeroQR?logo=github)](https://github.com/sabynextdoor/AeroQR/forks)
[![Contributors](https://img.shields.io/github/contributors/sabynextdoor/AeroQR?logo=github)](https://github.com/sabynextdoor/AeroQR/graphs/contributors)
[![Issues](https://img.shields.io/github/issues/sabynextdoor/AeroQR?logo=github&color=red)](https://github.com/sabynextdoor/AeroQR/issues)
[![PRs](https://img.shields.io/github/issues-pr/sabynextdoor/AeroQR?logo=github&color=brightgreen)](https://github.com/sabynextdoor/AeroQR/pulls)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

**A high-performance computer-vision system that finds a target QR code in a
live camera feed, verifies it against a reference "seed" image, and guides a
drone into perfect alignment — all at 60+ FPS.**

</div>

---

## Table of Contents

- [Why AeroQR?](#-why-aeroqr)
- [Features](#-features)
- [Demo](#-demo)
- [How it works](#-how-it-works)
- [Detection pipeline](#-detection-pipeline)
- [Visual feedback](#-visual-feedback)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Quick start](#-quick-start)
- [Usage](#-usage)
  - [CLI reference](#cli-reference)
  - [Interactive controls](#keyboard-controls)
- [Drone protocol](#-drone-protocol)
- [Performance tuning](#-performance-tuning)
- [Project structure](#-project-structure)
- [Testing & development](#-testing--development)
- [Documentation](#-documentation)
- [Roadmap](#-roadmap)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

---

## 🎯 Why AeroQR?

QR codes are the visual anchors of autonomous drone applications — landing
markers, package drop zones, warehouse labels, survey fiducials. The hard part
isn't just *seeing* the code; it's recognising **the right one** and aligning
to it from a moving, vibrating, tilted platform.

AeroQR solves all three problems in a single threaded pipeline:

| Problem | AeroQR solution |
| --- | --- |
| **Seeing it** | Multi-scale detection over 4 pre-processing strategies in a dedicated worker thread. |
| **Recognising it** | Exact + similarity seed matching against a loaded reference image. |
| **Aligning to it** | Auto-calibrated orientation analysis and prioritised UDP drone commands. |

## ✨ Features

- 🚀 **60+ FPS real-time detection** — capture, detection and rendering run on separate threads.
- 🎯 **Multi-scale scanning** — 6 scales × 4 strategies for near, far and fuzzy codes.
- 🔄 **Auto-calibration** — locks the reference orientation from 5 median-stabilised samples.
- 📐 **Orientation feedback** — computes angle error within a 10° tolerance.
- 🧠 **Kalman-style tracking** — smooths corners; keeps position during brief losses.
- 🎨 **Rich HUD overlay** — status bar, corner markers, crosshair, rotation arrow.
- 🚁 **Drone control** — UDP command channel with cooldown throttling and navigation priorities.
- 🖥️ **Camera auto-discovery** — DirectShow + fallback, external webcam by default.
- 🔌 **Installs anywhere** — `pip install`, console script, or `python -m aeroqr`.

## 🎬 Demo

> 🎥 **Demo video slot** — the installation / live-detection demo clip goes here.
> Drop your clip in and link it from the [Releases](https://github.com/sabynextdoor/AeroQR/releases)
> tab (or add `assets/demo.mp4` to the repo) and it will render inline on this page.

**Try it live:**

```bash
python -m aeroqr
```

Hold a printed QR code up to your camera — within a few seconds the system locks
onto it, auto-calibrates the reference orientation and starts steering towards a
perfect, dead-centre alignment. The [Releases](https://github.com/sabynextdoor/AeroQR/releases)
tab carries the built package artifacts for every version.

## 🧠 How it works

```
 ┌─────────────────────────────────────────┐
 │  WebcamStream  (capture thread)         │
 │  ─────────────────────────────────────  │
 │  1280×720 @ 30 FPS                      │
 └──────────────┬──────────────────────────┘
                │ frames
                ▼
 ┌─────────────────────────────────────────┐
 │  QRWorker  (detector thread)            │
 │  ─────────────────────────────────────  │
 │  6 scales × {gray · CLAHE · sharpen}    │
 │  + Otsu fallback                        │
 └──────────────┬──────────────────────────┘
                │ data + 4 corners
                ▼
 ┌─────────────────────────────────────────┐
 │  SeedMatcher                            │
 │  ─────────────────────────────────────  │
 │  payload match → auto-calibrate → angle │
 └──────────────┬──────────────────────────┘
                │ match + orientation
                ▼
 ┌─────────────────────────────────────────┐
 │  SimpleTracker → Overlay (main thread)  │
 │                   │                     │
 │                   ▼                     │
 │  DroneController (UDP, throttled)       │
 └─────────────────────────────────────────┘
```

The **capture**, **detection** and **main loop** are fully decoupled, so the
serialised detector never blocks the camera reader or the renderer.

## 🔬 Detection pipeline

Each frame is scanned with up to 18 scale × strategy combinations:

| Strategy | When it helps |
| --- | --- |
| Plain grayscale | Fast baseline for clean codes |
| CLAHE enhancement | Poor or uneven lighting |
| Sharpening filter | Slightly blurred / motion-affected codes |
| Otsu thresholding | High-contrast fallback for weak detections |
| Upscaling 2.0× → 1.2× | Small / far-away QR codes |
| Downscaling 0.8× → 0.6× | Large codes that dominate the frame |

## 🎨 Visual feedback

| Colour | Meaning |
| --- | --- |
| 🟩 Green box | Matched seed, correct orientation |
| 🟧 Orange box | Matched seed, rotate to align |
| 🟥 Red box | QR present but wrong seed |
| ⬜ Grey box | Predicted position (temporarily lost) |
| ➡️ Arrow | Animated direction to rotate |

The status bar shows `✅ QR MATCHED`, `⚠️ ADJUSTING ROTATION`, `QR LOCKED`,
`🔍 SEARCHING FOR QR...` or `SCANNING...`, and the terminal prints live angle
instructions.

## 📋 Requirements

- **Python 3.8+**
- **OpenCV 4.5+** (with contrib-free `QRCodeDetector`)
- **NumPy 1.21+**
- Tkinter (bundled with most Python installers — used only for the file dialog)

Support for older Windows setups through the DirectShow backend is included.

## 🔧 Installation

### Option 1 — pip (recommended)

```bash
pip install aeroqr
```

### Option 2 — from source

```bash
git clone https://github.com/sabynextdoor/AeroQR.git
cd AeroQR

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -e ".[dev]"
```

### Verify

```bash
python -m aeroqr --version
# or
aeroqr --version
```

## 🚀 Quick start

```bash
# Run the app (you'll be guided through camera + seed selection):
python -m aeroqr

# Fully automated (camera 0, headless-friendly args):
python -m aeroqr --camera 0 --seed path/to/seed.png
```

1. **Select a camera** — press <kbd>Enter</kbd> for the external webcam, or type `0` for the laptop camera.
2. **Load the seed QR** — pick any image containing the QR you want to track.
3. **Connect a drone (optional)** — answer `n` for visual feedback only.
4. **Scan** — hold the QR code up to the camera. Watch it lock, calibrate and align.

## 🖥️ Usage

### CLI reference

```text
usage: aeroqr [-h] [--version] [-c CAMERA] [-s SEED] [-d] [--drone-ip DRONE_IP]

AeroQR — real-time QR detection, seed matching and orientation tracking
for drone applications (ISRO IROUC 2026).

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -c, --camera CAMERA   camera index to open (default: interactive prompt)
  -s, --seed SEED       path to the seed QR image (default: file dialog)
  -d, --drone           enable drone control (default: interactive prompt)
  --drone-ip DRONE_IP   drone command IP address (default: 192.168.1.100)
```

### Keyboard controls

| Key | Action |
| --- | --- |
| <kbd>Q</kbd> | Quit (and command the drone to `LAND` if connected) |
| <kbd>L</kbd> | Load a new seed QR image |
| <kbd>R</kbd> | Reset the seed matcher and calibration |
| <kbd>D</kbd> | Toggle drone control on/off |

### Preparing seed images

- Use **high-contrast** QR codes (black on white).
- Provide at least **200 × 200 px**, undistorted.
- Capture the seed **upright** — the system calibrates to this orientation.
- Works with `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`.

## 🚁 Drone protocol

Commands are sent over **UDP** (default `192.168.1.100:8888`) with a 300 ms
cooldown between transmissions. Navigation is prioritised:

1. **Fix rotation** — `ROTATE_LEFT <n>°` / `ROTATE_RIGHT <n>°`
2. **Centre horizontally** — `MOVE_LEFT` / `MOVE_RIGHT <n>`
3. **Centre vertically** — `MOVE_UP` / `MOVE_DOWN <n>`
4. **Hover** — `HOVER`

When the QR disappears for more than 10 frames, the drone sweeps with
`ROTATE_RIGHT 20` until it reacquires the target.

> ⚠️ **Security note:** the drone channel is unauthenticated. Use it only on
> trusted, isolated networks. See [SECURITY.md](SECURITY.md).

## 🚄 Performance tuning

All tunables live in [`src/aeroqr/config.py`](src/aeroqr/config.py):

| Parameter | Default | Description |
| --- | --- | --- |
| `DETECTION_SCALES` | `(2.0 … 0.6)` | Scale window per frame |
| `MATCHING_THRESHOLD` | `85` | % similarity for a positive match |
| `CALIBRATION_SAMPLES` | `5` | Detections before locking angle |
| `ANGLE_TOLERANCE` | `10` | Degrees of accepted error |
| `SMOOTH_FACTOR` | `0.7` | Corner smoothing (higher = steadier) |
| `LOSE_AFTER` | `30` | Frames before QR is declared lost |
| `COMMAND_COOLDOWN` | `0.3` | Seconds between drone commands |

Low latency tips: close background apps, prefer a USB3 webcam, and keep
`CAPTURE_BUFFER_SIZE = 1` to avoid frame lag.

## 📂 Project structure

```
AeroQR/
├── .github/                 # CI/CD + issue & PR templates
├── docs/                    # ARCHITECTURE.md · API.md
├── src/aeroqr/
│   ├── __main__.py          # python -m aeroqr
│   ├── app.py               # orchestration / main loop
│   ├── cli.py               # command-line interface
│   ├── config.py            # tunable parameters
│   ├── controller.py        # DroneController (UDP)
│   ├── detector.py          # QRWorker (background detection)
│   ├── matcher.py           # SeedMatcher (match + calibrate)
│   ├── stream.py            # WebcamStream (threaded capture)
│   ├── tracker.py           # SimpleTracker (smoothing)
│   └── utils.py             # geometry, validation, HUD, dialogs
├── tests/                   # pytest suite
├── pyproject.toml           # packaging, dependencies, tooling
├── requirements.txt
├── requirements-dev.txt
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## 🔬 Testing & development

```bash
pip install -e ".[dev]"
pytest                      # 22 tests
ruff check .                # lint
ruff format --check .       # format
```

CI runs the suite on **Windows + Ubuntu** across **Python 3.9 → 3.12**, and
automatically builds the sdist/wheel. A release workflow drafts GitHub
Releases from `v*` tags; a publishing workflow is wired for PyPI
(trusted publishing).

## 📚 Documentation

- [Architecture & data flow](docs/ARCHITECTURE.md)
- [API reference](docs/API.md)
- [Contributing guide](CONTRIBUTING.md)
- [Code of conduct](CODE_OF_CONDUCT.md)
- [Security policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## 🗺️ Roadmap

- [ ] Audio feedback for rotation instructions
- [ ] Distance estimation from QR size
- [ ] Multiple simultaneous QR tracking
- [ ] Session recording mode
- [ ] PyQt dashboard with live graphs
- [ ] REST API mode

## 🛠️ Troubleshooting

| Symptom | Fix |
| --- | --- |
| No camera found | Re-run with `--camera 0`; check the camera is not locked by another app |
| `ModuleNotFoundError` | `pip install -e ".[dev]"` inside your virtualenv |
| Slow FPS | Reduce `DETECTION_SCALES`, close background apps, use USB3 |
| Detects wrong QR | Load a clearer seed; check `MATCHING_THRESHOLD` |
| No QR ever detected | Improve lighting; keep code < 45° tilt; use a 200×200 px+ print |

## ❓ FAQ

**Do I need a drone?**
No. Without drone control AeroQR is a powerful visual feedback tool — run it,
and the terminal + overlay guide you.

**Why did the standalone script disappear?**
It was promoted into a proper installable package. The logic is unchanged, now
organised into focused modules under `src/aeroqr/`.

**Which camera index should I use?**
`0` = built-in laptop camera, `1` = external USB webcam (default).

## 🤝 Contributing

Contributions of all kinds are welcome — features, bugs, docs, tests. Please
read [CONTRIBUTING.md](CONTRIBUTING.md) first, then:

1. Fork the repo
2. Create a feature branch
3. Make your change + tests
4. Keep `ruff` and `pytest` green
5. Open a pull request

## 📄 License

Released under the [MIT License](LICENSE). Copyright © 2026 sabynextdoor.
Third-party licenses are documented in the [NOTICE](NOTICE) file.

## 🙏 Acknowledgments

- **ISRO IROUC 2026** — for the challenge and the inspiration.
- **OpenCV community** — the computer-vision backbone.
- **NumPy & the Python scientific ecosystem** — for the compute layer.
- Every contributor and tester who helped harden the pipeline.

---

<div align="center">

**Made with ❤️ for ISRO IROUC 2026 by [sabynextdoor](https://github.com/sabynextdoor)**

⭐ Star this repo if AeroQR helps your project — it fuels the roadmap!

Questions? [sabynextdoor@gmail.com](mailto:sabynextdoor@gmail.com)

</div>