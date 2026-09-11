"""LPIPS perceptual distance for OpenCV BGR video frames."""

## IMPORTS ##
from functools import lru_cache
from math import isfinite
import logging

import cv2
import numpy as np

## LOGGER ## 
logger = logging.getLogger(__name__)

## HELPER FUNCTIONS ##
@lru_cache(maxsize=1)
def _load_model():
    # Load weights only when a comparison is needed.
    import lpips
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    return lpips.LPIPS(net="alex", verbose=False).to(device).eval(), device


def _prepare_frame(frame: np.ndarray) -> np.ndarray:
    """Return RGB float32 NCHW data in [-1, 1], keeping the full frame."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb = cv2.resize(rgb, (224, 224), interpolation=cv2.INTER_AREA)
    normalized = rgb.astype(np.float32) / 127.5 - 1.0
    return np.ascontiguousarray(normalized.transpose(2, 0, 1)[None])


## MAIN FUNCTIONALITY ##
def frame_distance(
    frame: np.ndarray,
    reference_frame: np.ndarray
):
    """Return LPIPS distance.

    Inputs are uint8 BGR frames. Comparisons use the full image resized to 224x224.
    Higher thresholds reject more frames. Pretrained AlexNet weights download
    on first comparison unless cached locally; the model is reused thereafter.
    """

    import torch

    model, device = _load_model()
    candidate = torch.from_numpy(_prepare_frame(frame)).to(device)
    reference = torch.from_numpy(_prepare_frame(reference_frame)).to(device)
    with torch.inference_mode():
        distance = model(candidate, reference).item()
    if not isfinite(distance):
        raise ValueError("LPIPS returned a non-finite distance")

    return distance


def frames_are_not_similar(
    frame: np.ndarray,
    reference_frame: np.ndarray,
    similarity_threshold: float = 0.1
) -> bool:
    """Return whether LPIPS distance exceeds the threshold (equality is a match).

    Inputs are uint8 BGR frames. Comparisons use the full image resized to 224x224.
    Higher thresholds reject more frames. Pretrained AlexNet weights download
    on first comparison unless cached locally; the model is reused thereafter.
    """

    distance = frame_distance(frame, reference_frame)

    return distance > similarity_threshold


def frames_are_similar(
    frame: np.ndarray,
    retained_frame: np.ndarray,
    similarity_threshold: float = 0.1
) -> bool:
    """Return whether LPIPS distance is below the threshold (equality is a match).

    Inputs are uint8 BGR frames. Comparisons use the full image resized to 224x224.
    Higher thresholds reject more frames. Pretrained AlexNet weights download
    on first comparison unless cached locally; the model is reused thereafter.
    """

    return not frames_are_not_similar(frame, retained_frame, similarity_threshold)


def frames_are_similar_pixeldif(frame1, frame2, tolerance_pct = 10):
    """Determine whether two frames are near identical based on tolerance_pct (% pixels allowed to deviate)"""
    
    pixels_differ = np.any(frame1 != frame2, axis=2)

    diff_pct = pixels_differ.mean() * 100

    below_tolerance = diff_pct < tolerance_pct

    return below_tolerance