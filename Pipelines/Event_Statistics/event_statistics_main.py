"""Main script for the Event_Statistics pipeline.

To run this script, use the following command from the project root:
    uv run python -m Pipelines.Event_Statistics.event_statistics_main
"""

## IMPORTS ##
# Internal
from Shared_Functions.logger_functionality import *

from .Functions.confirm_feeling_events import feeling_confirmation
from .Functions.generate_plots import generate_plots
from .Functions.generate_table import generate_table
## _______ ##


## STATIC VARIABLES ##
# Directories - input
INPUT_DIR_FEA = "./Data/Standardise_Data/FEA_85.csv"
INPUT_DIR_MANUAL_REGISTRATIONS = (
    "/work/MP_ACID/Data/raw/iMotions/manually_marked_events.csv"
)

# Directories - internal output
# OUTPUT_DIR_AAA = "Pipelines/Event_Statistics/Data/xxx.zzz"

# Directories - global output
OUTPUT_DIR_BASE = "./Output"
OUTPUT_PATH_STATISTICS_FOLDER = (
    f"{OUTPUT_DIR_BASE}/Event_Statistics"
)
OUTPUT_DIR_FEELING_EVENT_CONFIRMATION = (
    f"{OUTPUT_DIR_BASE}/Event_Statistics"
)

# Directories - logs
OUTPUT_DIR_LOG_FULL_PIPELINE = (
    "./Pipelines/Event_Statistics/Logs/full_pipeline.log"
)
OUTPUT_DIR_LOG_TABLE = (
    "./Pipelines/Event_Statistics/Logs/table_generation.log"
)
OUTPUT_DIR_LOG_PLOTS = (
    "./Pipelines/Event_Statistics/Logs/plot_generation.log"
)
OUTPUT_DIR_LOG_CONFIRMATION = (
    "./Pipelines/Event_Statistics/Logs/confirm_feeling_events.log"
)

# Other
FEELING_COLUMNS = [
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

PLOT_FEELING_COLUMNS = [
    feeling
    for feeling in FEELING_COLUMNS
    if feeling not in {
        "Joy",
        "Engagement",
    }
]

CONFIRMATION_TIME_WINDOW_MS = 5_000
## _______________________ ##


## HELPER FUNCTIONS ##
## ________________ ##


## MAIN FUNCTION ##
def main() -> None:
    """Run the full Event_Statistics pipeline."""
    generate_table(
        input_dir=INPUT_DIR_FEA,
        output_path=OUTPUT_PATH_STATISTICS_FOLDER,
        feeling_cols=FEELING_COLUMNS,
        logger=setup_logger(
            output_dir_log=OUTPUT_DIR_LOG_TABLE,
            logger_name="event_statistics.table_generation",
        ),
    )

    generate_plots(
        input_dir=INPUT_DIR_FEA,
        output_path=OUTPUT_PATH_STATISTICS_FOLDER,
        plot_feeling_cols=PLOT_FEELING_COLUMNS,
        logger=setup_logger(
            output_dir_log=OUTPUT_DIR_LOG_PLOTS,
            logger_name="event_statistics.plot_generation",
        ),
    )

    feeling_confirmation(
        input_dir_manual=INPUT_DIR_MANUAL_REGISTRATIONS,
        input_dir_machine=INPUT_DIR_FEA,
        output_dir=OUTPUT_DIR_FEELING_EVENT_CONFIRMATION,
        feeling_cols=PLOT_FEELING_COLUMNS,
        time_window_ms=CONFIRMATION_TIME_WINDOW_MS,
        logger=setup_logger(
            output_dir_log=OUTPUT_DIR_LOG_CONFIRMATION,
            logger_name="event_statistics.feeling_confirmation",
        ),
    )

    rebuild_pipeline_log(
        step_log_paths=[
            OUTPUT_DIR_LOG_TABLE,
            OUTPUT_DIR_LOG_PLOTS,
            OUTPUT_DIR_LOG_CONFIRMATION,
        ],
        output_dir_log=OUTPUT_DIR_LOG_FULL_PIPELINE,
    )


## CALL OF MAIN FUNCTION ##
if __name__ == "__main__":
    main()
