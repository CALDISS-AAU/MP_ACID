# Feelings Investigation Pipeline

## Overview

The `Feelings_Investigation` pipeline creates interactive visualisations from
the standardised facial-expression analysis (FEA) datasets. It generates
figures showing when feelings are detected and how long uninterrupted
detection sequences continue for each task and participant group.

Every FEA CSV file matching the configured input pattern is processed
independently. The certainty threshold is extracted from its filename and
included in the corresponding figure titles and output directories.

## Visualisations

The pipeline creates two types of visualisation for each task:

1. **Feelings over time**
   - Creates one subplot per participant group.
   - Plots each configured feeling as a binary step line against time.
   - Uses a shared time range across the group subplots.
2. **Feeling-sequence distributions**
   - Finds uninterrupted sequences of positive detections for each feeling.
   - Displays sequence lengths using combined box and half-violin plots.
   - Creates one subplot per participant group.

All figures are saved as standalone interactive HTML files with scroll zoom,
responsive sizing, and controls for showing or hiding feelings.

## Inputs

Inputs are configured in `feelings_investigation_main.py` and are read
relative to `INPUT_BASE`, which defaults to the project root:

| Input variable | Default value |
| --- | --- |
| `INPUT_DIR_FEA_DATA_FOLDER` | `Data/Standardise_Data` |
| `INPUT_FILE_PATTERN` | `FEA_*.csv` |

Input filenames should follow the `FEA_<certainty>.csv` pattern. Each dataset
must contain the following columns:

- `Timestamp`
- `group`
- `task`
- Every configured feeling column

## Configuration

The default feeling columns are:

- Anger
- Contempt
- Confusion
- Disgust
- Engagement
- Fear
- Joy
- Sadness
- Surprise

This list can be changed in `feelings_investigation_main.py`. The plotting
functions assign each feeling a consistent colour and support up to 12 unique
feelings with the current colour palette.

## Outputs

Feeling-over-time figures are written to:

```text
Pipelines/Feelings_Investigation/Data/Plots/Graphs/FEA_<certainty>/
task_<task>.html
```

Sequence-distribution figures are written to:

```text
Pipelines/Feelings_Investigation/Data/Plots/Box/FEA_<certainty>/
sequence_lengths_task_<task>.html
```

Task identifiers are sanitised before being used in filenames. Output
directories are created automatically when required.

## Running the pipeline

Run the pipeline from the project root:

```bash
uv run python -m Pipelines.Feelings_Investigation.feelings_investigation_main
```

The standardised FEA files must exist before running this pipeline.

## Logging

Plot-generation messages are written to:

```text
Pipelines/Feelings_Investigation/Logs/plots.log
```

The plot log is incorporated into:

```text
Pipelines/Feelings_Investigation/Logs/full_pipeline.log
```