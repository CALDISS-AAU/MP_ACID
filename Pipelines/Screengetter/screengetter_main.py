"""Main script for the Screengetter pipeline.

To run this script, use the following command from the project root:
    uv run python -m Pipelines.Screengetter.screengetter_main
"""

## IMPORTS ##
import re
import json
from pathlib import Path

import numpy as np

# Internal
from Shared_Functions.logger_functionality import *
from .Functions.create_reference import create_reference
from .Functions.arrays_from_frames import extract_framearrays
from .Functions.event_loader import load_events
from .Functions.annotate_frames import annotate_frames_in_intervals

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
OUTPUT_REFERENCE = OUTPUT_DIR_INT / "Reference2"

# Directories - global output
OUTPUT_BASE = Path(".") / "Data" / "Screengetter"

# Directories - logs
OUTPUT_DIR_LOGS = Path(".") / "Pipelines" / "Screengetter" / "Logs"
OUTPUT_DIR_LOG_FULL_PIPELINE = OUTPUT_DIR_LOGS / "full_pipeline.log"
OUTPUT_DIR_LOG_1 = OUTPUT_DIR_LOGS / "example_1.log"

# Resources
VIDEO_RESOLUTIONS = OUTPUT_REFERENCE / "resolutions.json"
REFERENCE_SET = OUTPUT_REFERENCE / "reference_lookup_tagged.json"

# Filename schema
SCREENREC_FILE_SCHEMA = r"Scene_{GROUP}_{TASK}.PRIMO-RA"

# SEED
SEED_NO = 1789021234

## MOCK DATA ##
event_timestamps = {
    "group": "C4",
    "task": "11",
    "event_ranges": [
        range(115000, 120000),
        range(220000, 230000),
        range(470000, 477000)
    ]
}

## HELPER FUNCTIONS ##
def _read_smallest_resolution(
    input_path = VIDEO_RESOLUTIONS
):
    with open(input_path, "r", encoding="utf-8") as f:
        resolutions = json.load(f)

    smallest = min(resolutions, key=lambda r: r["total"])

    smallest_resolution = {"width": smallest["width"], "height": smallest["height"]}

    return smallest_resolution

def _get_filename(
    group_name,
    task,
    screenrecs_dir: Path = INPUT_DIR_SCREENRECS,
    filename_schema = SCREENREC_FILE_SCHEMA
):
    """Determine filename of screenrecording based on group and task name"""

    filename_stub = filename_schema.format(
        GROUP = group_name,
        TASK = task
    )

    screenrec_filepath = next(screenrecs_dir.glob(f"{filename_stub}*"), None)

    return screenrec_filepath

def _store_framearrays(
    framearrays_in_intervals,
    group_name,
    task, 
    output_frames_maindir = OUTPUT_FRAMEARRAYS
    ):

    output_frames_dir = output_frames_maindir / f"{group_name}_{task}"
    output_frames_dir.mkdir(parents = True, exist_ok=True)

    output_path_meta = output_frames_dir / f"{group_name}_{task}_framearrays_meta.json"

    meta_out = []

    for interval_framearrays in framearrays_in_intervals:
        
        event_start = min([framearray[0] for framearray in interval_framearrays]) # First tuple item is the start of interval. Lowest value corresponds to start of event.
    
        for start, end, framearray in interval_framearrays:

            output_path_framearray = output_frames_dir / f"{start}_{end}.npy"

            np.save(output_path_framearray, framearray)

            meta_entry = {
                "event_start": event_start,
                "interval_start": start, 
                "interval_end": end,
                "framearray_path": str(output_path_framearray)
            }

            meta_out.append(meta_entry)

    with open(output_path_meta, "w", encoding = "utf-8") as output_file:
        json.dump(meta_out, output_file, indent=2)
    

## MAIN FUNCTION ##
def main(input_data = None) -> None:
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
    reference_lookup = json.load(reference_lookup)

    if input_data is None:
        events_df = load_events(input_file = INPUT_EVENTS_PATH)

    group_tasks = zip(events_df.col("group"), events_df.col("task"))

    for group, task in group_tasks.items():

        screenrec_filepath = _get_filename(group, task)

        event_timestamps_group_task = events_df.filter(
            events_df.col("group") == group & 
            events_df.col("task") == task
        ).get_column("feeling_timestamp").to_list()

        framearrays_in_intervals = extract_framearrays(
            screenrec_filepath,
            event_timestamps_group_task,
            freq_per_s = 1,
            standardize_resolution = False
        )

        frames_annotated = annotate_frames_in_intervals(
            framearrays_in_intervals,
            reference_dir = OUTPUT_REFERENCE,
            reference_set = REFERENCE_SET
        )

        # TODO: Store framearrays + dataset of event, start, end, framepath, tag

        #_store_framearrays(
        #    framearrays_in_intervals, 
        #    group, 
        #    task
        #)

        # TODO: Analyze tag function: last tag, change in tag

        # TODO: Disregard last tag == unknown (or all tags unknown?)

        # TODO: Output: Similar output as other pipeline - distribution of UI tags


    
    



## CALL OF MAIN FUNCTION ##
if __name__ == "__main__":
    main()
