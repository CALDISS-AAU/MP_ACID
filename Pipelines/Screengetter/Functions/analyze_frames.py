"""Analyze tagged frames using their JSON metadata."""

from pathlib import Path
import logging

import plotly.express as px
import polars as pl

logger = logging.getLogger(__name__)


def analyze_frames(
    framearrays_dir: Path,
    tagged_events_path: Path,
) -> None:
    """Write total and per-task trajectory charts alongside the frame arrays.

    Each feeling event contributes once. Tags follow frame-start order, and
    events containing only unknown tags are excluded. Frame arrays are not read.
    """
    frames = pl.read_json(tagged_events_path)
    if frames.is_empty():
        logger.info("No tagged frames to analyze in %s", tagged_events_path)
        return

    event_keys = ["group", "task", "feeling_timestamp"]
    frames = frames.sort([*event_keys, "frame_start"], maintain_order=True)
    frames = frames.with_columns(
        pl.col("tag").sort_by("frame_end").last().over(event_keys).alias("last_tag"),
        pl.col("tag").str.join("->").over(event_keys).alias("tag_trajectory")
    )
    events = frames.select(
        [*event_keys, "tag_trajectory"]
    ).unique(maintain_order=True)

    total_counts = events.group_by("tag_trajectory").len(name="count").sort(
        ["count", "tag_trajectory"], descending=[True, False]
    )

    task_counts = events.group_by(["task", "tag_trajectory"]).len(name="count").sort(
        ["task", "count", "tag_trajectory"], descending=[False, True, False]
    )

    labels = {"tag_trajectory": "Tag trajectory", "count": "Feeling events", "task": "Task"}
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

    output_dir = Path(framearrays_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for chart, filename in (
        (total_chart, "tag_trajectories_total.html"),
        (task_chart, "tag_trajectories_by_task.html"),
    ):
        chart.update_yaxes(dtick=1)
        output_path = output_dir / filename
        chart.write_html(output_path, include_plotlyjs=True, full_html=True)
        logger.info("Saved tag trajectory chart to %s", output_path)
