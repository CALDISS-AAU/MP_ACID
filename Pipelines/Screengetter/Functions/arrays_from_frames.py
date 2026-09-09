"""Extract screenshots from screenrecordings"""

## IMPORTS ##
import logging
from pathlib import Path

import cv2
import numpy as np

## _______ ##


## HELPER FUNCTIONS ##
def _frames_are_similar(frame1, frame2, tolerance_pct = 10):
    """Determine whether two frames are near identical based on tolerance_pct (% pixels allowed to deviate)"""
    
    pixels_differ = np.any(frame1 != frame2, axis=2)

    diff_pct = pixels_differ.mean() * 100

    below_tolerance = diff_pct < tolerance_pct

    return below_tolerance

def iter_framearrays(
    cap,
    start_s,
    stop_s,
    dt,
    use_resolution: dict | None = None
):
    """Yield (timestamp_seconds, BGR array) samples, optionally resized."""

    if dt <= 0:
        raise ValueError("Frame sampling interval must be positive")

    timestamp_s = float(start_s)

    while timestamp_s < stop_s:
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_s * 1000)
        success, frame = cap.read()

        if not success:
            break

        if use_resolution is not None:
            frame = cv2.resize(
                frame,
                (use_resolution["width"], use_resolution["height"]),
                interpolation = cv2.INTER_AREA
            )

        yield timestamp_s, frame
        timestamp_s += dt


def _get_framearrays_from_interval(
    cap,
    start_s,
    stop_s,
    dt,
    use_resolution: dict | None = None
):
    return list(iter_framearrays(cap, start_s, stop_s, dt, use_resolution))

def _aggregate_framearrays(
    framearrays,
    start_s,
    stop_s,
    dt, 
    similarity_tolerance = 10
    ):

    aggregated_framearrays = []

    if not framearrays:
        raise ValueError("List of framearrays is empty. Nothing to aggregate")
    
    interval_start = framearrays[0][0]
    representative_frame = framearrays[0][1]

    for timestamp_s, frame in framearrays[1:]:
        if _frames_are_similar(representative_frame, frame, similarity_tolerance):
            continue

        interval_end = timestamp_s - dt
        aggregated_framearrays.append(
            (interval_start, interval_end, representative_frame)
        )
        interval_start = timestamp_s
        representative_frame = frame

    interval_end = min(framearrays[-1][0] + dt, stop_s)
    aggregated_framearrays.append(
        (interval_start, interval_end, representative_frame)
    )

    return aggregated_framearrays


## MAIN FUNCTIONALITY ##

def extract_framearrays(
    screenrec_filepath: Path,
    time_intervals: list[range],
    freq_per_s: int = 1,
    standardize_resolution = False,
    use_resolution: dict | None = None
) -> list[tuple]:
    """
    Extract image arrays of frames from a video file at a fixed frequency.

    Parameters
    ----------
    screenrec_filepath:
        Path to the video file.

    time_intervals:
        List of time interval ranges in seconds. For example, range(10, 20) extracts
        frames from 10.0 seconds up to (but not including) 20.0 seconds.

    freq_per_s:
        Number of frames to extract per second.

    standardize_resolution:
        Whether to resize frame to specified resolution (requires use_resolution).

    use_resolution:
        Dict with width and height in pixels to use for resizing frames ({"width": int, "height": int}).


    Returns
    -------
    list[tuple[float, Image.Image]]
        A list of (timestamp_seconds, screenshot) tuples.
    """

    if standardize_resolution and use_resolution is None:
        raise ValueError("Option standardize_resolution=True requires a use_resolution (width, height)")

    if not screenrec_filepath.exists():
        raise FileNotFoundError(screenrec_filepath)

    cap = cv2.VideoCapture(screenrec_filepath)

    if not cap.isOpened():
        raise ValueError(f"Could not open video: {screenrec_filepath}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration_s = frame_count / fps

    framearrays_in_intervals = []

    for time_interval in time_intervals:
        start_s = time_interval.start / 1000
        stop_s = min(time_interval.stop / 1000, duration_s)
        dt = 1 / freq_per_s

        framearrays = _get_framearrays_from_interval(
            cap, start_s, stop_s, dt,
            use_resolution = use_resolution if standardize_resolution else None
        )

        framearrays_aggregated = _aggregate_framearrays(framearrays, start_s, stop_s, dt)

        framearrays_in_intervals.append(framearrays_aggregated)

    cap.release()

    return framearrays_in_intervals

