"""Example helper functions for the pipeline."""

## IMPORTS ##
import logging
import polars as pl
from bisect import bisect_right
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


def _extract_matching_transcriptions(
    input_dir: str,
    events: pl.DataFrame,
    logger: logging.Logger,
) -> pl.DataFrame:
    transcriptions = pl.read_csv(input_dir).sort(
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


def _add_present_feelings(
    input_dir: str,
    final_data: pl.DataFrame,
    relevant_feelings: list[str],
    logger: logging.Logger,
) -> pl.DataFrame:
    feelings_data = pl.read_csv(input_dir)

    # Organize feeling rows by group and task.
    feelings_lookup = {}

    for row in feelings_data.iter_rows(named=True):
        key = (row["group"], row["task"])
        feelings_lookup.setdefault(key, []).append(row)

    feelings_per_interval = []

    for interval in final_data.iter_rows(named=True):
        key = (interval["group"], interval["task"])
        rows = feelings_lookup.get(key, [])

        # Select feeling rows within this transcription interval.
        matching_rows = [
            row
            for row in rows
            if (
                interval["transcription_start"]
                <= row["Timestamp"]
                <= interval["transcription_end"]
            )
        ]

        # Include each feeling if it occurs at least once in the interval.
        present_feelings = [
            feeling
            for feeling in relevant_feelings
            if any(row[feeling] == 1 for row in matching_rows)
        ]

        feelings_per_interval.append(present_feelings)

    result = final_data.with_columns(
        pl.Series(
            "present_feelings",
            feelings_per_interval,
            dtype=pl.List(pl.String),
        )
    )

    logger.info(
        "Added present feelings to %d transcription intervals",
        result.height,
    )

    return result


def _add_input_events(
    input_dir: str,
    final_data: pl.DataFrame,
    logger: logging.Logger,
) -> pl.DataFrame:
    input_data = pl.read_csv(input_dir).sort(
        ["group", "task", "Timestamp"]
    )

    # Organize input-event rows by group and task.
    input_lookup = {}

    for row in input_data.iter_rows(named=True):
        key = (row["group"], row["task"])
        input_lookup.setdefault(key, []).append(row)

    mouse_coordinates_per_interval = []
    input_sources_per_interval = []

    for interval in final_data.iter_rows(named=True):
        key = (interval["group"], interval["task"])
        rows = input_lookup.get(key, [])

        # Select input events within the transcription interval.
        matching_rows = [
            row
            for row in rows
            if (
                interval["transcription_start"]
                <= row["Timestamp"]
                <= interval["transcription_end"]
            )
        ]

        mouse_coordinates = [
            row["Data"]
            for row in matching_rows
            if row["InputEventSource"] == "Mouse"
        ]

        # dict.fromkeys removes duplicates while preserving order.
        input_sources = list(dict.fromkeys(
            row["InputEventSource"]
            for row in matching_rows
            if row["InputEventSource"] is not None
        ))

        mouse_coordinates_per_interval.append(mouse_coordinates)
        input_sources_per_interval.append(input_sources)

    result = final_data.with_columns(
        pl.Series(
            "MouseCoordinates",
            mouse_coordinates_per_interval,
            dtype=pl.List(pl.String),
        ),
        pl.Series(
            "InputEventSources",
            input_sources_per_interval,
            dtype=pl.List(pl.String),
        ),
    )

    logger.info(
        "Added input events to %d transcription intervals",
        result.height,
    )

    return result
## MAIN FUNCTIONALITY ##
def extract_and_combine(
    input_dir_fea_data: str,
    input_dir_transcription_data: str,
    input_dir_mouse_data: str,
    relevant_feelings: list[str],
    logger: logging.Logger,
) -> pl.DataFrame:
    events = _extract_feeling_timestamps(
        input_dir=input_dir_fea_data, 
        relevant_feelings=relevant_feelings, 
        logger=logger
    )

    final_data = _extract_matching_transcriptions(
        input_dir=input_dir_transcription_data,
        events=events,
        logger=logger,
    )

    final_data = _add_present_feelings(
        input_dir=input_dir_fea_data,
        final_data=final_data,
        relevant_feelings=relevant_feelings,
        logger=logger,
    )

    final_data = _add_input_events(
        input_dir=input_dir_mouse_data,
        final_data=final_data,
        logger=logger,
    )

    logger.info(final_data.head(10))
    # logger.info(
    #     "%s",
    #     final_data
    #     .filter(pl.col("group") == "A5")
    #     .head(10),
    # )
    return final_data