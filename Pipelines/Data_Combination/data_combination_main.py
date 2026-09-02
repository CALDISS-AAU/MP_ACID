"""Main script for the Data_Combination pipeline.

To run this script, use the following command from the project root:
    uv run python -m Pipelines.Data_Combination.data_combination_main
"""

## IMPORTS ##
# Internal
from Shared_Functions.logger_functionality import *
from .Functions.extract_and_combine import extract_and_combine
## _______ ##


## STATIC VARIABLES ##
# Directories - input
INPUT_DIR_BASE = "."
INPUT_DIR_FEA_DATA = f"{INPUT_DIR_BASE}/Data/Standardise_Data/FEA_85.csv"
INPUT_DIR_TRANSCRIPTION_DATA = f"{INPUT_DIR_BASE}/Data/Standardise_Data/transcriptions.csv"
INPUT_DIR_MOUSE_DATA = f"{INPUT_DIR_BASE}/Data/Standardise_Data/mouse_tracking.csv"

# Directories - internal output
# OUTPUT_DIR_AAA = "Pipelines/Data_Combination/Data/xxx.zzz"

# Directories - global output
# OUTPUT_DIR_AAA = "./Data/Data_Combination/xxx.zzz"

# Directories - logs
OUTPUT_DIR_LOG_FULL_PIPELINE = "./Pipelines/Data_Combination/Logs/full_pipeline.log"
OUTPUT_DIR_LOG_1 = "./Pipelines/Data_Combination/Logs/extract_feelings_timestamp.log"

# Other
feeling_cols = [
    "Anger",
    "Contempt",
    "Confusion",
    "Disgust",
    # "Engagement",
    "Fear",
    # "Joy",
    "Sadness",
    "Surprise",
]

## _______________________ ##


## HELPER FUNCTIONS ##
## ________________ ##


## MAIN FUNCTION ##
def main() -> None:
    """Run the full Data_Combination pipeline."""

    timestamps = extract_and_combine(
        input_dir_fea_data=INPUT_DIR_FEA_DATA,
        input_dir_transcription_data=INPUT_DIR_TRANSCRIPTION_DATA,
        input_dir_mouse_data=INPUT_DIR_MOUSE_DATA,
        relevant_feelings=feeling_cols,
        logger=setup_logger(
            output_dir_log=OUTPUT_DIR_LOG_1,
            logger_name="data_combination.step_1",
        ),
    )

    rebuild_pipeline_log(
        step_log_paths=[
            OUTPUT_DIR_LOG_1,
        ],
        output_dir_log=OUTPUT_DIR_LOG_FULL_PIPELINE,
    )


## CALL OF MAIN FUNCTION ##
if __name__ == "__main__":
    main()
