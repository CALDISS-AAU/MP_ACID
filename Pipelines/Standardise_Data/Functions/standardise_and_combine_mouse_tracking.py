"""Helper functions related to mouse tracking in the Standardise_Data pipeline."""

## IMPORTS ##
import logging
from pathlib import Path
import polars as pl
## _______ ##


## HELPER FUNCTIONS ##
def _extract_group(
    input_file: Path,
    logger: logging.Logger,
) -> str:
    """Extract the participant/group ID from the iMotions metadata."""

    with input_file.open("r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#Respondent Name,"):
                group = line.split(",")[1].strip()

                logger.info(
                    "From %s group (%s) has been extracted",
                    input_file,
                    group,
                )

                return group

    raise ValueError(f"Could not find '#Respondent Name' in {input_file}")

def _reduce_to_tasks(
    df: pl.DataFrame,
    logger: logging.Logger,
) -> pl.DataFrame:
    """Keep rows between StartMedia and EndMedia, inclusive."""

    original_row_count = df.height
    kept_rows = []
    inside_task = False

    for row in df.iter_rows(named=True):
        slide_event = row["SlideEvent"]

        if slide_event == "StartMedia":
            if inside_task:
                logger.warning(
                    "Found StartMedia before the previous task ended"
                )

            inside_task = True

        elif slide_event == "EndMedia" and not inside_task:
            logger.warning(
                "Found EndMedia without a preceding StartMedia"
            )
            continue

        if inside_task:
            kept_rows.append(row)

        if slide_event == "EndMedia":
            inside_task = False

    if inside_task:
        logger.warning(
            "The dataset ended before the final task reached EndMedia"
        )

    df_tasks = pl.DataFrame(
        kept_rows,
        schema=df.schema,
    )

    logger.info(
        "Reduced dataframe from %d to %d rows by retaining task intervals",
        original_row_count,
        df_tasks.height,
    )

    return df_tasks

def _add_task_id(
    df: pl.DataFrame,
    logger: logging.Logger,
) -> pl.DataFrame:
    """Extract the task ID from the SourceStimuliName column."""

    df = df.with_columns(
        pl.col("SourceStimuliName")
        .str.extract(r"^(\d+)\.", group_index=1)
        .alias("task")
    )

    logger.info("Added task IDs from SourceStimuliName")

    return df

def _reset_time(
    df: pl.DataFrame,
    logger: logging.Logger,
) -> pl.DataFrame:
    """Reset the timestamp so each task starts at 0 ms."""

    # Log the original task intervals
    task_intervals = (
        df.group_by("task")
        .agg(
            pl.col("Timestamp").min().alias("original_start"),
            pl.col("Timestamp").max().alias("original_end"),
        )
        .sort("task")
    )

    for row in task_intervals.iter_rows(named=True):
        logger.info(
            "Task %s: original [%d - %d] ms",
            row["task"],
            row["original_start"],
            row["original_end"],
        )

    # Reset timestamps
    df = df.with_columns(
        (
            pl.col("Timestamp")
            - pl.col("Timestamp").min().over("task")
        ).alias("Timestamp")
    )

    # Log the new task intervals
    task_intervals = (
        df.group_by("task")
        .agg(
            pl.col("Timestamp").min().alias("new_start"),
            pl.col("Timestamp").max().alias("new_end"),
        )
        .sort("task")
    )

    for row in task_intervals.iter_rows(named=True):
        logger.info(
            "Task %s: new [%d - %d] ms",
            row["task"],
            row["new_start"],
            row["new_end"],
        )

    return df

def _remove_irrelevant_cols(
    df: pl.DataFrame,
    logger: logging.Logger,
) -> pl.DataFrame:
    """Keep only columns required for downstream event analysis."""

    relevant_cols = [
        "Timestamp",
        "group",
        "task",
        # "SlideEvent", # Indicates start and end of task
        "InputEventSource",
        "Data",
    ]

    irrelevant_cols = [
        col
        for col in df.columns
        if col not in relevant_cols
    ]

    df = df.select(relevant_cols)

    logger.info(
        "Removed %d irrelevant columns: %s",
        len(irrelevant_cols),
        ", ".join(irrelevant_cols),
    )

    logger.info(
        "Retained columns: %s",
        ", ".join(relevant_cols),
    )

    return df

## MAIN FUNCTIONALITY ##
def standardise_and_combine_mouse_tracking(
    input_folder: str,
    output_dir: str,
    logger: logging.Logger,
) -> None:
    """Removes metadata. \
        Adds group and task ids to individual datasets \
        Combines all datasets"""
    logger.info("="*40)
    logger.info("Initiate mission: Combine all mouse tracking datasets into one")
    logger.info("="*40)

    list_of_dfs = []
    output_path = Path(output_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("-"*40)
    for file in Path(input_folder).glob("*.csv"):
        group_id = _extract_group(file, logger)
        df = pl.read_csv(file, skip_rows=22)
        logger.info(f"Read {file} into a new dataframe and skipping the metadata")
        logger.info("-"*20)
        logger.info(f"Adding group id ({group_id}) to {file}")
        df = df.with_columns(
            pl.lit(group_id).alias("group"),
        )

        logger.info("-"*20)
        logger.info("Removing rows before and after tasks")
        df = _reduce_to_tasks(df, logger)

        logger.info("-"*20)
        logger.info("Adding task id")
        df = _add_task_id(df, logger)

        logger.info("-"*20)
        logger.info("Resetting timestamps for each task")
        df = _reset_time(df, logger)

        list_of_dfs.append(df)

    df_combined = pl.concat(list_of_dfs)
    logger.info("-"*20)
    logger.info("Removing irrelevant cols")
    df_combined = _remove_irrelevant_cols(df, logger)
    df_combined.write_csv(output_dir)

    logger.info("-"*40)
    logger.info("All mouse tracking datasets have been combined into one with the group and task ids as columns")
    logger.info("="*20)

    