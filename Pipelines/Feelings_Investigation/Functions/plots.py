"""Plotting functions for the Feelings_Investigation pipeline."""

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
## __________________ ##


## MAIN FUNCTIONALITY ##
def feeling_vs_time_graph(
    input_file: str | Path,
    output_folder: str | Path,
    feeling_cols: list[str],
    logger: logging.Logger,
) -> None:
    """Create one interactive figure per task, with one subplot per group."""

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

    # Two columns keeps the individual group panels reasonably readable.
    subplot_columns = 2

    for task in tasks:
        task_df = df.filter(pl.col("task") == task)

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

        task_maximum_timestamp = (
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

            figure.update_xaxes(
                range=[0, task_maximum_timestamp],
                autorange=False,
                rangemode="tozero",
                row=subplot_row,
                col=subplot_column,
            )

            figure.update_yaxes(
                range=[-0.05, 1.05],
                tickmode="array",
                tickvals=[0, 1],
                ticktext=["No", "Yes"],
                row=subplot_row,
                col=subplot_column,
            )

        figure.update_layout(
            title={
                "text": (
                    "Detected emotions over time"
                    f"<br><sup>Task {task} · "
                    f"Threshold {certainty}% · "
                    f"{len(groups)} groups</sup>"
                )
            },
            template="plotly_white",
            hovermode="closest",
            legend={
                "title": {
                    "text": "Emotions",
                },
                # Clicking an emotion hides it in every group panel.
                "groupclick": "togglegroup",
            },
            height=max(
                650,
                subplot_rows * 260,
            ),
        )

        # Add axis titles only along the outside of the figure.
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

        safe_task = _make_safe_filename(str(task))

        plot_directory = (
            output_folder
            / f"FEA_{certainty}"
        )

        plot_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file = (
            plot_directory
            / f"task_{safe_task}.html"
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
                "Saved combined plot for task %s, "
                "threshold %s%%, containing %d groups to %s. "
                "X-axis range: 0-%d ms"
            ),
            task,
            certainty,
            len(groups),
            output_file,
            task_maximum_timestamp,
        )