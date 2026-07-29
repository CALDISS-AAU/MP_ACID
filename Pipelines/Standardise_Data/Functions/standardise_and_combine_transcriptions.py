"""Helper functions related to transcriptions in the Standardise_Data pipeline."""

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
    """Extracts the group and task numbers from the file name"""
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
    """Adds group and task ids to individual datasets and combines all datasets"""
    logger.info("="*20)
    logger.info("Initiate mission: Combine all transcription datasets into one")
    logger.info("-"*20)

    list_of_dfs = []
    output_path = Path(output_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for file in Path(input_folder).glob("*.csv"):
        group_id, task_id = _extract_group_and_task(file, logger)
        logger.info(f"Adding group id ({group_id}) and task id ({task_id}) to {file}")
        df = pl.read_csv(file)
        df = df.with_columns(
            pl.lit(group_id).alias("group"),
            pl.lit(task_id).alias("task")
        )
        list_of_dfs.append(df)

    df_combined = pl.concat(list_of_dfs)
    df_combined.write_csv(output_dir)

    logger.info("All transcription datasets have been combined into one with the group and task ids as columns")
    logger.info("="*20)