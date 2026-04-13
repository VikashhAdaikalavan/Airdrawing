# AirDrawing (Draw in Air)

![Python](https://img.shields.io/badge/Python-3.8+-blue) ![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green) ![MediaPipe](https://img.shields.io/badge/MediaPipe-latest-orange)

Paint on your screen using just your hand — no stylus, no tablet, no touching anything.

---

## What it does

- Tracks your index finger in real time using your webcam
- Lets you draw, erase, and pause using hand gestures alone
- Smooth brush strokes with a 5-frame averaging buffer
- Pick any color, resize brush/eraser on the fly, and save your art as a PNG

---

## Gestures

| Gesture | Action |
|---|---|
| ☝️ Index finger up, rest folded | **Draw** |
| ✊ Fist or 2–3 fingers extended | **Erase** (uses palm center) |
| 🖐️ All four fingers extended | **Pause** |

> **Tip:** Good lighting makes a big difference. Face a window or a lamp — the hand tracker struggles in dim rooms.

---

## Setup

**Requirements:** Python 3.8+, a webcam

**1. Install dependencies**
```bash
pip install opencv-python mediapipe numpy pillow
```

> `tkinter` ships with most Python installs. If it's missing on Linux:
> ```bash
> sudo apt install python3-tk
> ```

**2. Run the app**
```bash
python drawing.py
```

The app opens a window with your camera feed on the left and controls on the right. Hold your hand up and start drawing.

---

## Dependencies

| Package | Purpose |
|---|---|
| `opencv-python` | Camera feed and drawing on canvas |
| `mediapipe` | Hand landmark detection |
| `numpy` | Canvas and image processing |
| `Pillow` | Displaying frames in the UI |
| `tkinter` | GUI window and controls |

---

## Controls

| Control | Description |
|---|---|
| **Change Color** | Opens a color picker dialog |
| **Brush Size** | Slider from 2 to 20px |
| **Eraser Size** | Slider from 10 to 60px |
| **Clear Canvas** | Wipes the drawing (no undo) |
| **Save Drawing** | Saves a PNG to the same folder with a timestamp |

---

## Notes

- Only one hand is tracked at a time
- Drawings are saved as `air_drawing_YYYYMMDD_HHMMSS.png` in the same directory as the script
- No internet connection required — everything runs locally
