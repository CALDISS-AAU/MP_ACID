"""Create interactive plots for the Feelings_Investigation pipeline."""

## IMPORTS ##
import logging
import re
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.colors import qualitative
import polars as pl
## _______ ##


## STATIC VARIABLES ##
## __________________ ##


## HELPER FUNCTIONS ##
def _extract_certainty_from_filename(
    input_file: Path,
) -> str:
    """Extract certainty from filenames such as FEA_85.csv."""

    match = re.search(r"FEA_(\d+)", input_file.stem)

    if match is None:
        return "unknown"

    return match.group(1)


def _make_safe_filename(value: str) -> str:
    """Replace characters that may be unsuitable in filenames."""

    return re.sub(
        pattern=r"[^A-Za-z0-9_-]+",
        repl="_",
        string=value,
    )


def _create_feeling_colours(
    feeling_cols: list[str],
) -> dict[str, str]:
    """Assign one visually distinct colour to each feeling."""

    colour_palette = [
        "#E41A1C",  # Red
        "#377EB8",  # Blue
        "#4DAF4A",  # Green
        "#FF7F00",  # Orange
        "#984EA3",  # Purple
        "#A65628",  # Brown
        "#F781BF",  # Pink
        "#17BECF",  # Cyan
        "#BCBD22",  # Olive
        "#FFD700",  # Yellow
        "#000000",  # Black
        "#7F7F7F",  # Grey
    ]

    if len(feeling_cols) > len(colour_palette):
        raise ValueError(
            f"At most {len(colour_palette)} feelings are supported "
            "by the selected colour palette."
        )

    if len(feeling_cols) != len(set(feeling_cols)):
        raise ValueError(
            "feeling_cols must not contain duplicate feeling names."
        )

    return {
        feeling: colour_palette[index]
        for index, feeling in enumerate(feeling_cols)
    }


def _find_sequential_one_lengths(
    values: list[int | None],
) -> list[int]:
    """Return the lengths of uninterrupted sequences of ones."""

    sequence_lengths = []
    current_length = 0

    for value in values:
        if value == 1:
            current_length += 1
        elif current_length > 0:
            sequence_lengths.append(current_length)
            current_length = 0

    # Include a sequence that continues until the final row.
    if current_length > 0:
        sequence_lengths.append(current_length)

    return sequence_lengths


def _apply_feeling_vs_time_design(
    figure: go.Figure,
    task: str,
    certainty: str,
    number_of_groups: int,
    maximum_timestamp: int,
    subplot_rows: int,
    subplot_columns: int,
) -> None:
    """Apply the layout and axis design to a feeling-over-time figure.

    Args:
        figure: Plotly figure to style.
        task: Task represented by the figure.
        certainty: FEA certainty threshold.
        number_of_groups: Number of group subplots.
        maximum_timestamp: Largest task timestamp in milliseconds.
        subplot_rows: Number of subplot rows.
        subplot_columns: Number of subplot columns.

    """
    figure.update_xaxes(
        range=[0, maximum_timestamp],
        autorange=False,
        rangemode="tozero",
    )

    figure.update_yaxes(
        range=[-0.05, 1.05],
        tickmode="array",
        tickvals=[0, 1],
        ticktext=["No", "Yes"],
    )

    figure.update_layout(
        title={
            "text": (
                "Detected emotions over time"
                f"<br><sup>Task {task} · "
                f"Threshold {certainty}% · "
                f"{number_of_groups} groups</sup>"
            )
        },
        template="plotly_white",
        hovermode="closest",
        legend={
            "title": {
                "text": "Emotions",
            },
            "groupclick": "togglegroup",
        },
        height=max(
            650,
            subplot_rows * 260,
        ),
    )

    for column in range(1, subplot_columns + 1):
        figure.update_xaxes(
            title_text="Time (ms)",
            row=subplot_rows,
            col=column,
        )

    for row in range(1, subplot_rows + 1):
        figure.update_yaxes(
            title_text="Detected",
            row=row,
            col=1,
        )


