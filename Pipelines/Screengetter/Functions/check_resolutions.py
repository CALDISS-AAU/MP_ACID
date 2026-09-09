"""Determine and persist the resolutions of video files."""

import json
from collections.abc import Iterable
from math import inf
from pathlib import Path

import cv2


def determine_smallest_resolution(
    files: Iterable[Path],
    output_dir: Path,
    replace_resolutions = False
) -> dict[str, int]:
    """Read video resolutions and returns smallest resolution"""

    files = list(files)
    if not files:
        raise ValueError("No video files supplied")

    output_dir.mkdir(parents = True, exist_ok = True)
    output_path = output_dir / "resolutions.json"

    if output_path.is_file() and not replace_resolutions:

        with output_path.open("r", encoding="utf-8") as input_file:
            resolutions = json.load(input_file)

        smallest_total = min([res.get("total") for res in resolutions])

        smallest_resolution = next({"width": res["width"], "height": res["height"]} for res in resolutions if res.get("total") == smallest_total)

        return smallest_resolution
    
    else:
        
        resolutions: list[dict[str, str]] = []
        smallest_total= inf

        for video_path in files:
            cap = cv2.VideoCapture(video_path)

            try:
                if not cap.isOpened():
                    raise ValueError(f"Could not open video: {video_path}")

                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                if width <= 0 or height <= 0:
                    raise ValueError(f"Invalid video resolution: {video_path}")

                total = width*height

                resolutions.append(
                    {
                        "filename": video_path.name,
                        "width": width,
                        "height" : height,
                        "total": total
                    }
                )

                if total < smallest_total:
                    smallest_total = total
                    smallest_resolution = {"width": width, "height": height}
                    
            finally:
                cap.release()
        
        with output_path.open("w", encoding="utf-8") as output_file:
            json.dump(resolutions, output_file, indent=2)

        return smallest_resolution
