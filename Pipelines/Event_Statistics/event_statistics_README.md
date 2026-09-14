# Event Statistics Pipeline

## Overview

The `Event_Statistics` pipeline summarises standardised facial-expression
analysis (FEA) data and compares machine-detected feelings with manually
registered events. It produces an Excel summary workbook, interactive Plotly
figures, and a feeling-confirmation report.

## Processing stages

The pipeline runs three stages in order:

1. **Table generation**
   - Imports the standardised FEA dataset and partitions it by group and task.
   - Calculates feeling totals for every group-task combination.
   - Calculates totals by group, by task, and across the complete dataset.
   - Writes sum and percentage worksheets to an Excel workbook.
2. **Plot generation**
   - Creates a grouped bar chart of feeling occurrences by task.
   - Creates a histogram of observed feeling totals by group-task pair.
   - Estimates feeling totals over ten minutes and creates a second density
     histogram.
   - Adds kernel-density estimates and median markers to both histograms.
3. **Feeling confirmation**
   - Imports manually registered events and machine-generated FEA data.
   - Matches records by group and task.
   - Inspects machine detections within five seconds before and after each
     manual event.
   - Reports detected feelings and their individual counts.

The table and plot scripts import and partition the FEA dataset independently.

## Inputs

Input paths are configured in `event_statistics_main.py`:

| Input variable | Default input |
| --- | --- |
| `INPUT_DIR_FEA` | `Data/Standardise_Data/FEA_85.csv` |
| `INPUT_DIR_MANUAL_REGISTRATIONS` | User-specific manual-event CSV file |

`INPUT_DIR_MANUAL_REGISTRATIONS` must be changed to the location of the user's
manual-event dataset.

The standardised FEA dataset must contain `Row`, `Timestamp`, `group`, `task`,
and every configured feeling column. The manual dataset uses semicolon
separators and must contain `Group`, `Stimuli`, `Start`, and `Task`. Manual
timestamps must use the `mm:ss` format.

## Configuration

`FEELING_COLUMNS` contains all feelings included in the Excel tables:

- Anger
- Contempt
- Confusion
- Disgust
- Engagement
- Fear
- Joy
- Sadness
- Surprise

`PLOT_FEELING_COLUMNS` excludes Joy and Engagement. It is used for the plots
and the feeling-confirmation report.

`CONFIRMATION_TIME_WINDOW_MS` defaults to `5_000`. Machine detections are
therefore inspected from five seconds before through five seconds after each
manual timestamp. The lower boundary is restricted to zero milliseconds.

## Outputs

Outputs are written beneath `Data/Event_Statistics/`:

| Output | Description |
| --- | --- |
| `sum_table.xlsx` | Sum and percentage worksheets by group and task |
| `feeling_bar_chart.html` | Feeling totals and group statistics by task |
| `feeling_density_histogram.html` | Observed group-task feeling totals |
| `ten_minute_feeling_density_histogram.html` | Ten-minute estimates |
| `feeling_confirmation.csv` | Manual and machine event comparison |

The HTML files are standalone interactive Plotly visualisations. The density
histograms distinguish group prefixes and tasks by colour, include an overall
kernel-density curve, and mark the estimated median with a dotted line.

## Running the pipeline

Run the pipeline from the project root:

```bash
uv run python -m Pipelines.Event_Statistics.event_statistics_main
```

Both input files must exist before the pipeline runs. Output directories are
created automatically when required.

## Logging

Each processing stage writes to its own file in
`Pipelines/Event_Statistics/Logs/`:

- `table_generation.log`
- `plot_generation.log`
- `confirm_feeling_events.log`

After all stages finish, these logs are combined into `full_pipeline.log`.