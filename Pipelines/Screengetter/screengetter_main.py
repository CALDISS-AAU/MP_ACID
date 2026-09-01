"""Main script for the Screengetter pipeline.

To run this script, use the following command from the project root:
    uv run python -m Pipelines.Screengetter.screengetter_main
"""

## IMPORTS ##
from pathlib import Path
import re
# Internal
#from Shared_Functions.logger_functionality import *
from .Functions.screenshots_from_timeinterval import extract_screenshots

## _______ ##


## STATIC VARIABLES ##
# Directories - input
#INPUT_DIR_RAW = Path("..") / "main_Data" / "raw" / "iMotions"
INPUT_DIR_RAW = Path(".") / "Data" / "raw" / "iMotions"
INPUT_DIR_SCREENRECS = INPUT_DIR_RAW / "ScreenRecordings_PRIMO"

# Directories - internal output
# OUTPUT_DIR_AAA = "Pipelines/Standardise_Data/Data/xxx.zzz"

# Directories - global output
OUTPUT_BASE = Path(".") / "Data" / "Screengetter"

# Directories - logs
OUTPUT_DIR_LOGS = Path(".") / "Pipelines" / "Screengetter" / "Logs"
OUTPUT_DIR_LOG_FULL_PIPELINE = OUTPUT_DIR_LOGS / "full_pipeline.log"
OUTPUT_DIR_LOG_1 = OUTPUT_DIR_LOGS / "example_1.log"

# Filename schema
SCREENREC_FILE_SCHEMA = r"Scene_{GROUP}_{TASK}.PRIMO-RA"


## MOCK DATA ##
event_timestamps = {
    "group": "C4",
    "task": "11",
    "event_timestamps": [
        120000,
        240000.6,
        480000.9
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


## MAIN FUNCTION ##
def main(input_data = event_timestamps) -> None:
    """Run the full Screengetter pipeline."""

    group = input_data.get("group")
    task = input_data.get("task")
    timestamps = input_data.get("event_timestamps")

    screenrec_filepath = _get_filename(group, task)

    timerange = range(timestamps[0]-5000, timestamps[0]+5000)
    
    screenshot, screenshots = extract_screenshots(
        screenrec_filepath,
        timerange,
        freq_per_s = 1
    )
    print(len(screenshots))
    
    screenshot.save("screenshot_test.png")

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
