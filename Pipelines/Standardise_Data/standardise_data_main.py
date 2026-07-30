"""Main script for the Standardise_Data pipeline.

To run this script, use the following command from the project root:
    uv run python -m Pipelines.Standardise_Data.standardise_data_main
"""

## IMPORTS ##
# Internal
from Shared_Functions.logger_functionality import *
from .Functions.standardise_and_combine_transcriptions import standardise_and_combine_transcriptions
from .Functions.standardise_and_combine_mouse_tracking import standardise_and_combine_mouse_tracking
from .Functions.standardise_and_combine_FEA import standardise_and_combine_fea
## _______ ##


## STATIC VARIABLES ##
# Directories - input
INPUT_DIR_TRANSCRIPTIONS_FOLDER = "/work/MP_ACID/Data/raw/iMotions/Audio_PRIMO_resp_transcribed/csv"
INPUT_DIR_MOUSE_TRACKING_FOLDER = "/work/MP_ACID/Data/raw/iMotions/MouseData"
INPUT_DIR_FEA_FOLDER = "/work/MP_ACID/Data/raw/iMotions/FEA/DDD-F2026-RespCam-FEA_PRIMO"

# Directories - internal output
# OUTPUT_DIR_AAA = "Pipelines/Standardise_Data/Data/xxx.zzz"

# Directories - global output
OUTPUT_BASE = "." #"/work/MP_ACID"
OUTPUT_DIR_TRANSCRIPTION_DATA = f"{OUTPUT_BASE}/Data/Standardise_Data/transcriptions.csv"
OUTPUT_DIR_MOUSE_TRACKING_DATA = f"{OUTPUT_BASE}/Data/Standardise_Data/mouse_tracking.csv"
OUTPUT_DIR_FEA_DATA = f"{OUTPUT_BASE}/Data/Standardise_Data/FEA.csv"

# Directories - logs
OUTPUT_DIR_LOG_FULL_PIPELINE = "./Pipelines/Standardise_Data/Logs/full_pipeline.log"
OUTPUT_DIR_LOG_TRANSCRIPTIONS = "./Pipelines/Standardise_Data/Logs/transcriptions.log"
OUTPUT_DIR_LOG_MOUSE_TRACKING = "./Pipelines/Standardise_Data/Logs/mouse_tracking.log"
OUTPUT_DIR_LOG_FEA = "./Pipelines/Standardise_Data/Logs/FEA.log"

# Other
PERCENT_CERTAINTY = 85
## _______________________ ##


## HELPER FUNCTIONS ##
## ________________ ##


## MAIN FUNCTION ##
def main() -> None:
    """Run the full Standardise_Data pipeline."""

    standardise_and_combine_transcriptions(
        input_folder=INPUT_DIR_TRANSCRIPTIONS_FOLDER,
        output_dir=OUTPUT_DIR_TRANSCRIPTION_DATA,
        logger=setup_logger(
            output_dir_log=OUTPUT_DIR_LOG_TRANSCRIPTIONS,
            logger_name="standardise_data.transcriptions",
        ),
    )

    standardise_and_combine_mouse_tracking(
        input_folder=INPUT_DIR_MOUSE_TRACKING_FOLDER,
        output_dir=OUTPUT_DIR_MOUSE_TRACKING_DATA,
        logger=setup_logger(
            output_dir_log=OUTPUT_DIR_LOG_MOUSE_TRACKING,
            logger_name="standardise_data.mouse_tracking",
        ),
    )

    standardise_and_combine_fea(
        input_folder=INPUT_DIR_FEA_FOLDER,
        output_dir=OUTPUT_DIR_FEA_DATA,
        percent_certainty=PERCENT_CERTAINTY,
        logger=setup_logger(
            output_dir_log=OUTPUT_DIR_LOG_FEA,
            logger_name="standardise_data.fea",
        ),
    )

    rebuild_pipeline_log(
        step_log_paths=[
            OUTPUT_DIR_LOG_TRANSCRIPTIONS,
            OUTPUT_DIR_LOG_MOUSE_TRACKING,
            OUTPUT_DIR_LOG_FEA,
        ],
        output_dir_log=OUTPUT_DIR_LOG_FULL_PIPELINE,
    )


## CALL OF MAIN FUNCTION ##
if __name__ == "__main__":
    main()