def _generate_feeling_vs_time_figure(
    task_df: pl.DataFrame,
    task: str,
    groups: list[str],
    feeling_cols: list[str],
    feeling_colours: dict[str, str],
    certainty: str,
) -> go.Figure:
    """Create group subplots and feeling traces ->
       Apply the feeling-over-time graph design ->
       Return the completed figure
    """
    subplot_columns = 2
    subplot_rows = (
        len(groups) + subplot_columns - 1
    ) // subplot_columns

    figure = make_subplots(
        rows=subplot_rows,
        cols=subplot_columns,
        subplot_titles=[
            f"Group {group}"
            for group in groups
        ],
        shared_xaxes=True,
        shared_yaxes=True,
        vertical_spacing=min(
            0.04,
            0.4 / subplot_rows,
        ),
        horizontal_spacing=0.08,
    )

    maximum_timestamp = (
        task_df.get_column("Timestamp")
        .cast(pl.Int64)
        .max()
    )

    for group_index, group in enumerate(groups):
        subplot_row = (
            group_index // subplot_columns
        ) + 1
        subplot_column = (
            group_index % subplot_columns
        ) + 1

        plot_df = (
            task_df.filter(
                pl.col("group") == group
            )
            .sort("Timestamp")
        )

        timestamps = (
            plot_df.get_column("Timestamp")
            .cast(pl.Int64)
            .to_list()
        )

        for feeling in feeling_cols:
            feeling_values = (
                plot_df.get_column(feeling)
                .cast(pl.Int8)
                .to_list()
            )

            figure.add_trace(
                go.Scattergl(
                    x=timestamps,
                    y=feeling_values,
                    mode="lines",
                    name=feeling,
                    legendgroup=feeling,
                    showlegend=(group_index == 0),
                    line={
                        "color": feeling_colours[feeling],
                        "width": 1,
                        "shape": "hv",
                    },
                    hovertemplate=(
                        f"<b>{feeling}</b><br>"
                        f"Group: {group}<br>"
                        "Time: %{x:,} ms<br>"
                        "Detected: %{y}"
                        "<extra></extra>"
                    ),
                ),
                row=subplot_row,
                col=subplot_column,
            )

    _apply_feeling_vs_time_design(
        figure=figure,
        task=task,
        certainty=certainty,
        number_of_groups=len(groups),
        maximum_timestamp=maximum_timestamp,
        subplot_rows=subplot_rows,
        subplot_columns=subplot_columns,
    )

    return figure


def _apply_sequence_distribution_design(
    figure: go.Figure,
    task: str,
    certainty: str,
    number_of_groups: int,
    feeling_cols: list[str],
    subplot_rows: int,
    subplot_columns: int,
) -> None:
    """Apply the design to a sequence-distribution figure.

    Args:
        figure: Plotly figure to style.
        task: Task represented by the figure.
        certainty: FEA certainty threshold.
        number_of_groups: Number of group subplots.
        feeling_cols: Feeling names displayed on the x-axis.
        subplot_rows: Number of subplot rows.
        subplot_columns: Number of subplot columns.

    """
    figure.update_xaxes(
        tickmode="array",
        tickvals=list(range(len(feeling_cols))),
        ticktext=feeling_cols,
        tickangle=-35,
        range=[
            -0.5,
            len(feeling_cols) - 0.2,
        ],
    )

    figure.update_yaxes(
        range=[0, 100],
        autorange=False,
        tickmode="linear",
        tick0=0,
        dtick=50,
    )

    figure.update_layout(
        title={
            "text": (
                "Sequential emotion-detection lengths"
                f"<br><sup>Task {task} · "
                f"Threshold {certainty}% · "
                f"{number_of_groups} groups</sup>"
            )
        },
        template="plotly_white",
        violinmode="overlay",
        boxmode="overlay",
        hovermode="closest",
        legend={
            "title": {
                "text": "Emotions",
            },
            "groupclick": "togglegroup",
        },
        height=max(
            650,
            subplot_rows * 300,
        ),
    )

    for column in range(1, subplot_columns + 1):
        figure.update_xaxes(
            title_text="Feeling",
            row=subplot_rows,
            col=column,
        )

    for row in range(1, subplot_rows + 1):
        figure.update_yaxes(
            title_text="Sequential rows",
            row=row,
            col=1,
        )


