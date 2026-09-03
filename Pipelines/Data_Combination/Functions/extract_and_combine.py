"""Example helper functions for the pipeline."""

## IMPORTS ##
import logging
import polars as pl
from bisect import bisect_right
from typing import Any
from pathlib import Path
## _______ ##


## DEFINITIONS ##
Row = dict[str, Any]
Lookup = dict[tuple[str, str], list[Row]]
## ___________ ##

## HELPER FUNCTIONS ##
def _extract_feeling_timestamps(
    feelings_data: pl.DataFrame,
    relevant_feelings: list[str],
    logger: logging.Logger,
) -> pl.DataFrame:
    events = (
        feelings_data
        .filter(pl.any_horizontal(pl.col(relevant_feelings) == 1))
        .select("group", "task", "Timestamp")
    )

    logger.info(
        "Extracted %d timestamp rows based on feelings",
        events.height,
    )

    return events


def _extract_matching_transcriptions(
    transcription_data: pl.DataFrame,
    events: pl.DataFrame,
    logger: logging.Logger,
) -> pl.DataFrame:
    transcriptions = transcription_data.sort(
        ["group", "task", "start"]
    )

    # Store transcription rows by group/task.
    transcription_lookup = {
        key: group.to_dicts()
        for key, group in transcriptions.group_by(
            ["group", "task"],
            maintain_order=True,
        )
    }

    final_data = []
    added_intervals = set()

    for event in events.iter_rows(named=True):
        key = (event["group"], event["task"])
        timestamp = event["Timestamp"]
        rows = transcription_lookup.get(key, [])

        if not rows:
            continue

        starts = [row["start"] for row in rows]
        index = bisect_right(starts, timestamp) - 1

        # Timestamp occurs before the first transcription row.
        if index < 0:
            continue

        current = rows[index]

        # Timestamp is inside the current sentence.
        if timestamp <= current["end"]:
            transcription_start = current["start"]
            transcription_end = current["end"]
            transcription_text = current["text"]

        # Timestamp may be in the gap before the next sentence.
        elif index + 1 < len(rows):
            following = rows[index + 1]

            if timestamp < following["start"]:
                transcription_start = current["start"]
                transcription_end = following["end"]
                transcription_text = (
                    f"{current['text']} {following['text']}"
                )
            else:
                continue
        else:
            continue

        interval_key = (
            event["group"],
            event["task"],
            transcription_start,
            transcription_end,
        )

        # Do not add the same matched interval more than once.
        if interval_key in added_intervals:
            continue

        added_intervals.add(interval_key)

        final_data.append({
            "group": event["group"],
            "task": event["task"],
            "feeling_timestamp": timestamp,
            "transcription_start": transcription_start,
            "transcription_end": transcription_end,
            "transcription_text": transcription_text,
        })

    result = pl.DataFrame(final_data)

    logger.info("Extracted %d transcription intervals", result.height)
    return result


def _build_group_task_lookup(
    data: pl.DataFrame,
) -> Lookup:
    """Organize dataframe rows by group and task."""
    lookup = {}

    for row in data.iter_rows(named=True):
        key = (row["group"], row["task"])
        lookup.setdefault(key, []).append(row)

    return lookup


def _get_matching_interval_rows(
    interval: Row,
    lookup: Lookup,
) -> list[Row]:
    """Find rows with the same group/task inside an interval."""
    key = (interval["group"], interval["task"])
    rows = lookup.get(key, [])

    return [
        row
        for row in rows
        if (
            interval["transcription_start"]
            <= row["Timestamp"]
            <= interval["transcription_end"]
        )
    ]


def _add_list_columns(
    data: pl.DataFrame,
    columns: dict[str, list[list[str]]],
) -> pl.DataFrame:
    """Add one or more string-list columns to a dataframe."""
    return data.with_columns(
        [
            pl.Series(
                name,
                values,
                dtype=pl.List(pl.String),
            )
            for name, values in columns.items()
        ]
    )


