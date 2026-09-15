"""Generate interactive plots for the Event_Statistics pipeline."""

## IMPORTS ##
import logging
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import plotly.graph_objects as go
## _______ ##


## HELPER FUNCTIONS ##
def _import_and_group_data(
    csv_path: str | Path,
    logger: logging.Logger,
) -> dict[str, dict[Any, pl.DataFrame]]:
    """Load FEA data and partition it by group and task."""
    logger.info(
        "Reading data from %s",
        csv_path,
    )

    try:
        df = pl.read_csv(csv_path)

        logger.info(
            "Imported %d rows and %d columns",
            df.height,
            df.width,
        )

        df = df.drop("Row")

        logger.debug(
            "Dropped columns: Row"
        )

        datasets = {
            "full": {
                "all": df,
            },
            "by_group": {
                key[0]: partition
                for key, partition in df.partition_by(
                    "group",
                    as_dict=True,
                    maintain_order=False,
                ).items()
            },
            "by_task": {
                key[0]: partition
                for key, partition in df.partition_by(
                    "task",
                    as_dict=True,
                    maintain_order=False,
                ).items()
            },
            "by_group_and_task": df.partition_by(
                [
                    "group",
                    "task",
                ],
                as_dict=True,
                maintain_order=False,
            ),
        }

        logger.info(
            "Created %d group partitions, %d task partitions, "
            "and %d group-task partitions",
            len(datasets["by_group"]),
            len(datasets["by_task"]),
            len(datasets["by_group_and_task"]),
        )

        return datasets

    except Exception:
        logger.exception(
            "Failed to import and group data from %s",
            csv_path,
        )
        raise


def _create_bar_chart(
    datasets: dict[str, dict[Any, pl.DataFrame]],
    output_path: str,
    plot_feeling_cols: list[str],
    logger: logging.Logger,
) -> None:
    """Create a grouped bar chart of feeling occurrences by task.

    Args:
        datasets: Dataframe partitions organised by group and task.
        output_path: Directory in which to save the chart.
        plot_feeling_cols: Feeling columns included in the chart.
        logger: Logger used to record chart generation.

    """
    output_directory = Path(output_path)
    plot_path = output_directory / "feeling_bar_chart.html"

    logger.info(
        "Creating Plotly bar chart at %s",
        plot_path,
    )

    try:
        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        partitions = datasets["by_group_and_task"]

        if not partitions:
            raise ValueError(
                "The group-task dataset contains no partitions."
            )

        groups = sorted(
            {
                group
                for group, _ in partitions
            },
            key=str,
        )

        tasks = sorted(
            {
                task
                for _, task in partitions
            },
            key=int,
        )

        task_statistics: dict[
            Any,
            dict[str, dict[str, float]],
        ] = {}

        for task in tasks:
            group_values = {
                feeling: []
                for feeling in plot_feeling_cols
            }

            for group in groups:
                partition = partitions.get(
                    (
                        group,
                        task,
                    )
                )

                if partition is None:
                    continue

                sums = partition.select(
                    pl.col(plot_feeling_cols).sum()
                ).row(0)

                for feeling, value in zip(
                    plot_feeling_cols,
                    sums,
                    strict=True,
                ):
                    group_values[feeling].append(
                        int(value)
                        if value is not None
                        else 0
                    )

            task_statistics[task] = {}

            for feeling, values in group_values.items():
                statistics = pl.Series(values)

                task_statistics[task][feeling] = {
                    "total": sum(values),
                    "mean": float(
                        statistics.mean() or 0
                    ),
                    "median": float(
                        statistics.median() or 0
                    ),
                    "groups": len(values),
                }

        figure = go.Figure()

        colours = [
            "#4E79A7",
            "#F28E2B",
            "#E15759",
            "#76B7B2",
        ]

        for task_index, task in enumerate(tasks):
            totals = [
                task_statistics[task][feeling]["total"]
                for feeling in plot_feeling_cols
            ]

            custom_data = [
                [
                    task_statistics[task][feeling]["mean"],
                    task_statistics[task][feeling]["median"],
                    task_statistics[task][feeling]["groups"],
                ]
                for feeling in plot_feeling_cols
            ]

            figure.add_trace(
                go.Bar(
                    name=f"Task {task}",
                    x=plot_feeling_cols,
                    y=totals,
                    marker_color=colours[
                        task_index % len(colours)
                    ],
                    customdata=custom_data,
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        f"Task: {task}<br>"
                        "Total occurrences: %{y:,}<br>"
                        "Mean per group: "
                        "%{customdata[0]:.2f}<br>"
                        "Median per group: "
                        "%{customdata[1]:.2f}<br>"
                        "Groups: %{customdata[2]:.0f}"
                        "<extra></extra>"
                    ),
                )
            )

        figure.update_layout(
            title={
                "text": "Feeling occurrences by task",
                "x": 0.5,
                "xanchor": "center",
            },
            autosize=True,
            height=700,
            barmode="group",
            bargap=0.18,
            bargroupgap=0.05,
            xaxis={
                "title": "Feeling",
                "categoryorder": "array",
                "categoryarray": plot_feeling_cols,
            },
            yaxis={
                "title": "Total occurrences",
                "rangemode": "tozero",
                "gridcolor": "#D9D9D9",
            },
            margin={
                "l": 90,
                "r": 40,
                "t": 100,
                "b": 100,
            },
            legend={
                "title": {
                    "text": "Task",
                },
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "center",
                "x": 0.5,
            },
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            font={
                "family": "Arial",
                "size": 13,
            },
            hovermode="closest",
        )

        figure.write_html(
            plot_path,
            include_plotlyjs=True,
            full_html=True,
            config={
                "responsive": True,
                "displaylogo": False,
            },
        )

    except Exception:
        logger.exception(
            "Failed to create Plotly bar chart at %s",
            plot_path,
        )
        raise

    logger.info(
        "Created Plotly bar chart at %s",
        plot_path,
    )


