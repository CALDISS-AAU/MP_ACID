"""Extract screenshots from screenrecordings"""

## IMPORTS ##
from torch import max_pool2d
import logging
from pathlib import Path

import cv2
import numpy as np

from .frame_similarity import frames_are_similar, frames_are_not_similar

## _______ ##

## LOGGER ## 
logger = logging.getLogger(__name__)

## HELPER FUNCTIONS ##
def _get_framearrays_from_interval(
    cap,
    start_s,
    stop_s,
    dt,
    use_resolution: dict | None = None
    ):
    """Wrapper for iter_framearrays to return list instead of generator"""

    return list(iter_framearrays(cap, start_s, stop_s, dt, use_resolution))


def _aggregate_framearrays(
    framearrays,
    start_s,
    stop_s,
    dt, 
    similarity_tolerance = 0.1
    ):
    """Aggregate frames to intervals based on frame similarity (LPIPS distance). If distance between frames are below similarity_tolerance, frames are assumed to be part of the same view."""

    aggregated_framearrays = []

    if not framearrays:
        logger.error(f"List of framearrays from start {start_s} is empty. Nothing to aggregate")
        return []
    
    framearrays = [(timestamp_s, frame) for timestamp_s, frame in framearrays if frame is not None]

    if not framearrays:
        logger.warning(f"No frames for interval with start {start_s}. Nothing to aggregate")
        return [
            (start_s, stop_s, None)
        ]

    interval_start = framearrays[0][0]
    representative_frame = framearrays[0][1]

    for timestamp_s, frame in framearrays[1:]:
        if frames_are_similar(representative_frame, frame, similarity_tolerance):
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
            logger.warning(f"Failed to load frame at {timestamp_s}")
            yield timestamp_s, None
            timestamp_s += dt
            continue
            
        if use_resolution is not None:
            frame = cv2.resize(
                frame,
                (use_resolution["width"], use_resolution["height"]),
                interpolation = cv2.INTER_AREA
            )

        yield timestamp_s, frame
        timestamp_s += dt


def extract_framearrays(
    screenrec_filepath: Path,
    timestamps: list[int],
    freq_per_s: int = 1,
    buffer_ms: int  = 500,
    context_include_ms: int = 5000,
    standardize_resolution = False,
    use_resolution: dict | None = None
) -> list[tuple]:
    """
    Extract image arrays of frames from a video file at a fixed frequency.

    Parameters
    ----------
    screenrec_filepath:
        Path to the video file.

    timestamps:
        List of timestamps in ms.

    freq_per_s:
        Number of frames to extract per second.

    buffer_ms:
        Buffer in ms between last extracted frames and timestamp (default: 500)

    context_include_ms:
        How much context prior to timestamp-buff_ms to include in ms (default: 5000; 5 seconds)

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

    logger.info(f"estimated duration: {duration_s}")

    time_intervals = [
        range(max(timestamp-buffer_ms-context_include_ms, 0), max(timestamp-buffer_ms, 1)) for timestamp in timestamps
    ]

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

