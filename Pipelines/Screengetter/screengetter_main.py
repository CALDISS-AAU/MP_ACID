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
#from Shared_Functions.logger_functionality import *
from .Functions.check_resolutions import determine_smallest_resolution
from .Functions.arrays_from_frames import extract_framearrays

## _______ ##


## STATIC VARIABLES ##
# Directories - input
#INPUT_DIR_RAW = Path("..") / "main_Data" / "raw" / "iMotions"
INPUT_DIR_RAW = Path(".") / "Data" / "raw" / "iMotions"
INPUT_DIR_SCREENRECS = INPUT_DIR_RAW / "ScreenRecordings_PRIMO"

# Directories - internal output
OUTPUT_DIR_INT = Path(".") / "Pipelines" / "Screengetter" / "Data"
OUTPUT_FRAMEARRAYS = OUTPUT_DIR_INT / "Framearrays"

# Directories - global output
OUTPUT_BASE = Path(".") / "Data" / "Screengetter"

# Directories - logs
OUTPUT_DIR_LOGS = Path(".") / "Pipelines" / "Screengetter" / "Logs"
OUTPUT_DIR_LOG_FULL_PIPELINE = OUTPUT_DIR_LOGS / "full_pipeline.log"
OUTPUT_DIR_LOG_1 = OUTPUT_DIR_LOGS / "example_1.log"

# Resources
VIDEO_RESOLUTIONS = OUTPUT_DIR_INT / "resolutions.json"

# Filename schema
SCREENREC_FILE_SCHEMA = r"Scene_{GROUP}_{TASK}.PRIMO-RA"


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
def main(input_data = event_timestamps) -> None:
    """Run the full Screengetter pipeline."""

    smallest_resolution = determine_smallest_resolution(
        files = list(INPUT_DIR_SCREENRECS.glob("*")),
        output_dir = OUTPUT_DIR_INT,
        replace_resolutions=False
    )

    group = input_data.get("group")
    task = input_data.get("task")
    event_ranges = input_data.get("event_ranges")

    screenrec_filepath = _get_filename(group, task)
    
    framearrays_in_intervals = extract_framearrays(
        screenrec_filepath,
        event_ranges,
        freq_per_s = 1
    )

    _store_framearrays(
        framearrays_in_intervals, 
        group, 
        task
    )


    
    #rebuild_pipeline_log(
    #    step_log_paths=[
    #        OUTPUT_DIR_LOG_1,
    #        OUTPUT_DIR_LOG_2,
    #    ],
    #    output_dir_log=OUTPUT_DIR_LOG_FULL_PIPELINE,
    #)


## CALL OF MAIN FUNCTION ##
if __name__ == "__main__":
    main()