def _classify_group(group: Any) -> str:
    """Classify a group according to its identifier prefix."""
    group_id = str(group)

    if group_id.startswith("A"):
        return "Group A"

    if group_id.startswith("C"):
        return "Group C"

    return "Other"


def _create_observed_density_data(
    datasets: dict[str, dict[Any, pl.DataFrame]],
    plot_feeling_cols: list[str],
) -> pl.DataFrame:
    """Calculate observed feeling totals for each group-task pair."""
    partitions = datasets["by_group_and_task"]

    if not partitions:
        raise ValueError(
            "The group-task dataset contains no partitions."
        )

    pair_data: list[dict[str, Any]] = []

    for (group, task), partition in partitions.items():
        feeling_sums = partition.select(
            pl.col(plot_feeling_cols).sum()
        ).row(0)

        feeling_density = sum(
            int(value)
            if value is not None
            else 0
            for value in feeling_sums
        )

        pair_data.append(
            {
                "group": str(group),
                "task": task,
                "group_type": _classify_group(group),
                "feeling_density": feeling_density,
            }
        )

    return pl.DataFrame(pair_data)


def _estimate_ten_minute_feeling_density(
    partition: pl.DataFrame,
    plot_feeling_cols: list[str],
    group: Any,
    task: Any,
    logger: logging.Logger,
) -> float:
    """Estimate feeling occurrences over a ten-minute period.

    Args:
        partition: FEA rows for one group-task combination.
        plot_feeling_cols: Feeling columns included in the calculation.
        group: Group identifier represented by the partition.
        task: Task identifier represented by the partition.
        logger: Logger used to record invalid durations and scaling.

    Returns:
        The observed or duration-adjusted feeling-event count.

    """
    ten_minutes_ms = 600_000.0

    feeling_sums = partition.select(
        pl.col(plot_feeling_cols).sum()
    ).row(0)

    observed_feeling_events = sum(
        int(value)
        if value is not None
        else 0
        for value in feeling_sums
    )

    timestamps = (
        partition.select(
            pl.col("Timestamp")
            .cast(
                pl.Float64,
                strict=False,
            )
            .drop_nulls()
        )
        .to_series()
    )

    if timestamps.is_empty():
        logger.warning(
            "No valid timestamps for group %s, task %s; "
            "using the observed feeling total",
            group,
            task,
        )

        return float(observed_feeling_events)

    first_timestamp = float(
        timestamps.min()
    )
    last_timestamp = float(
        timestamps.max()
    )
    duration_ms = last_timestamp - first_timestamp

    if duration_ms <= 0:
        logger.warning(
            "Invalid duration of %.2f ms for group %s, task %s; "
            "using the observed feeling total",
            duration_ms,
            group,
            task,
        )

        return float(observed_feeling_events)

    if duration_ms < ten_minutes_ms:
        estimated_feeling_events = (
            observed_feeling_events
            * ten_minutes_ms
            / duration_ms
        )

        logger.debug(
            "Scaled group %s, task %s from %d events over %.2f ms "
            "to %.2f estimated events over 10 minutes",
            group,
            task,
            observed_feeling_events,
            duration_ms,
            estimated_feeling_events,
        )

        return estimated_feeling_events

    return float(observed_feeling_events)


