"""Example helper functions for the pipeline."""

## IMPORTS ##
import logging
import polars as pl
## _______ ##


## HELPER FUNCTIONS ##
def _extract_feeling_timestamps(
    input_dir: str,
    relevant_feelings: list[str],
    logger: logging.Logger,
) -> pl.DataFrame:
    events = (
        pl.read_csv(input_dir)
        .filter(pl.any_horizontal(pl.col(relevant_feelings) == 1))
        .select("group", "task", "Timestamp")
    )

    logger.info("Extracted %d timestamp rows based on feelings", events.height)
    return events


## MAIN FUNCTIONALITY ##
def extract_and_combine(
    input_dir_fea_data: str,
    input_dir_transcription_data: str,
    relevant_feelings: list[str],
    logger: logging.Logger,
) -> pl.DataFrame:
    events = _extract_feeling_timestamps(
        input_dir=input_dir_fea_data, 
        relevant_feelings=relevant_feelings, 
        logger=logger
    )

    return events