def _generate_sequence_distribution_figure(
    task_df: pl.DataFrame,
    task: str,
    groups: list[str],
    feeling_cols: list[str],
    feeling_colours: dict[str, str],
    certainty: str,
) -> tuple[go.Figure, int]:
    """Find uninterrupted feeling-detection sequences ->
    Add box and violin traces for each group ->
    Apply the sequence-distribution graph design ->
    Return the completed figure and sequence count
    """
    subplot_columns = 2
    subplot_rows = (
        len(groups) + subplot_columns - 1
    ) // subplot_columns

    figure = make_subplots(
        rows=subplot_rows,
        cols=subplot_columns,
        subplot_titles=[
            f"Group {group}"
            for group in groups
        ],
        shared_yaxes=True,
        vertical_spacing=min(
            0.04,
            0.4 / subplot_rows,
        ),
        horizontal_spacing=0.08,
    )

    total_sequences = 0

    for group_index, group in enumerate(groups):
        subplot_row = (
            group_index // subplot_columns
        ) + 1
        subplot_column = (
            group_index % subplot_columns
        ) + 1

        group_df = (
            task_df.filter(
                pl.col("group") == group
            )
            .sort("Timestamp")
        )

        for feeling_index, feeling in enumerate(feeling_cols):
            values = (
                group_df.get_column(feeling)
                .cast(pl.Int8)
                .to_list()
            )

            sequence_lengths = _find_sequential_one_lengths(
                values
            )

            total_sequences += len(sequence_lengths)

            if not sequence_lengths:
                continue

            colour = feeling_colours[feeling]

            figure.add_trace(
                go.Box(
                    x=[
                        feeling_index - 0.12
                    ] * len(sequence_lengths),
                    y=sequence_lengths,
                    name=feeling,
                    legendgroup=feeling,
                    showlegend=False,
                    width=0.16,
                    boxpoints=False,
                    fillcolor=colour,
                    line={
                        "color": colour,
                        "width": 1.5,
                    },
                    marker={
                        "color": colour,
                    },
                    opacity=0.85,
                    hovertemplate=(
                        f"<b>{feeling}</b><br>"
                        f"Group: {group}<br>"
                        "Sequence length: %{y} rows"
                        "<extra></extra>"
                    ),
                ),
                row=subplot_row,
                col=subplot_column,
            )

            figure.add_trace(
                go.Violin(
                    x0=feeling_index,
                    y=sequence_lengths,
                    name=feeling,
                    legendgroup=feeling,
                    showlegend=(group_index == 0),
                    side="positive",
                    width=0.7,
                    points=False,
                    meanline={
                        "visible": True,
                    },
                    line={
                        "color": colour,
                        "width": 1.5,
                    },
                    fillcolor=colour,
                    opacity=0.55,
                    spanmode="hard",
                    hovertemplate=(
                        f"<b>{feeling}</b><br>"
                        f"Group: {group}<br>"
                        "Sequence length: %{y} rows"
                        "<extra></extra>"
                    ),
                ),
                row=subplot_row,
                col=subplot_column,
            )

    _apply_sequence_distribution_design(
        figure=figure,
        task=task,
        certainty=certainty,
        number_of_groups=len(groups),
        feeling_cols=feeling_cols,
        subplot_rows=subplot_rows,
        subplot_columns=subplot_columns,
    )

    return figure, total_sequences
## __________________ ##


