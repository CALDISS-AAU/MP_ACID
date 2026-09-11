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

# Directories - logs
OUTPUT_DIR_LOGS = Path(".") / "Pipelines" / "Screengetter" / "Logs"
OUTPUT_DIR_LOG_FULL_PIPELINE = OUTPUT_DIR_LOGS / "full_pipeline.log"
OUTPUT_DIR_LOG_1 = OUTPUT_DIR_LOGS / "example_1.log"

# Resources
VIDEO_RESOLUTIONS = OUTPUT_REFERENCE / "resolutions.json"
REFERENCE_SET = OUTPUT_REFERENCE / "reference_lookup_tagged.json"

# Filename schema
SCREENREC_FILE_SCHEMA = r"Scene_{GROUP}_{TASK}.PRIMO[-_]RA"

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
        TASK = f"{int(task):02d}"
    )
    screenrec_filepath = next(screenrecs_dir.glob(f"{filename_stub}*"), None)

    return screenrec_filepath, filename_stub

def _combine_entries(group, task, event_timestamps, annotated_frames):

    entries = []
    timestamps_failed = 0

    for timestamp, frame_data in dict(zip(event_timestamps, annotated_frames)).items():

        n_frames_failed = sum([frame is None for start, end, frame, tag in frame_data])
        all_failed = int((n_frames_failed / len(frame_data)) == 1)
        
        for start, end, frame, tag in frame_data:
            combined_entry = {
                "group": group,
                "task": task, 
                "feeling_timestamp": timestamp,
                "frame_start": start, 
                "frame_end": end, 
                "frame": frame,
                "tag": tag
            }
        
        entries.append(combined_entry)
        timestamps_failed += all_failed
    
    return entries, timestamps_failed


def _store_framearrays(
    processed_events: list[dict],
    output_frames_dir: Path = OUTPUT_FRAMEARRAYS
    ):

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
    
    if input_data is None:
        events_df = load_events(input_file = INPUT_EVENTS_PATH)

    group_tasks = dict(events_df.select("group", "task").iter_rows())
    
    processed_events = []
    events_failed = 0

    for group, task in group_tasks.items():

        logger.info(f"Processing events for {group}-{task}")

        try:

            screenrec_filepath, filename_lookup = _get_filename(group, task)

            if not screenrec_filepath:
                logger.error(f"Failed to find video for {group}-{task}. Expected filename to match: {filename_lookup}")
                continue

            logger.info(f"Recording found at {screenrec_filepath}")

            event_timestamps_group_task = events_df.filter(
                (pl.col("group") == group) & 
                (pl.col("task") == task)
            ).get_column("feeling_timestamp").to_list()

            if len(event_timestamps_group_task) == 0:
                logging.warning(f"No events found for {group}-{task}. Continuing...")
                continue

            logger.info(f"{len(event_timestamps_group_task)} events loaded for file {screenrec_filepath}")

            framearrays_in_intervals = extract_framearrays(
                screenrec_filepath,
                event_timestamps_group_task,
                freq_per_s = 1,
                standardize_resolution = False
            )

            logger.info("Framearrays extracted")

            frames_annotated = annotate_frames_in_intervals(
                framearrays_in_intervals,
                reference_dir = OUTPUT_REFERENCE,
                reference_set = REFERENCE_SET,
                use_resolution = smallest_resolution
            )

            logger.info("Framearraays annotated")

            combined_entries, group_task_events_failed = _combine_entries(group, task, event_timestamps_group_task, frames_annotated)

            logger.info(f"Processed {len(combined_entries)} frames for {group}-{task}")

            processed_events.extend(combined_entries)
            events_failed += group_task_events_failed

        except Exception as e:
            logger.error(f"Processing failed for {group}-{task} with error: \n {e}")

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
        output_path_meta
    )


## CALL OF MAIN FUNCTION ##
if __name__ == "__main__":
    main()
