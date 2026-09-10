"""Main script for the Event_Statistics pipeline.

To run this script, use the following command from the project root:
    uv run python -m Pipelines.Event_Statistics.event_statistics_main
"""

## IMPORTS ##
# Internal
from Shared_Functions.logger_functionality import *
from .Functions.generate_plots import generate_plots
from .Functions.confirm_feeling_events import feeling_confirmation
## _______ ##


## STATIC VARIABLES ##
# Directories - input
INPUT_DIR_FEA = "./Data/Standardise_Data/FEA_75.csv"
INPUT_DIR_MANUAL_REGISTRATIONS = "/work/MP_ACID/Data/raw/iMotions/manually_marked_events.csv"

# Directories - internal output
# OUTPUT_DIR_AAA = "Pipelines/Event_Statistics/Data/xxx.zzz"

# Directories - global output
OUTPUT_DIR_BASE = '.'
OUTPUT_PATH_STATISTICS_FOLDER = f"{OUTPUT_DIR_BASE}/Data/Event_Statistics"
OUTPUT_DIR_FEELING_EVENT_CONFIRMATION = f"{OUTPUT_DIR_BASE}/Data/Event_Statistics"

# Directories - logs
OUTPUT_DIR_LOG_FULL_PIPELINE = "./Pipelines/Event_Statistics/Logs/full_pipeline.log"
OUTPUT_DIR_LOG_1 = "./Pipelines/Event_Statistics/Logs/plot_generation.log"
OUTPUT_DIR_LOG_2 = "./Pipelines/Event_Statistics/Logs/confirm_feeling_events.log"

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

    feeling_confirmation(
        input_dir_manual=INPUT_DIR_MANUAL_REGISTRATIONS,
        input_dir_machine=INPUT_DIR_FEA,
        output_dir=OUTPUT_DIR_FEELING_EVENT_CONFIRMATION,
        logger=setup_logger(
            output_dir_log=OUTPUT_DIR_LOG_2,
            logger_name="event_statistics.step_2",
        ),
    )

    rebuild_pipeline_log(
        step_log_paths=[
            OUTPUT_DIR_LOG_1,
            OUTPUT_DIR_LOG_2,
        ],
        output_dir_log=OUTPUT_DIR_LOG_FULL_PIPELINE,
    )


## CALL OF MAIN FUNCTION ##
if __name__ == "__main__":
    main()
