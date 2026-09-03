"""Main script for the Bertopic pipeline.

To run this script, use the following command from the project root:
    uv run python -m Pipelines.Bertopic.bertopic_main
"""

## IMPORTS ##
# Internal
from Shared_Functions.logger_functionality import *
from .Functions.model_training import train_model
from .Functions.model_reduction import reduce_model
from .Functions.model_validation import validate_model
## _______ ##


## STATIC VARIABLES ##
# Directories - input
INPUT_BASE = "."
INPUT_DIR_DATA = f"{INPUT_BASE}/Data/Data_Combination/combined_data_when_feelings_85.json"

# Directories - internal output
OUTPUT_DIR_TRAINED_MODEL = "Pipelines/Bertopic/Data/85/trained_model"
OUTPUT_DIR_VISUALISATIONS = "Pipelines/Bertopic/Data/85/visualisations"

# Directories - global output
OUTPUT_BASE = "."
# OUTPUT_DIR_AAA = "./Data/Bertopic/xxx.zzz"

# Directories - logs
OUTPUT_DIR_LOG_FULL_PIPELINE = "./Pipelines/Bertopic/Logs/full_pipeline.log"
OUTPUT_DIR_LOG_1 = "./Pipelines/Bertopic/Logs/train_model.log"
OUTPUT_DIR_LOG_2 = "./Pipelines/Bertopic/Logs/reduce_model.log"
OUTPUT_DIR_LOG_3 = "./Pipelines/Bertopic/Logs/validate_model.log"

# Other
stopwords_extention = [
    'øhh', 'tak', 'thank', 'takk', 'mmm', 
    'okay', 'øhm', 'øh', 'hmm', 'altså',
    'ja', 'nej', 'nope', 'true', 'haha',
]
## _______________________ ##


## HELPER FUNCTIONS ##
## ________________ ##


## MAIN FUNCTION ##
def main() -> None:
    """Run the full Bertopic pipeline."""

    train_model(
        input_dir=INPUT_DIR_DATA,
        stopwords_extention=stopwords_extention,
        output_dir_model=OUTPUT_DIR_TRAINED_MODEL,
        output_dir_visualisations=OUTPUT_DIR_VISUALISATIONS,
        logger=setup_logger(
            output_dir_log=OUTPUT_DIR_LOG_1,
            logger_name="bertopic.step_1",
        ),
    )

    # validate_model(
    #     input_dir_data=INPUT_DIR_DATA,
    #     input_dir_model=OUTPUT_DIR_TRAINED_MODEL,
    #     logger=setup_logger(
    #         output_dir_log=OUTPUT_DIR_LOG_3,
    #         logger_name="bertopic.step_3",
    #     ),
    # )

    rebuild_pipeline_log(
        step_log_paths=[
            OUTPUT_DIR_LOG_1,
            # OUTPUT_DIR_LOG_2,
            # OUTPUT_DIR_LOG_3,
        ],
        output_dir_log=OUTPUT_DIR_LOG_FULL_PIPELINE,
    )


## CALL OF MAIN FUNCTION ##
if __name__ == "__main__":
    main()
