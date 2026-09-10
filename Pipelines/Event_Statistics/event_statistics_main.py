"""Main script for the Event_Statistics pipeline.

To run this script, use the following command from the project root:
    uv run python -m Pipelines.Event_Statistics.event_statistics_main
"""

## IMPORTS ##
# Internal
from Shared_Functions.logger_functionality import *
from .Functions.generate_plots import generate_plots
## _______ ##


## STATIC VARIABLES ##
# Directories - input
INPUT_DIR_FEA = "./Data/Standardise_Data/FEA_85.csv"

# Directories - internal output
# OUTPUT_DIR_AAA = "Pipelines/Event_Statistics/Data/xxx.zzz"

# Directories - global output
OUTPUT_DIR_BASE = '.'
OUTPUT_PATH_STATISTICS_FOLDER = f"{OUTPUT_DIR_BASE}/Data/Event_Statistics"

# Directories - logs
OUTPUT_DIR_LOG_FULL_PIPELINE = "./Pipelines/Event_Statistics/Logs/full_pipeline.log"
OUTPUT_DIR_LOG_1 = "./Pipelines/Event_Statistics/Logs/plot_generation.log"
# OUTPUT_DIR_LOG_2 = "./Pipelines/Event_Statistics/Logs/example_2.log"

## _______________________ ##


## HELPER FUNCTIONS ##
## ________________ ##


## MAIN FUNCTION ##
def main() -> None:
    """Run the full Event_Statistics pipeline."""

    generate_plots(
        input_dir=INPUT_DIR_FEA,
        output_path=OUTPUT_PATH_STATISTICS_FOLDER,
        logger=setup_logger(
            output_dir_log=OUTPUT_DIR_LOG_1,
            logger_name="event_statistics.step_1",
        ),
    )

    # example_function(
    #     input_str="World!",
    #     logger=setup_logger(
    #         output_dir_log=OUTPUT_DIR_LOG_2,
    #         logger_name="event_statistics.step_2",
    #     ),
    # )

    rebuild_pipeline_log(
        step_log_paths=[
            OUTPUT_DIR_LOG_1,
            # OUTPUT_DIR_LOG_2,
        ],
        output_dir_log=OUTPUT_DIR_LOG_FULL_PIPELINE,
    )


## CALL OF MAIN FUNCTION ##
if __name__ == "__main__":
    main()
