"""Main script for the Feelings_Investigation pipeline.

To run this script, use the following command from the project root:
    uv run python -m Pipelines.Feelings_Investigation.feelings_investigation_main
"""

## IMPORTS ##
# Standard
from pathlib import Path
# Internal
from Shared_Functions.logger_functionality import *
from .Functions.plots import *
## _______ ##


## STATIC VARIABLES ##
# Directories - input
INPUT_BASE = "."
INPUT_DIR_FEA_DATA_FOLDER = f"{INPUT_BASE}/Data/Standardise_Data"
INPUT_FILE_PATTERN = "FEA_*.csv"

# Directories - internal output
OUTPUT_DIR_PLOTS_FOLDER = "Pipelines/Feelings_Investigation/Data/Plots/Graphs"

# Directories - global output
# OUTPUT_DIR_AAA = "./Data/Feelings_Investigation/xxx.zzz"

# Directories - logs
OUTPUT_DIR_LOG_FULL_PIPELINE = "./Pipelines/Feelings_Investigation/Logs/full_pipeline.log"
OUTPUT_DIR_LOG_PLOTS = "./Pipelines/Feelings_Investigation/Logs/plots.log"
# OUTPUT_DIR_LOG_2 = "./Pipelines/Feelings_Investigation/Logs/example_2.log"

# Other
feeling_cols = [
    "Anger",
    "Contempt",
    "Confusion",
    "Disgust",
    "Engagement",
    "Fear",
    "Joy",
    "Sadness",
    "Surprise",
]

## _______________________ ##


## HELPER FUNCTIONS ##
## ________________ ##


## MAIN FUNCTION ##
def main() -> None:
    """Run the full Feelings_Investigation pipeline."""

    input_files = list(
        Path(INPUT_DIR_FEA_DATA_FOLDER).glob(INPUT_FILE_PATTERN)
    )

    logger_plots=setup_logger(
        output_dir_log=OUTPUT_DIR_LOG_PLOTS,
        logger_name="feelings_investigation.plots",
    )

    for file in input_files:
        feeling_vs_time_graph(
            input_file=file,
            output_folder=OUTPUT_DIR_PLOTS_FOLDER,
            feeling_cols=feeling_cols,
            logger=logger_plots,
        )

    rebuild_pipeline_log(
        step_log_paths=[
            OUTPUT_DIR_LOG_PLOTS,
        ],
        output_dir_log=OUTPUT_DIR_LOG_FULL_PIPELINE,
    )


## CALL OF MAIN FUNCTION ##
if __name__ == "__main__":
    main()
