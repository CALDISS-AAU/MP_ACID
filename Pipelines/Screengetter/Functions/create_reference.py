"""Create reference PNGs and frame arrays from a directory of videos."""

## IMPORTS ##
import json
from math import isfinite
from pathlib import Path
import random
import logging

import cv2
import numpy as np

from .arrays_from_frames import iter_framearrays
from .check_resolutions import determine_smallest_resolution
from .frame_similarity import frames_are_similar, frames_are_not_similar

## _______ ##


## STATIC VARIABLES ##
VIDEO_EXTENSIONS = {".mp4", ".wmv"}

## LOGGER ## 
logger = logging.getLogger(__name__)

## MAIN FUNCTIONALITY ##
def create_reference(
    input_dir: Path,
    output_dir: Path,
    *,
    similarity_threshold: float = 0.5,
    seed_use = None
) -> list[dict]:
    """
    Save reference frames sampled every five seconds from each video.

    Frames are resized to the dimensions of the video with the fewest pixels.
    The first sampled frame is retained. Subsequent frames are retained only
    when their LPIPS distance exceeds similarity_threshold for every retained
    frame across all input videos. Higher thresholds reject more frames. The
    default 0.1 is a starting point to tune on your videos. Comparisons resize
    full frames to 224x224; saved frames keep the common video resolution.
    Pretrained model weights download on first comparison and are cached locally.

    PNGs and NPYs use matching names in output_dir. Arrays retain OpenCV's BGR
    channel order. reference_lookup.json records their relative paths, source
    video, timestamp in seconds, dimensions and color order. The same lookup
    entries are returned. Only direct children with video extensions are read.
    Existing matching output filenames are overwritten; the lookup describes
    the current run. Source videos are never modified.
    """

    if not isfinite(similarity_threshold) or similarity_threshold < 0:
        raise ValueError("similarity_threshold must be finite and non-negative")

    random.seed(seed_use)

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

    sample_video_files = random.sample(video_files, 10)

    output_dir.mkdir(parents = True, exist_ok = True)
    smallest_resolution = determine_smallest_resolution(
        files = video_files,
        output_dir = output_dir,
        replace_resolutions = True
    )

    logger.info(f"Standardizing references using resolution {smallest_resolution.get("width")}x{smallest_resolution.get("height")}")

    lookup = []
    retained_frames = []

    for video_path in sample_video_files:
        cap = cv2.VideoCapture(str(video_path))

        try:
            if not cap.isOpened():
                raise ValueError(f"Could not open video: {video_path}")

            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)

            frames_read = iter_framearrays(
                cap, 
                start_s = 0, 
                stop_s = frame_count / fps, 
                dt = 5,
                use_resolution = smallest_resolution
            )

            if not frames_read:
                raise ValueError(f"Could not read any frames from: {video_path}")

            for timestamp_s, frame in frames_read:
                
                retain_frame = all(
                    frames_are_not_similar(frame, retained_frame, similarity_threshold)
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

        finally:
            cap.release()

    with (output_dir / "reference_lookup.json").open("w", encoding = "utf-8") as output_file:
        json.dump(lookup, output_file, indent=2)

    return lookup, smallest_resolution