def _create_ten_minute_density_data(
    datasets: dict[str, dict[Any, pl.DataFrame]],
    plot_feeling_cols: list[str],
    logger: logging.Logger,
) -> pl.DataFrame:
    """Estimate feeling totals and classify each group-task pair."""
    partitions = datasets["by_group_and_task"]

    if not partitions:
        raise ValueError(
            "The group-task dataset contains no partitions."
        )

    pair_data: list[dict[str, Any]] = []

    for (group, task), partition in partitions.items():
        feeling_density = (
            _estimate_ten_minute_feeling_density(
                partition=partition,
                plot_feeling_cols=plot_feeling_cols,
                group=group,
                task=task,
                logger=logger,
            )
        )

        pair_data.append(
            {
                "group": str(group),
                "task": task,
                "group_type": _classify_group(group),
                "feeling_density": feeling_density,
            }
        )

    return pl.DataFrame(pair_data)


def _get_sorted_density_tasks(
    density_data: pl.DataFrame,
) -> list[Any]:
    """Return unique density-data tasks in a stable sorted order."""
    tasks = (
        density_data.get_column("task")
        .unique()
        .to_list()
    )

    try:
        return sorted(
            tasks,
            key=int,
        )
    except (TypeError, ValueError):
        return sorted(
            tasks,
            key=str,
        )


def _add_density_histogram_traces(
    figure: go.Figure,
    density_data: pl.DataFrame,
    histogram_group: str,
    density_label: str,
    density_format: str,
) -> None:
    """Add group and task histogram traces to a figure.

    Args:
        figure: Plotly figure receiving the traces.
        density_data: Density values for each group-task pair.
        histogram_group: Plotly identifier shared by histogram traces.
        density_label: Description shown for density values on hover.
        density_format: Plotly numeric format applied to density values.

    """
    tasks = _get_sorted_density_tasks(
        density_data
    )

    colour_sets = {
        "Group A": [
            "#BDD7EE",
            "#6BAED6",
            "#3182BD",
            "#08519C",
        ],
        "Group C": [
            "#FDD0A2",
            "#FDAE6B",
            "#F16913",
            "#A63603",
        ],
        "Other": [
            "#D9D9D9",
            "#BDBDBD",
            "#969696",
            "#636363",
        ],
    }

    bin_size = 5.0
    bin_start = -0.5

    max_density = float(
        density_data.get_column(
            "feeling_density"
        ).max()
        or 0.0
    )

    number_of_bins = (
        int(
            (max_density - bin_start)
            // bin_size
        )
        + 1
    )

    bin_end = (
        bin_start
        + number_of_bins * bin_size
    )

    for group_type, shades in colour_sets.items():
        for task_index, task in enumerate(tasks):
            trace_data = density_data.filter(
                (pl.col("group_type") == group_type)
                & (pl.col("task") == task)
            )

            if trace_data.is_empty():
                continue

            colour = shades[
                task_index % len(shades)
            ]

            figure.add_trace(
                go.Histogram(
                    name=f"{group_type} — Task {task}",
                    x=trace_data.get_column(
                        "feeling_density"
                    ).to_list(),
                    marker={
                        "color": colour,
                        "line": {
                            "color": "#FFFFFF",
                            "width": 0.5,
                        },
                    },
                    opacity=1.0,
                    bingroup=histogram_group,
                    legendgroup=group_type,
                    xbins={
                        "start": bin_start,
                        "end": bin_end,
                        "size": bin_size,
                    },
                    hovertemplate=(
                        f"<b>{group_type}</b><br>"
                        f"Task: {task}<br>"
                        f"{density_label}: "
                        f"%{{x{density_format}}}<br>"
                        "Group-task pairs: %{y:,}"
                        "<extra></extra>"
                    ),
                )
            )


