"""Annotate frames based on UI location"""

## IMPORTS ##
import logging
from pathlib import Path
import json

import cv2
import numpy as np

from .frame_similarity import frame_distance

## _______ ##

## LOGGER ## 
logger = logging.getLogger(__name__)

## HELPER FUNCTIONS ##
def _load_references(
    reference_dir: Path,
    reference_set: Path):

    with open(reference_set, "r") as f:
        reference_lookup = json.load(f)

    references = []

    for reference_info in reference_lookup:

        npy_path = reference_dir / reference_info.get("npy_path")
        tag = reference_info.get("tag")

        reference_frame = np.load(npy_path)

        references.append(
            {
                "frame": reference_frame, 
                "tag": tag
                }
                )
        
    return references

## MAIN FUNCTIONS ##
def annotate_frame(
    frame: np.ndarray,
    reference_dir: Path,
    reference_set: Path,
    acceptance_threshold: float = 0.5
    ):

    references = _load_references(reference_dir, reference_set)

    for reference in references:
        reference.update({
            "distance": frame_distance(frame, reference["frame"])
        }
            
    )

    candidate = min(references, key=lambda r: r["distance"])

    if candidate["distance"] < acceptance_threshold:
        tag = candidate["tag"]
    else:
        tag = "Unknown"

    return tag

def annotate_frames_in_intervals(
    frames_in_intervals,
    reference_dir: Path,
    reference_set: Path
    ):

    frames_annotated = []

    for start, end, frame in frames_in_intervals:

        tag = annotate_frame(frame, reference_dir, reference_set)

        frames_annotated.append(
            (start, end, frame, tag)
        )


    return frames_annotated