def _add_present_feelings(
    feelings_data: pl.DataFrame,
    final_data: pl.DataFrame,
    relevant_feelings: list[str],
    logger: logging.Logger,
) -> pl.DataFrame:
    """Add all relevant feelings present in each interval."""
    feelings_lookup = _build_group_task_lookup(feelings_data)
    feelings_per_interval = []

    for interval in final_data.iter_rows(named=True):
        matching_rows = _get_matching_interval_rows(
            interval=interval,
            lookup=feelings_lookup,
        )

        present_feelings = [
            feeling
            for feeling in relevant_feelings
            if any(row[feeling] == 1 for row in matching_rows)
        ]

        feelings_per_interval.append(present_feelings)

    result = _add_list_columns(
        data=final_data,
        columns={
            "present_feelings": feelings_per_interval,
        },
    )

    logger.info(
        "Added present feelings to %d transcription intervals",
        result.height,
    )

    return result


def _add_input_events(
    input_data: pl.DataFrame,
    final_data: pl.DataFrame,
    logger: logging.Logger,
) -> pl.DataFrame:
    """Add mouse coordinates and input sources to each interval."""
    input_lookup = _build_group_task_lookup(input_data)
    mouse_coordinates_per_interval = []
    input_sources_per_interval = []

    for interval in final_data.iter_rows(named=True):
        matching_rows = _get_matching_interval_rows(
            interval=interval,
            lookup=input_lookup,
        )

        mouse_coordinates = [
            row["Data"]
            for row in matching_rows
            if row["InputEventSource"] == "Mouse"
        ]

        input_sources = list(dict.fromkeys(
            row["InputEventSource"]
            for row in matching_rows
            if row["InputEventSource"] is not None
        ))

        mouse_coordinates_per_interval.append(mouse_coordinates)
        input_sources_per_interval.append(input_sources)

    result = _add_list_columns(
        data=final_data,
        columns={
            "MouseCoordinates": mouse_coordinates_per_interval,
            "InputEventSources": input_sources_per_interval,
        },
    )

    logger.info(
        "Added input events to %d transcription intervals",
        result.height,
    )

    return result
    

def _save_combined_data(
    data: pl.DataFrame,
    output_path_base: str,
    logger: logging.Logger,
) -> None:
    """Save combined data as CSV and JSON."""
    output_base = Path(output_path_base)
    output_base.parent.mkdir(parents=True, exist_ok=True)

    output_path_csv = output_base.with_suffix(".csv")
    output_path_json = output_base.with_suffix(".json")

    list_columns = [
        "present_feelings",
        "MouseCoordinates",
        "InputEventSources",
    ]

    # CSV cannot store lists, so convert them to pipe-separated strings.
    csv_data = data.with_columns(
        [
            pl.col(column).list.join("|")
            for column in list_columns
        ]
    )

    csv_data.write_csv(output_path_csv)

    # JSON preserves the list columns.
    data.write_json(output_path_json)

    logger.info(
        "Saved %d combined rows to %s and %s",
        data.height,
        output_path_csv,
        output_path_json,
    )


## MAIN FUNCTIONALITY ##
def extract_and_combine(
    input_dir_fea_data: str,
    input_dir_transcription_data: str,
    input_dir_mouse_data: str,
    output_path_base: str,
    relevant_feelings: list[str],
    logger: logging.Logger,
) -> None:
    feelings_data = pl.read_csv(input_dir_fea_data)
    transcription_data = pl.read_csv(input_dir_transcription_data)
    input_data = pl.read_csv(input_dir_mouse_data)

    events = _extract_feeling_timestamps(
        feelings_data=feelings_data,
        relevant_feelings=relevant_feelings,
        logger=logger,
    )

    final_data = _extract_matching_transcriptions(
        transcription_data=transcription_data,
        events=events,
        logger=logger,
    )

    final_data = _add_present_feelings(
        feelings_data=feelings_data,
        final_data=final_data,
        relevant_feelings=relevant_feelings,
        logger=logger,
    )

    final_data = _add_input_events(
        input_data=input_data,
        final_data=final_data,
        logger=logger,
    )

    _save_combined_data(
        data=final_data,
        output_path_base=output_path_base,
        logger=logger,
    )