def _add_density_kde_and_median(
    figure: go.Figure,
    density_data: pl.DataFrame,
    density_label: str,
    density_format: str,
) -> None:
    """Calculate and add a KDE curve and median marker.

    Args:
        figure: Plotly figure receiving the statistical traces.
        density_data: Density values for each group-task pair.
        density_label: Description shown for KDE values on hover.
        density_format: Plotly numeric format applied to density values.

    """
    density_values = np.asarray(
        density_data.get_column(
            "feeling_density"
        ).to_list(),
        dtype=float,
    )

    if len(density_values) <= 1:
        return

    log_density_values = np.log1p(
        density_values
    )

    number_of_observations = len(
        log_density_values
    )

    log_standard_deviation = float(
        np.std(
            log_density_values,
            ddof=1,
        )
    )

    kde_bandwidth = (
        1.06
        * log_standard_deviation
        * number_of_observations ** (-1 / 5)
    )

    kde_bandwidth = max(
        kde_bandwidth,
        0.05,
    )

    kde_smoothing = 1.0
    kde_bandwidth *= kde_smoothing

    max_density = float(
        density_values.max()
    )

    kde_x = np.linspace(
        0,
        max(
            max_density,
            1.0,
        ),
        600,
    )

    kde_log_x = np.log1p(kde_x)

    standardised_distances = (
        kde_log_x[:, None]
        - log_density_values[None, :]
    ) / kde_bandwidth

    kde_log_y = np.mean(
        np.exp(
            -0.5
            * standardised_distances**2
        )
        / (
            kde_bandwidth
            * np.sqrt(2 * np.pi)
        ),
        axis=1,
    )

    kde_y = kde_log_y / (kde_x + 1)

    interval_widths = np.diff(kde_x)

    interval_areas = (
        (kde_y[:-1] + kde_y[1:])
        / 2
        * interval_widths
    )

    total_area = float(
        np.sum(interval_areas)
    )

    if total_area > 0:
        kde_y = kde_y / total_area

    normalized_interval_areas = (
        (kde_y[:-1] + kde_y[1:])
        / 2
        * interval_widths
    )

    cumulative_probability = np.concatenate(
        (
            [0.0],
            np.cumsum(
                normalized_interval_areas
            ),
        )
    )

    median_density = float(
        np.interp(
            0.5,
            cumulative_probability,
            kde_x,
        )
    )

    figure.add_trace(
        go.Scatter(
            name="Overall likelihood",
            x=kde_x,
            y=kde_y,
            mode="lines",
            line={
                "color": "#222222",
                "width": 4,
                "shape": "spline",
            },
            yaxis="y2",
            legendgroup="Overall",
            hovertemplate=(
                "<b>Overall likelihood</b><br>"
                f"{density_label}: "
                f"%{{x{density_format}}}<br>"
                "Estimated probability density: "
                "%{y:.5f}"
                "<extra></extra>"
            ),
        )
    )

    figure.add_vline(
        x=median_density,
        line={
            "color": "#222222",
            "width": 2,
            "dash": "dot",
        },
        annotation={
            "text": (
                "50% below "
                f"{median_density:.0f} events"
            ),
            "showarrow": False,
            "textangle": -90,
            "xanchor": "right",
            "yanchor": "top",
            "bgcolor": (
                "rgba(255, 255, 255, 0.85)"
            ),
            "bordercolor": "#222222",
            "borderwidth": 1,
            "borderpad": 4,
        },
        annotation_position="top right",
    )


def _apply_density_histogram_design(
    figure: go.Figure,
    title: str,
    xaxis_title: str,
) -> None:
    """Apply the shared design to a feeling-density histogram.

    Args:
        figure: Plotly figure to style.
        title: Title displayed above the histogram.
        xaxis_title: Title displayed beneath the x-axis.

    """
    figure.update_layout(
        title={
            "text": title,
            "x": 0.5,
            "xanchor": "center",
        },
        autosize=True,
        height=700,
        barmode="stack",
        bargap=0.05,
        xaxis={
            "title": xaxis_title,
            "rangemode": "tozero",
            "tickmode": "auto",
            "gridcolor": "#EEEEEE",
        },
        yaxis={
            "title": "Number of group-task pairs",
            "rangemode": "tozero",
            "dtick": 1,
            "gridcolor": "#D9D9D9",
        },
        yaxis2={
            "title": "Estimated probability density",
            "overlaying": "y",
            "side": "right",
            "rangemode": "tozero",
            "showgrid": False,
            "tickformat": ".4f",
        },
        legend={
            "title": {
                "text": "Group prefix and task",
            },
            "orientation": "h",
            "yanchor": "top",
            "y": -0.18,
            "xanchor": "center",
            "x": 0.5,
        },
        margin={
            "l": 90,
            "r": 110,
            "t": 100,
            "b": 210,
        },
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font={
            "family": "Arial",
            "size": 13,
        },
        hovermode="closest",
    )


