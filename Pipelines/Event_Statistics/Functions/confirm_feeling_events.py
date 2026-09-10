"""Helper functions for the Feeling_Confirmation pipeline."""

## IMPORTS ##
import logging
from pathlib import Path

import polars as pl
## _______ ##


## STATIC VARIABLES ##
FEELING_COLUMNS = [
    "Anger",
    "Contempt",
    "Confusion",
    "Disgust",
    # "Engagement",
    "Fear",
    # "Joy",
    "Sadness",
    "Surprise",
]

TIME_WINDOW_MS = 5_000
## ________________ ##


## HELPER FUNCTIONS ##
def _parse_manual_timestamp_ms(
    timestamp: str,
) -> int:
    """
    Convert a manual timestamp in mm:ss format to milliseconds.

    Example:
        05:02 -> 302,000 milliseconds
    """
    try:
        minutes_text, seconds_text = timestamp.strip().split(
            ":",
            maxsplit=1,
        )

        minutes = int(minutes_text)
        seconds = int(seconds_text)

    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError(
            f"Invalid manual timestamp {timestamp!r}; "
            "expected mm:ss, for example 05:02."
        ) from error

    if minutes < 0:
        raise ValueError(
            f"Invalid manual timestamp {timestamp!r}: "
            "minutes cannot be negative."
        )

    if not 0 <= seconds < 60:
        raise ValueError(
            f"Invalid manual timestamp {timestamp!r}: "
            "seconds must be between 00 and 59."
        )

    return (
        minutes * 60
        + seconds
    ) * 1_000


def _normalise_task(
    task: object,
) -> int:
    """
    Convert task values such as '05', 5, or 5.0 to integer 5.
    """
    try:
        return int(float(str(task).strip()))
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"Invalid task value: {task!r}"
        ) from error


## MAIN FUNCTIONALITY ##
def feeling_confirmation(
    input_dir_manual: str,
    input_dir_machine: str,
    output_dir: str,
    logger: logging.Logger,
) -> None:
    """
    Compare manually registered events with machine-registered feelings.

    For every manual event, inspect the corresponding machine data for
    the same group and task within two seconds before and after the
    manually registered timestamp.

    The resulting CSV reports whether any feelings were detected,
    which feelings were detected, and the count for each feeling.
    """
    output_directory = Path(output_dir)
    output_path = (
        output_directory
        / "feeling_confirmation.csv"
    )

    logger.info(
        "Starting feeling confirmation using manual data %s "
        "and machine data %s",
        input_dir_manual,
        input_dir_machine,
    )

    try:
        # The manual file uses semicolons.
        df_manual = pl.read_csv(
            input_dir_manual,
            separator=";",
            infer_schema_length=0,
        )

        # The machine file uses commas.
        df_machine = pl.read_csv(
            input_dir_machine,
        )

        required_manual_columns = {
            "Group",
            "Stimuli",
            "Start",
            "Task",
        }

        required_machine_columns = {
            "Timestamp",
            "group",
            "task",
            *FEELING_COLUMNS,
        }

        missing_manual_columns = (
            required_manual_columns
            - set(df_manual.columns)
        )

        missing_machine_columns = (
            required_machine_columns
            - set(df_machine.columns)
        )

        if missing_manual_columns:
            raise ValueError(
                "Manual data is missing columns: "
                f"{sorted(missing_manual_columns)}"
            )

        if missing_machine_columns:
            raise ValueError(
                "Machine data is missing columns: "
                f"{sorted(missing_machine_columns)}"
            )

        logger.info(
            "Imported %d manual events and %d machine rows",
            df_manual.height,
            df_machine.height,
        )

        # Normalize machine columns once before performing comparisons.
        df_machine = df_machine.with_columns(
            pl.col("group")
            .cast(pl.String)
            .str.strip_chars()
            .alias("group"),

            pl.col("task")
            .cast(pl.Int64, strict=False)
            .alias("task"),

            pl.col("Timestamp")
            .cast(pl.Int64, strict=False)
            .alias("Timestamp"),

            *[
                pl.col(feeling)
                .cast(pl.Int64, strict=False)
                .fill_null(0)
                .alias(feeling)
                for feeling in FEELING_COLUMNS
            ],
        )

        results: list[dict[str, object]] = []

        for manual_row in df_manual.iter_rows(
            named=True,
        ):
            group = str(
                manual_row["Group"]
            ).strip()

            task = _normalise_task(
                manual_row["Task"]
            )

            manual_timestamp = str(
                manual_row["Start"]
            ).strip()

            timestamp_ms = _parse_manual_timestamp_ms(
                manual_timestamp
            )

            window_start_ms = max(
                0,
                timestamp_ms - TIME_WINDOW_MS,
            )

            window_end_ms = (
                timestamp_ms + TIME_WINDOW_MS
            )

            matching_machine_rows = df_machine.filter(
                (pl.col("group") == group)
                & (pl.col("task") == task)
                & (
                    pl.col("Timestamp")
                    >= window_start_ms
                )
                & (
                    pl.col("Timestamp")
                    <= window_end_ms
                )
            )

            if matching_machine_rows.is_empty():
                feeling_counts = {
                    feeling: 0
                    for feeling in FEELING_COLUMNS
                }
            else:
                feeling_counts = (
                    matching_machine_rows.select(
                        [
                            pl.col(feeling)
                            .sum()
                            .alias(feeling)
                            for feeling in FEELING_COLUMNS
                        ]
                    )
                    .row(
                        0,
                        named=True,
                    )
                )

                feeling_counts = {
                    feeling: int(
                        feeling_counts[feeling] or 0
                    )
                    for feeling in FEELING_COLUMNS
                }

            detected_feelings = [
                feeling
                for feeling, count
                in feeling_counts.items()
                if count > 0
            ]

            result = {
                "Group": group,
                "Stimuli": manual_row["Stimuli"],
                "Start": manual_timestamp,
                "Task": task,
                "Manual_Timestamp_ms": timestamp_ms,
                "Window_Start_ms": window_start_ms,
                "Window_End_ms": window_end_ms,
                "Machine_Rows_Checked": (
                    matching_machine_rows.height
                ),
                "Any_Feeling_Detected": bool(
                    detected_feelings
                ),
                "Detected_Feelings": ", ".join(
                    detected_feelings
                ),
            }

            # Include separate count columns for easier analysis.
            result.update(
                {
                    f"{feeling}_Count": count
                    for feeling, count
                    in feeling_counts.items()
                }
            )

            results.append(result)

            logger.debug(
                "Manual event %s, task %s at %s: checked %d "
                "machine rows and detected %s",
                group,
                task,
                manual_timestamp,
                matching_machine_rows.height,
                (
                    ", ".join(detected_feelings)
                    if detected_feelings
                    else "no feelings"
                ),
            )

        result_df = pl.DataFrame(results)

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        result_df.write_csv(
            output_path,
        )

        matched_events = result_df.filter(
            pl.col("Any_Feeling_Detected")
        ).height

        logger.info(
            "Detected machine feelings for %d of %d manual events",
            matched_events,
            result_df.height,
        )

        logger.info(
            "Created feeling-confirmation report at %s",
            output_path,
        )

    except Exception:
        logger.exception(
            "Failed to compare manual and machine feeling events"
        )
        raise