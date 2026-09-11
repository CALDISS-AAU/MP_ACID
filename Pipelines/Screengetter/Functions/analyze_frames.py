"""Analyze tagged frames using their JSON metadata."""

## IMPORTS ##
from pathlib import Path
import logging

import plotly.express as px
import polars as pl

## LOGGER ## 
logger = logging.getLogger(__name__)

## HELPER FUNCTIONS ##
def _prepare_and_store_df(
    frames: pl.DataFrame,
    output_dir: Path
    ):
    """Prepare output dataset for annotated events and frames"""

    event_keys = ["group", "task", "feeling_timestamp"]
    frames = frames.sort([*event_keys, "frame_start"], maintain_order=True)
    frames = frames.with_columns(
        pl.col("tag").sort_by("frame_end").last().over(event_keys).alias("last_tag"),
        pl.col("tag").str.join("->").over(event_keys).alias("tag_trajectory")
    )
    events = frames.select(
        [*event_keys, "tag_trajectory"]
    ).unique(maintain_order=True)

    events_out = events.join(
        frames,
        on=event_keys,
        how="left"
    )

    path_out = output_dir / "event_frames_tagged.csv"
    events_out.write_csv(path_out)

    return events


def _count_frame_tags(
    events: pl.DataFrame
    ):
    """Aggregate annotated data into counted tag trajectories. One DataFrame for total and one stratified by task."""  

    total_counts = events.group_by("tag_trajectory").len(name="count").sort(
        ["count", "tag_trajectory"], descending=[True, False]
    )

    task_counts = events.group_by(["task", "tag_trajectory"]).len(name="count").sort(
        ["task", "count", "tag_trajectory"], descending=[False, True, False]
    )

    return total_counts, task_counts

def _plot_counts(
    total_counts: pl.DataFrame,
    task_counts: pl.DataFrame
    ):
    """Plot tag trajectories for total count and task count as separate plotly bar charts"""
    
    labels = {"tag_trajectory": "Tag trajectory", "count": "Events", "task": "Task"}
    
    total_chart = px.bar(
        total_counts,
        x="tag_trajectory",
        y="count",
        labels=labels,
        title="Tag trajectories across all tasks",
    )
    
    task_chart = px.bar(
        task_counts,
        x="tag_trajectory",
        y="count",
        color="task",
        barmode="group",
        labels=labels,
        title="Tag trajectories by task",
    )

    return total_chart, task_chart

def _store_plots(
    total_chart: px.bar,
    task_chart: px.bar,
    output_dir: Path
    ):
    """Store bar charts as HTML"""

    for chart, filename in (
        (total_chart, "tag_trajectories_total.html"),
        (task_chart, "tag_trajectories_by_task.html"),
        ):

        chart.update_yaxes(dtick=1)
        output_path = output_dir / filename

        chart.write_html(output_path, include_plotlyjs=True, full_html=True)
        
        logger.info("Saved tagged event plot to %s", output_path)


## MAIN FUNCTIONS ##
def analyze_frames(
    framearrays_dir: Path,
    tagged_events_path: Path,
    output_dir: Path
) -> None:
    """Write total and per-task trajectory charts alongside the frame arrays.

    Each feeling event contributes once. Tags follow frame-start order.
    """

    output_dir.mkdir(parents=True, exist_ok=True)

    frames = pl.read_json(tagged_events_path)
    
    events = _prepare_and_store_df(frames, output_dir)
    
    total_counts, task_counts = _count_frame_tags(events)

    total_chart, task_chart = _plot_counts(total_counts, task_counts)

    _store_plots(total_chart, task_chart, output_dir)