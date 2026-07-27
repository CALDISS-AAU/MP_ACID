"""Main script for the Example_Pipeline pipeline.

To run this script, use the following command from the project root:
    uv run python -m Pipelines.Example_Pipeline.example_pipeline_main
"""

## IMPORTS ##
# Internal
from Shared_Functions.logger_functionality import *
from .Functions.example_functions_script import example_function
## _______ ##


## STATIC VARIABLES ##
# Directories - input
# INPUT_DIR_AAA = "xxx/yyy.zzz"

# Directories - internal output
# OUTPUT_DIR_AAA = "Pipelines/Example_Pipeline/Data/xxx.zzz"

# Directories - global output
# OUTPUT_DIR_AAA = "./Data/Example_Pipeline/xxx.zzz"

# Directories - logs
OUTPUT_DIR_LOG_FULL_PIPELINE = "./Pipelines/Example_Pipeline/Logs/full_pipeline.log"
OUTPUT_DIR_LOG_1 = "./Pipelines/Example_Pipeline/Logs/example_1.log"
OUTPUT_DIR_LOG_2 = "./Pipelines/Example_Pipeline/Logs/example_2.log"

## _______________________ ##


## HELPER FUNCTIONS ##
## ________________ ##


## MAIN FUNCTION ##
def main() -> None:
    """Run the full Example_Pipeline pipeline."""

    example_function(
        input_str="Hello",
        logger=setup_logger(
            output_dir_log=OUTPUT_DIR_LOG_1,
            logger_name="example_pipeline.step_1",
        ),
    )

    example_function(
        input_str="World!",
        logger=setup_logger(
            output_dir_log=OUTPUT_DIR_LOG_2,
            logger_name="example_pipeline.step_2",
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