def _create_density_histogram(
    density_data: pl.DataFrame,
    plot_path: Path,
    title: str,
    xaxis_title: str,
    histogram_group: str,
    histogram_density_label: str,
    histogram_density_format: str,
    kde_density_label: str,
    kde_density_format: str,
    plot_description: str,
    logger: logging.Logger,
) -> None:
    """Add the histogram traces ->
       Add the KDE curve and median marker ->
       Apply the shared histogram design ->
       Save the completed figure
    """
    logger.info(
        "Creating %s at %s",
        plot_description,
        plot_path,
    )

    try:
        plot_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        figure = go.Figure()

        _add_density_histogram_traces(
            figure=figure,
            density_data=density_data,
            histogram_group=histogram_group,
            density_label=histogram_density_label,
            density_format=histogram_density_format,
        )

        _add_density_kde_and_median(
            figure=figure,
            density_data=density_data,
            density_label=kde_density_label,
            density_format=kde_density_format,
        )

        _apply_density_histogram_design(
            figure=figure,
            title=title,
            xaxis_title=xaxis_title,
        )

        figure.write_html(
            plot_path,
            include_plotlyjs=True,
            full_html=True,
            config={
                "responsive": True,
                "displaylogo": False,
            },
        )

    except Exception:
        logger.exception(
            "Failed to create %s at %s",
            plot_description,
            plot_path,
        )
        raise

    logger.info(
        "Created %s at %s",
        plot_description,
        plot_path,
    )


def _create_feeling_density_histogram(
    datasets: dict[str, dict[Any, pl.DataFrame]],
    output_path: str,
    plot_feeling_cols: list[str],
    logger: logging.Logger,
) -> None:
    """Calculate observed feeling totals ->
       Create and save the observed feeling-density histogram
    """
    density_data = _create_observed_density_data(
        datasets=datasets,
        plot_feeling_cols=plot_feeling_cols,
    )

    plot_path = (
        Path(output_path)
        / "feeling_density_histogram.html"
    )

    _create_density_histogram(
        density_data=density_data,
        plot_path=plot_path,
        title=(
            "Distribution of feeling occurrences "
            "across group-task pairs"
        ),
        xaxis_title=(
            "Total occurrences across the "
            f"{len(plot_feeling_cols)} plotted feelings"
        ),
        histogram_group="feeling_density",
        histogram_density_label=(
            "Feeling-density bin"
        ),
        histogram_density_format="",
        kde_density_label="Feeling events",
        kde_density_format=":.0f",
        plot_description=(
            "feeling-density histogram"
        ),
        logger=logger,
    )


## MAIN FUNCTIONALITY ##
def generate_plots(
    input_dir: str | Path,
    output_path: str,
    plot_feeling_cols: list[str],
    logger: logging.Logger,
) -> None:
    """Import and partition the standardised FEA data ->
       Create the task-level feeling bar chart ->
       Create the observed feeling-density histogram ->
       Create the estimated ten-minute density histogram
    """
    datasets = _import_and_group_data(
        csv_path=input_dir,
        logger=logger,
    )

    _create_bar_chart(
        datasets=datasets,
        output_path=output_path,
        plot_feeling_cols=plot_feeling_cols,
        logger=logger,
    )

    _create_feeling_density_histogram(
        datasets=datasets,
        output_path=output_path,
        plot_feeling_cols=plot_feeling_cols,
        logger=logger,
    )

    _create_ten_minute_feeling_density_histogram(
        datasets=datasets,
        output_path=output_path,
        plot_feeling_cols=plot_feeling_cols,
        logger=logger,
    )


def _create_ten_minute_feeling_density_histogram(
    datasets: dict[str, dict[Any, pl.DataFrame]],
    output_path: str,
    plot_feeling_cols: list[str],
    logger: logging.Logger,
) -> None:
    """Estimate ten-minute feeling totals ->
       Create and save the estimated feeling-density histogram
    """
    density_data = _create_ten_minute_density_data(
        datasets=datasets,
        plot_feeling_cols=plot_feeling_cols,
        logger=logger,
    )

    plot_path = (
        Path(output_path)
        / "ten_minute_feeling_density_histogram.html"
    )

    _create_density_histogram(
        density_data=density_data,
        plot_path=plot_path,
        title=(
            "Estimated 10-minute distribution of feeling "
            "occurrences across group-task pairs"
        ),
        xaxis_title=(
            "Estimated feeling occurrences over 10 minutes"
        ),
        histogram_group=(
            "ten_minute_feeling_density"
        ),
        histogram_density_label=(
            "Estimated 10-minute density"
        ),
        histogram_density_format=":.1f",
        kde_density_label=(
            "Estimated 10-minute events"
        ),
        kde_density_format=":.1f",
        plot_description=(
            "estimated 10-minute feeling-density histogram"
        ),
        logger=logger,
    )


