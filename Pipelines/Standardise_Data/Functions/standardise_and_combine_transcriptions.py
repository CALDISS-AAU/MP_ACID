"""Standardise and combine transcription data for downstream analysis."""

## IMPORTS ##
import logging
from pathlib import Path
import polars as pl
## _______ ##


## HELPER FUNCTIONS ##
def _extract_group_and_task(
    input_file: Path,
    logger: logging.Logger,
) -> tuple[str, str]:
    """Extract the group and task identifiers from the input filename."""
    name = input_file.stem 
    _, group, task = name.split("_")

    logger.info(
        "From %s group (%s) and task (%s) has been extracted",
        input_file,
        group,
        task,
    )

    return group, task

## MAIN FUNCTIONALITY ##
def standardise_and_combine_transcriptions(
    input_folder: str,
    output_dir: str,
    logger: logging.Logger,
) -> None:
    """Standardise and combine transcription CSV files into one dataset."""
    logger.info("="*20)
    logger.info("Initiate mission: Combine all transcription datasets into one")
    logger.info("-"*20)

    list_of_dfs = []
    output_path = Path(output_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for file in Path(input_folder).glob("*.csv"):
        group_id, task_id = _extract_group_and_task(file, logger)
        logger.info(
            (
                "Adding group ID (%s) and task ID (%s) to %s and "
                "converting timestamps from seconds to milliseconds"
            ),
            group_id,
            task_id,
            file,
        )
        df = pl.read_csv(file)
        df = df.with_columns(
            pl.col("start") * 1000,
            pl.col("end") * 1000,
            pl.lit(group_id).alias("group"),
            pl.lit(task_id).alias("task")
        )
        list_of_dfs.append(df)

    df_combined = pl.concat(list_of_dfs)
    df_combined.write_csv(output_dir)

    logger.info(
        (
            "All transcription datasets have been combined into one with "
            "the group and task ids as columns"
        )
    )
    logger.info("="*20)