## MAIN FUNCTIONALITY ##
def feeling_vs_time_graph(
    input_file: str | Path,
    output_folder: str | Path,
    feeling_cols: list[str],
    logger: logging.Logger,
) -> None:
    """Read and validate an FEA dataset ->
       Extract the certainty threshold and assign feeling colours ->
       Create one figure per task with one subplot per group ->
       Plot feeling detections over time ->
       Save each figure as an interactive HTML file
    """

    input_file = Path(input_file)
    output_folder = Path(output_folder)

    logger.info(
        "Reading FEA dataset from %s",
        input_file,
    )

    df = pl.read_csv(
        input_file,
        schema_overrides={
            "group": pl.String,
            "task": pl.String,
        },
    )
    
    required_columns = [
        "Timestamp",
        "group",
        "task",
        *feeling_cols,
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{input_file} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    certainty = _extract_certainty_from_filename(input_file)

    tasks = (
        df.get_column("task")
        .drop_nulls()
        .unique()
        .sort()
        .to_list()
    )

    feeling_colours = _create_feeling_colours(feeling_cols)

    logger.info(
        "Creating %d task figures from %s",
        len(tasks),
        input_file.name,
    )

    for task in tasks:
        task_df = df.filter(
            pl.col("task") == task
        )

        groups = (
            task_df.get_column("group")
            .drop_nulls()
            .unique()
            .sort()
            .to_list()
        )

        if not groups:
            logger.warning(
                "No groups found for task %s in %s",
                task,
                input_file.name,
            )
            continue

        figure = _generate_feeling_vs_time_figure(
            task_df=task_df,
            task=task,
            groups=groups,
            feeling_cols=feeling_cols,
            feeling_colours=feeling_colours,
            certainty=certainty,
        )

        safe_task = _make_safe_filename(str(task))
        plot_directory = output_folder / f"FEA_{certainty}"

        plot_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file = plot_directory / f"task_{safe_task}.html"

        figure.write_html(
            output_file,
            include_plotlyjs=True,
            full_html=True,
            config={
                "scrollZoom": True,
                "displaylogo": False,
                "responsive": True,
            },
        )


def feeling_sequence_distribution_graph(
    input_file: str | Path,
    output_folder: str | Path,
    feeling_cols: list[str],
    logger: logging.Logger,
) -> None:
    """Read and validate an FEA dataset ->
       Generate sequence-distribution figures for each task ->
       Save each figure as an interactive HTML file
    """

    input_file = Path(input_file)
    output_folder = Path(output_folder)

    logger.info(
        "Reading FEA dataset for sequence distributions from %s",
        input_file,
    )

    df = pl.read_csv(
        input_file,
        schema_overrides={
            "group": pl.String,
            "task": pl.String,
        },
    )

    required_columns = [
        "Timestamp",
        "group",
        "task",
        *feeling_cols,
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{input_file} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    certainty = _extract_certainty_from_filename(input_file)
    feeling_colours = _create_feeling_colours(feeling_cols)

    tasks = (
        df.get_column("task")
        .drop_nulls()
        .unique()
        .sort()
        .to_list()
    )

    subplot_columns = 2

    logger.info(
        "Creating %d sequence-distribution figures from %s",
        len(tasks),
        input_file.name,
    )

    for task in tasks:
        task_df = df.filter(
            pl.col("task") == task
        )

        groups = (
            task_df.get_column("group")
            .drop_nulls()
            .unique()
            .sort()
            .to_list()
        )

        if not groups:
            logger.warning(
                "No groups found for task %s in %s",
                task,
                input_file.name,
            )
            continue

        figure, total_sequences = (
            _generate_sequence_distribution_figure(
                task_df=task_df,
                task=task,
                groups=groups,
                feeling_cols=feeling_cols,
                feeling_colours=feeling_colours,
                certainty=certainty,
            )
        )

        safe_task = _make_safe_filename(str(task))
        plot_directory = output_folder / f"FEA_{certainty}"

        plot_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file = (
            plot_directory
            / f"sequence_lengths_task_{safe_task}.html"
        )

        figure.write_html(
            output_file,
            include_plotlyjs=True,
            full_html=True,
            config={
                "scrollZoom": True,
                "displaylogo": False,
                "responsive": True,
            },
        )

        logger.info(
            (
                "Saved sequence-distribution plot for task %s, "
                "threshold %s%%, containing %d groups and "
                "%d sequences to %s"
            ),
            task,
            certainty,
            len(groups),
            total_sequences,
            output_file,
        )










