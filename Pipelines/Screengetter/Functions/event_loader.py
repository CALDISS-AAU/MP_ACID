"""Load event data for the Screengetter pipeline."""

## IMPORTS ##
from pathlib import Path
import logging

import polars as pl

## _______ ##

## LOGGER ## 
logger = logging.getLogger(__name__)

## MAIN FUNCTIONALITY ##
def load_events(input_file: Path) -> pl.DataFrame:
    """Read an events CSV, preserving group and task IDs as strings."""

    event_df = pl.read_csv(
        input_file, 
        columns = ["group", "task", "feeling_timestamp", "present_feelings"], 
        schema_overrides={
            "group": pl.String,
            "task": pl.String,
        })

    return event_df
