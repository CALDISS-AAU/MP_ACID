# Data Combination Pipeline

## Overview

The `Data_Combination` pipeline combines standardised facial-expression
analysis (FEA), transcription, and mouse-tracking data. It identifies
transcription intervals associated with selected feelings and enriches them
with surrounding transcription context, feelings, mouse coordinates, and
input-event sources.

The pipeline processes every configured combination of FEA certainty
threshold and surrounding-sentence counts.

## Processing

For each configuration, the pipeline:

1. Reads the standardised FEA, transcription, and mouse-tracking datasets.
2. Extracts timestamps at which at least one relevant feeling is present.
3. Matches each timestamp to a transcription interval with the same group and
   task identifiers.
4. Adds the configured numbers of preceding and succeeding sentences to the
   extended transcription text.
5. Records all relevant feelings present during the matched interval.
6. Adds mouse coordinates and unique input-event sources recorded during the
   interval.
7. Saves the combined data as CSV and JSON files.

Duplicate transcription intervals are excluded. Events before the first
transcription or after the final transcription are not included. When an event
occurs between two sentences, the matched text contains both surrounding
sentences.

## Inputs

Inputs are configured in `data_combination_main.py` and are read relative to
`INPUT_DIR_BASE`, which defaults to the project root:

| Input variable | Default input |
| --- | --- |
| `INPUT_DIR_FEA_DATA_BASE` | `Data/Standardise_Data` |
| `INPUT_DIR_TRANSCRIPTION_DATA` | `Data/Standardise_Data/transcriptions.csv` |
| `INPUT_DIR_MOUSE_DATA` | `Data/Standardise_Data/mouse_tracking.csv` |

For each certainty threshold, the FEA input is read from
`FEA_<threshold>.csv` inside `INPUT_DIR_FEA_DATA_BASE`.

The datasets must contain matching `group` and `task` identifiers. The
pipeline also expects the timestamp, transcription, feeling, and input-event
columns created by the `Standardise_Data` pipeline.

## Configuration

The default configuration processes:

- FEA certainty thresholds: `75` and `85`
- Preceding sentences: `0`, `1`, and `2`
- Succeeding sentences: `0` and `1`
- Feelings: Anger, Contempt, Confusion, Disgust, Fear, Sadness, and Surprise

This produces 12 parameter combinations. These values can be changed in
`data_combination_main.py`.

## Outputs

Each parameter combination produces one CSV file and one JSON file beneath
`Data/Data_Combination/`. Filenames follow this pattern:

```text
combined_data_when_feelings_pc<certainty>_pre<preceding>_post<succeeding>
```

The CSV output stores list columns as pipe-separated strings. The JSON output
preserves those columns as lists. These columns include:

- `present_feelings`
- `MouseCoordinates`
- `InputEventSources`

## Running the pipeline

Run the pipeline from the project root:

```bash
uv run python -m Pipelines.Data_Combination.data_combination_main
```

The output directory is created automatically when required. All configured
input files must already exist.

## Logging

Processing messages are written to:

```text
Pipelines/Data_Combination/Logs/extract_feelings_timestamp.log
```

The step log is incorporated into:

```text
Pipelines/Data_Combination/Logs/full_pipeline.log
```