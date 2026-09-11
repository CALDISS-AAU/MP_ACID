"""Main script for the Screengetter pipeline.

To run this script, use the following command from the project root:
    uv run python -m Pipelines.Screengetter.screengetter_main
"""

## IMPORTS ##
import re
import json
from pathlib import Path

import numpy as np
import polars as pl

# Internal
from Shared_Functions.logger_functionality import *
from .Functions.create_reference import create_reference
from .Functions.arrays_from_frames import extract_framearrays
from .Functions.event_loader import load_events
from .Functions.annotate_frames import annotate_frames_in_intervals
from .Functions.analyze_frames import analyze_frames
from .Functions.process_events import process_event_data

## _______ ##


## STATIC VARIABLES ##
# Directories - input
INPUT_DIR_DATA = Path(".") / "Data"
INPUT_DIR_RAW = INPUT_DIR_DATA / "raw" / "iMotions"
INPUT_DIR_SCREENRECS = INPUT_DIR_RAW / "ScreenRecordings_PRIMO"
INPUT_EVENTS_PATH = INPUT_DIR_DATA / "Data_Combination" / "combined_data_when_feelings_pc85_pre0_post0.csv"

# Directories - internal output
OUTPUT_DIR_INT = Path(".") / "Pipelines" / "Screengetter" / "Data"
OUTPUT_FRAMEARRAYS = OUTPUT_DIR_INT / "Framearrays"
OUTPUT_REFERENCE = OUTPUT_DIR_INT / "Reference"

# Directories - global output
OUTPUT_BASE = Path(".") / "Data" / "Screengetter"
OUTPUT_RESULTS = Path(".") / "Output/" / "Screengetter"

# Directories - logs
OUTPUT_DIR_LOGS = Path(".") / "Pipelines" / "Screengetter" / "Logs"
OUTPUT_DIR_LOG_FULL_PIPELINE = OUTPUT_DIR_LOGS / "full_pipeline.log"
OUTPUT_DIR_LOG_1 = OUTPUT_DIR_LOGS / "example_1.log"

# Resources
VIDEO_RESOLUTIONS = OUTPUT_REFERENCE / "resolutions.json"
REFERENCE_SET = OUTPUT_REFERENCE / "reference_lookup_tagged.json"

# SEED
SEED_NO = 1789021234


## HELPER FUNCTIONS ##
def _read_smallest_resolution(
    input_path = VIDEO_RESOLUTIONS
    ):
    """Reads the smallest resolution from the reference material. Used to standardize resolution between input and reference data"""
    
    with open(input_path, "r", encoding="utf-8") as f:
        resolutions = json.load(f)

    smallest = min(resolutions, key=lambda r: r["total"])

    smallest_resolution = {"width": smallest["width"], "height": smallest["height"]}

    return smallest_resolution

def _store_framearrays(
    processed_events: list[dict],
    output_frames_dir: Path = OUTPUT_FRAMEARRAYS
    ):
    """Stores frames of processed events as numpy arrays. A json with metadata for all events are created with path for each .npy file stored"""

    output_path_meta = output_frames_dir / "event_frames_meta.json"

    for event_dict in processed_events:
        
        frame = event_dict.pop("frame")

        if frame is not None:

            frame_arary_output_name = f'{event_dict["group"]}-{event_dict["task"]}_{event_dict["frame_start"]}-{event_dict["frame_end"]}.npy'
            frame_arary_output_path = output_frames_dir / frame_arary_output_name

            np.save(frame_arary_output_path, frame)

            event_dict.update({
                "framearray_path": frame_arary_output_name
            })

    with open(output_path_meta, "w", encoding = "utf-8") as output_file:
        json.dump(processed_events, output_file, indent=2)
    
    return output_path_meta

## MAIN FUNCTION ##
def main() -> None:
    """Run the full Screengetter pipeline."""

    logger = setup_logger(
            output_dir_log=OUTPUT_DIR_LOG_FULL_PIPELINE,
            logger_name="Pipelines.Screengetter",
        )
    for handler in logger.handlers:
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )

    if not REFERENCE_SET.is_file():
        logger.info(f"No reference set found at path {REFERENCE_SET}. New reference set to be created at dir {OUTPUT_REFERENCE}.")
        create_reference(
            input_dir = INPUT_DIR_SCREENRECS,
            output_dir = OUTPUT_REFERENCE,
            seed_use = SEED_NO
        )
        logger.info(f"New reference set created at {OUTPUT_REFERENCE}. Please provide manual annotations of the reference images using the JSON key 'tag': >tag< and store at path {REFERENCE_SET}. Then re-run the workflow.")
        
        return

    smallest_resolution = _read_smallest_resolution(VIDEO_RESOLUTIONS)
    
    events_df = load_events(input_file = INPUT_EVENTS_PATH)

    processed_events, events_failed = process_event_data(
        events_df,
        smallest_resolution,
        screenrecs_dir=INPUT_DIR_SCREENRECS,
        reference_dir=OUTPUT_REFERENCE,
        reference_set=REFERENCE_SET
    )

    logger.info(f"Storing {len(processed_events)-events_failed} tagged events to {OUTPUT_FRAMEARRAYS}. {events_failed} failed.")

    try:        
        output_path_meta = _store_framearrays(
            processed_events,
            OUTPUT_FRAMEARRAYS
        )
    except Exception as e:
        logger.error(f"Failed to store processed events to {OUTPUT_FRAMEARRAYS} with error: \n {e}")

    logger.info(f"Processed events saved to {OUTPUT_FRAMEARRAYS}")

    analyze_frames(
        OUTPUT_FRAMEARRAYS,
        output_path_meta,
        OUTPUT_RESULTS
    )


## CALL OF MAIN FUNCTION ##
if __name__ == "__main__":
    main()
