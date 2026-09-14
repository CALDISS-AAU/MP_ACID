# Standardise Data Pipeline

## Overview

The `Standardise_Data` pipeline converts raw transcription, mouse-tracking,
and facial-expression analysis (FEA) exports into consistent CSV datasets for
downstream processing. It adds group and task identifiers, standardises task
timestamps where applicable, removes unused data, and combines files from the
same data source.

## Processing stages

The pipeline runs the following stages in order:

1. **Transcriptions**
   - Reads every CSV file in the transcription input folder.
   - Extracts the group and task identifiers from each filename.
   - Converts the `start` and `end` columns from seconds to milliseconds.
   - Combines all transcription files into one dataset.
2. **Mouse tracking**
   - Skips the iMotions metadata rows and extracts the group identifier from
     the `#Respondent Name` metadata field.
   - Retains rows between `StartMedia` and `EndMedia` events, inclusive.
   - Extracts task identifiers from `SourceStimuliName`.
   - Resets `Timestamp` so that each task begins at zero milliseconds.
   - Retains the columns required for mouse-tracking analysis and combines all
     files into one dataset.
3. **Facial-expression analysis**
   - Skips the iMotions metadata rows and extracts the group identifier.
   - Retains task intervals and Affectiva AFFDEX measurements.
   - Adds task identifiers and resets timestamps for individual tasks.
   - Retains the configured feeling columns.
   - Converts feeling scores to binary values at each configured certainty
     threshold and writes one combined dataset per threshold.

## Inputs

Input paths are configured in `standardise_data_main.py`. Set
`INPUT_DIR_BASE` to the user-specific location of the raw iMotions data. The
remaining input directories are derived from this base path:

| Input variable | Path relative to `INPUT_DIR_BASE` |
| --- | --- |
| `INPUT_DIR_TRANSCRIPTIONS_FOLDER` | `Audio_PRIMO_resp_transcribed/csv` |
| `INPUT_DIR_MOUSE_TRACKING_FOLDER` | `MouseData` |
| `INPUT_DIR_FEA_FOLDER` | `FEA/DDD-F2026-RespCam-FEA_PRIMO` |

The transcription filename stem must contain three underscore-separated
parts: a prefix, group identifier, and task identifier. Mouse-tracking and FEA
files must contain the iMotions columns and metadata fields referenced by their
processing functions.

## Outputs

By default, outputs are written relative to the project root:

| Data source | Output |
| --- | --- |
| Transcriptions | `Data/Standardise_Data/transcriptions.csv` |
| Mouse tracking | `Data/Standardise_Data/mouse_tracking.csv` |
| FEA | `Data/Standardise_Data/FEA_<threshold>.csv` |

The default FEA certainty thresholds are `75`, `80`, `85`, `90`, `95`, and
`99`. The configured feeling columns are Anger, Contempt, Confusion, Disgust,
Engagement, Fear, Joy, Sadness, and Surprise.

## Running the pipeline

Run the pipeline from the project root:

```bash
uv run python -m Pipelines.Standardise_Data.standardise_data_main
```

The pipeline creates output parent directories when required. Input folders
must exist and contain compatible CSV files.

## Logging

Each processing stage writes to its own file in
`Pipelines/Standardise_Data/Logs/`:

- `transcriptions.log`
- `mouse_tracking.log`
- `FEA.log`

After all stages finish, these logs are combined into `full_pipeline.log`.