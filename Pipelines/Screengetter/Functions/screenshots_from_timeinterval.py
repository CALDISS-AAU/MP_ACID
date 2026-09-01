"""Extract screenshots from screenrecordings"""

## IMPORTS ##
import logging
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

## _______ ##


## HELPER FUNCTIONS ##
def _frames_are_similar(frame1, frame2, tolerance_pct = 5):
    """Determine whether two frames are near identical based on tolerance_pct (% pixels allowed to deviate)"""
    
    pixels_differ = np.any(frame1 != frame2, axis=2)

    diff_pct = pixels_differ.mean() * 100

    below_tolerance = diff_pct < tolerance_pct

    return below_tolerance

## MAIN FUNCTIONALITY ##

def extract_screenshots(
    screenrec_filepath: Path,
    time_interval: range,
    freq_per_s: int = 1,
) -> list[tuple[float, Image.Image]]:
    """
    Extract screenshots from an MP4 at a fixed frequency.

    Parameters
    ----------
    screenrec_filepath:
        Path to the MP4 file.

    time_interval:
        Time interval in seconds. For example, range(10, 20) extracts
        frames from 10.0 seconds up to (but not including) 20.0 seconds.

    freq_per_s:
        Number of screenshots to extract per second.

    Returns
    -------
    list[tuple[float, Image.Image]]
        A list of (timestamp_seconds, screenshot) tuples.
    """
    if freq_per_s <= 0:
        raise ValueError("freq_per_s must be greater than 0")

    if not screenrec_filepath.exists():
        raise FileNotFoundError(screenrec_filepath)

    cap = cv2.VideoCapture(str(screenrec_filepath))

    if not cap.isOpened():
        raise ValueError(f"Could not open video: {screenrec_filepath}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration_s = frame_count / fps

    start_s = time_interval.start / 1000
    stop_s = min(time_interval.stop / 1000, duration_s)
    dt = 1 / freq_per_s

    screenshots = []

    timestamp_s = float(start_s)

    while timestamp_s < stop_s:
        # Seek to the requested timestamp.
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_s * 1000)

        success, frame = cap.read()

        if not success:
            break

        #screenshots.append((timestamp_s, frame))
        screenshots.append(frame)

        timestamp_s += dt

        

    # TODO: Aggregate based on frame similarity: from, to, frame

    mean_frame = np.mean(screenshots, axis = 0).astype(np.uint8)
    ## OpenCV uses BGR; PIL expects RGB.
    frame_rgb = cv2.cvtColor(mean_frame, cv2.COLOR_BGR2RGB)
    screenshot = Image.fromarray(frame_rgb)

    cap.release()

    return screenshot, screenshots

