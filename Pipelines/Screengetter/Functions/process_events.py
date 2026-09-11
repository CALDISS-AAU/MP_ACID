"""Main script for the Screengetter pipeline.

To run this script, use the following command from the project root:
    uv run python -m Pipelines.Screengetter.screengetter_main
"""

## IMPORTS ##
import re
import json
from pathlib import Path
import logging

import numpy as np
import polars as pl

# Internal
from .create_reference import create_reference
from .arrays_from_frames import extract_framearrays
from .event_loader import load_events
from .annotate_frames import annotate_frames_in_intervals
from .analyze_frames import analyze_frames

## _______ ##

## STATIC VARIABLES ##
# Filename schema
SCREENREC_FILE_SCHEMA = r"Scene_{GROUP}_{TASK}.PRIMO[-_]RA"

## LOGGER ## 
logger = logging.getLogger(__name__)

## HELPER FUNCTIONS ##
def _get_filename(
    group_name,
    task,
    screenrecs_dir,
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


## MAIN FUNCTION ##
def process_event_data(
    events_df: pl.DataFrame,
    smallest_resolution: dict,
    screenrecs_dir: Path,
    reference_dir: Path, 
    reference_set: Path):
    """
    Processes event data from Data_Combination pipeline. For each event timestamp, 1 frame per second is extracted in the 5 seconds leading up to the event (context settings not currently exposed at higher level function).
    Frames are tagged based on UI location using an annotated reference set.
    """

    group_tasks = dict(events_df.select("group", "task").iter_rows())
    
    processed_events = []
    events_failed = 0

    for group, task in group_tasks.items():

        logger.info(f"Processing events for {group}-{task}")

        try:

            screenrec_filepath, filename_lookup = _get_filename(group, task, screenrecs_dir)

            if not screenrec_filepath:
                logger.error(f"Failed to find video for {group}-{task}. Expected filename to match: {filename_lookup}")
                continue

            logger.info(f"Recording found at {screenrec_filepath}")

            event_timestamps_group_task = events_df.filter(
                (pl.col("group") == group) & 
                (pl.col("task") == task)
            ).get_column("feeling_timestamp").to_list()

            if len(event_timestamps_group_task) == 0:
                logger.warning(f"No events found for {group}-{task}. Continuing...")
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
                reference_dir = reference_dir,
                reference_set = reference_set,
                use_resolution = smallest_resolution
            )

            logger.info("Framearraays annotated")

            combined_entries, group_task_events_failed = _combine_entries(group, task, event_timestamps_group_task, frames_annotated)

            logger.info(f"Processed {len(combined_entries)} frames for {group}-{task}")

            processed_events.extend(combined_entries)
            events_failed += group_task_events_failed

        except Exception as e:
            logger.error(f"Processing failed for {group}-{task} with error: \n {e}")

    return processed_events, events_failed