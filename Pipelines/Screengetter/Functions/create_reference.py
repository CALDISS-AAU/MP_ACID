"""Create reference PNGs and frame arrays from a directory of videos."""

## IMPORTS ##
import json
from math import isfinite
from pathlib import Path

import cv2
import numpy as np

from .arrays_from_frames import iter_framearrays
from .check_resolutions import determine_smallest_resolution

## _______ ##


## STATIC VARIABLES ##
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".m4v", ".webm", ".wmv", ".mpg", ".mpeg"}


## MAIN FUNCTIONALITY ##
def create_reference(
    input_dir: Path,
    output_dir: Path
) -> list[dict]:
    """
    Save reference frames sampled every five seconds from each video.

    Frames are resized to the dimensions of the video with the fewest pixels.
    The first sampled frame is retained. Subsequent frames are retained when
    more than 50% of pixels differ from at least one already retained frame
    across all input videos. A match with another retained frame does not veto
    retention. A pixel differs when any BGR channel differs; comparison is
    exact, without a channel-value tolerance.

    PNGs and NPYs use matching names in output_dir. Arrays retain OpenCV's BGR
    channel order. reference_lookup.json records their relative paths, source
    video, timestamp in seconds, dimensions and color order. The same lookup
    entries are returned. Only direct children with video extensions are read.
    Existing matching output filenames are overwritten; the lookup describes
    the current run. Source videos are never modified.
    """

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.is_dir():
        raise NotADirectoryError(input_dir)

    video_files = sorted(
        path for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    )

    if not video_files:
        raise ValueError(f"No video files found in: {input_dir}")

    output_dir.mkdir(parents = True, exist_ok = True)
    smallest_resolution = determine_smallest_resolution(
        files = video_files,
        output_dir = output_dir,
        replace_resolutions = True
    )

    lookup = []
    retained_frames = []

    for video_path in video_files:
        cap = cv2.VideoCapture(str(video_path))

        try:
            if not cap.isOpened():
                raise ValueError(f"Could not open video: {video_path}")

            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            if not isfinite(fps) or fps <= 0 or not isfinite(frame_count) or frame_count <= 0:
                raise ValueError(f"Invalid video duration metadata: {video_path}")

            frames_read = False

            for timestamp_s, frame in iter_framearrays(
                cap, 0, frame_count / fps, 5,
                use_resolution = smallest_resolution
            ):
                frames_read = True
                retain_frame = not retained_frames or all(
                    np.any(frame != retained_frame, axis=2).mean() > 0.5
                    for retained_frame in retained_frames
                )

                if not retain_frame:
                    continue

                # Include the video extension to distinguish equal stems.
                filename_stub = f"{video_path.name}_{int(timestamp_s):010d}"
                png_path = output_dir / f"{filename_stub}.png"
                npy_path = output_dir / f"{filename_stub}.npy"

                if not cv2.imwrite(str(png_path), frame):
                    raise OSError(f"Could not write reference image: {png_path}")
                np.save(npy_path, frame)
                retained_frames.append(frame)

                lookup.append(
                    {
                        "source_video": video_path.name,
                        "timestamp_s": timestamp_s,
                        "png_path": png_path.name,
                        "npy_path": npy_path.name,
                        "width": smallest_resolution["width"],
                        "height": smallest_resolution["height"],
                        "color_order": "BGR"
                    }
                )

            if not frames_read:
                raise ValueError(f"Could not read any frames from: {video_path}")

        finally:
            cap.release()

    with (output_dir / "reference_lookup.json").open("w", encoding = "utf-8") as output_file:
        json.dump(lookup, output_file, indent=2)

    return lookup
