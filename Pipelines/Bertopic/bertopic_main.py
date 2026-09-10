"""Main script for the Bertopic pipeline.

To run this script, use the following command from the project root:
    uv run python -m Pipelines.Bertopic.bertopic_main
"""

## IMPORTS ##
# Internal
from Shared_Functions.logger_functionality import *
from .Functions.model_training import train_model
## _______ ##


## STATIC VARIABLES ##
# Directories - input
INPUT_BASE = "."
INPUT_DIR_DATA = f"{INPUT_BASE}/Data/Data_Combination_OLD/combined_data_when_feelings_85.json"

# Directories - internal output
OUTPUT_DIR_TRAINED_MODEL_BASE = "Pipelines/Bertopic/Data/trained_model"
OUTPUT_DIR_VISUALISATIONS_BASE = "Pipelines/Bertopic/Data/visualisations"

# Directories - global output
OUTPUT_BASE = "."
# OUTPUT_DIR_AAA = "./Data/Bertopic/xxx.zzz"

# Directories - logs
OUTPUT_DIR_LOG_FULL_PIPELINE = "./Pipelines/Bertopic/Logs/full_pipeline.log"
OUTPUT_DIR_LOG_1 = "./Pipelines/Bertopic/Logs/train_model.log"

# BERTopic-stuff
STOPWORDS_EXTENSION = [
    'øhh', 'tak', 'thank', 'takk', 'mmm', 
    'okay', 'øhm', 'øh', 'hmm', 'altså',
    'ja', 'nej', 'nope', 'true', 'haha',
    'mmh', 'nå', 'and', 'do', 'hahaha',
    'nååååå', 'hey', 'yes', 
]
# Umap
N_NEIGHBOURS = [10, 15, 20]
N_COMPONENTS = [10, 20]
# HDB
MIN_CLUSTER_SIZE = [20, 30, 40, 50]
MIN_SAMPLES = [5, 10]
# Vectorizer_model
MAX_DF = [0.8]
NGRAM_RANGE = [(1,2)]
## _______________________ ##


## HELPER FUNCTIONS ##
## ________________ ##


## MAIN FUNCTION ##
def main() -> None:
    """Run the full Bertopic pipeline."""
    for n_neighbours in N_NEIGHBOURS:
        for n_components in N_COMPONENTS:
            for min_cluster_size in MIN_CLUSTER_SIZE:
                for min_samples in MIN_SAMPLES:
                    for max_df in MAX_DF:
                        for ngram_range in NGRAM_RANGE:
                            output_dir_model = f'{OUTPUT_DIR_TRAINED_MODEL_BASE}/nn{n_neighbours}_nc{n_components}_mcs{min_cluster_size}_ms{min_samples}_mad{max_df}_ngr{ngram_range}'
                            output_dir_visualisations = f'{OUTPUT_DIR_VISUALISATIONS_BASE}/nn{n_neighbours}_nc{n_components}_mcs{min_cluster_size}_ms{min_samples}_mad{max_df}_ngr{ngram_range}'
                            train_model(
                                input_dir=INPUT_DIR_DATA,
                                stopwords_extension=STOPWORDS_EXTENSION,
                                output_dir_model=output_dir_model,
                                output_dir_visualisations=output_dir_visualisations,
                                n_neighbors=n_neighbours,
                                n_components=n_components,
                                min_cluster_size=min_cluster_size,
                                min_samples=min_samples,
                                max_df=max_df,
                                ngram_range=ngram_range,
                                logger=setup_logger(
                                    output_dir_log=OUTPUT_DIR_LOG_1,
                                    logger_name="bertopic.step_1",
                                    overwrite=False,
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
