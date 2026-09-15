# MP_ACID Repository
This repository is part of the MP_ACID project and contains the core data processing and analysis pipelines.

Analysis of concurrent interaction data. Detecting usability and user experience issues (UUEIs) in using AI-assistant on AUB Primo and associated features.

## Project Structure
The overall structure of this project can be seen below:
```
.
├── Data/  # Data shared across pipelines
├── Output/  # Data generated for deliveries
├── Pipelines/
│   ├── Standardise_Data/
│   │   ├── Data/
│   │   ├── Functions/
│   │   │   ├── standardise_and_combine_FEA.py
│   │   │   ├── standardise_and_combine_mouse_tracking.py
│   │   │   └── standardise_and_combine_transcriptions.py
│   │   ├── Logs/
│   │   ├── Tests/
│   │   ├── standardise_data_main.py
│   │   └── standardise_data_README.md
│   ├── Data_Combination/
│   │   ├── Data/
│   │   ├── Functions/
│   │   │   └── extract_and_combine.py
│   │   ├── Logs/
│   │   ├── Tests/
│   │   ├── data_combination_main.py
│   │   └── data_combination_README.md
│   ├── Feelings_Investigation/
│   │   ├── Data/
│   │   ├── Functions/
│   │   │   └── plots.py
│   │   ├── Logs/
│   │   ├── Tests/
│   │   ├── feelings_investigation_main.py
│   │   └── feelings_investigation_README.md
│   ├── Bertopic/
│   │   ├── Data/
│   │   ├── Functions/
│   │   │   └── model_training.py
│   │   ├── Logs/
│   │   ├── Tests/
│   │   ├── bertopic_main.py
│   │   └── bertopic_README.md
│   └── Event_Statistics/
│       ├── Data/
│       ├── Functions/
│       │   ├── confirm_feeling_events.py
│       │   ├── generate_plots.py
│       │   └── generate_table.py
│       ├── Logs/
│       ├── Tests/
│       ├── event_statistics_main.py
│       └── event_statistics_README.md
├── Shared_Functions/
│   ├── Pipeline_Functions/
│   │   ├── pipeline_generator.py
│   │   └── wipe_pipeline_data.py
│   └── logger_functionality.py
├── README.md
├── main.py  # Combines and runs all pipelines
├── pyproject.toml
├── test.py  # Combines all pipeline tests
└── uv.lock
```

## Shared Functions

The `Shared_Functions/` directory contains reusable functionality that
can be used across multiple pipelines within the project.

### pipeline_generator.py

The `pipeline_generator.py` module provides functionality for generating
new standardized pipeline folder structures directly from the terminal.

Before using the generator, navigate to the project root directory
containing the `pyproject.toml` file and install the project in
editable mode:

```bash
cd my_project
pip install -e .
```

New pipelines can then be created from any folder within the project 
root using:

```bash
create-pipeline pipeline_name
```

Examples:

```bash
create-pipeline data cleaning
```

```bash
create-pipeline MY very_oWn Test_Pipeline
```

Pipeline names may contain spaces, underscores, mixed casing, and
numbers. Only alphanumeric characters will be included in the final
pipeline name. Spaces and special characters are treated as word
separators and converted to underscores.

### wipe_pipeline_data.py

The `wipe_pipeline_data.py` module provides functionality for clearing
generated files from a pipeline's `Data/` and `Logs/` directories.

Clear a pipeline from anywhere within the project using:

```bash
clear-pipeline pipeline_name
```

For example:

```bash
clear-pipeline data combination
```

The command preserves the pipeline directories and their `.gitkeep` files.
Files stored in the project-level `Data/` and `Output/` directories are not
affected.

### logger_functionality.py

The `logger_functionality.py` module provides shared logging functionality
for all pipelines.

The `setup_logger()` function creates and returns a logger that writes to a
specified log file. It automatically creates the parent directory when
necessary and can either overwrite the existing log or append new messages
to it.

The `rebuild_pipeline_log()` function combines the logs from individual
pipeline steps into a single `full_pipeline.log` file. Step logs are added in
the order provided, while paths to missing log files are skipped.

## Requirements

The project requires Python 3.12 or later. Its dependencies are defined in
`pyproject.toml` and locked in `uv.lock`.

The primary dependencies include:

- BERTopic
- Plotly
- Polars
- Sentence Transformers
- spaCy
- XlsxWriter

Install the project dependencies from the project root using:

```bash
uv sync
```

## Pipelines

The project consists of five pipelines that run in the following order:

1. `Standardise_Data`
2. `Data_Combination`
3. `Feelings_Investigation`
4. `Bertopic`
5. `Event_Statistics`

### Standardise Data

The `Standardise_Data` pipeline converts raw transcription, mouse-tracking,
and facial-expression analysis exports into consistent datasets. It adds
group and task identifiers, standardises timestamps, removes unused data,
and combines files from the same source.

For detailed information, see:

```text
Pipelines/Standardise_Data/standardise_data_README.md
```

### Data Combination

The `Data_Combination` pipeline combines standardised facial-expression,
transcription, and input-event data. It associates detected feelings with
transcription intervals and adds the configured amount of surrounding
transcription context.

For detailed information, see:

```text
Pipelines/Data_Combination/data_combination_README.md
```

### Feelings Investigation

The `Feelings_Investigation` pipeline generates interactive visualisations
for examining how feelings occur over time and how feeling sequences are
distributed across the data.

For detailed information, see:

```text
Pipelines/Feelings_Investigation/feelings_investigation_README.md
```

### BERTopic

The `Bertopic` pipeline trains and saves BERTopic models from the combined
transcription data. It supports testing multiple combinations of UMAP,
HDBSCAN, and vectorisation parameters and generates an interactive topic
overview for each trained model.

For detailed information, see:

```text
Pipelines/Bertopic/bertopic_README.md
```

### Event Statistics

The `Event_Statistics` pipeline produces descriptive tables and plots for
registered feeling and input events. It also evaluates whether manually
registered feelings are confirmed by facial-expression detections within a
configured time window.

For detailed information, see:

```text
Pipelines/Event_Statistics/event_statistics_README.md
```

### Screengetter

The `Screengetter` pipeline analyzes where in the UI events are occurring. It extracts frames every second in the five seconds leading up to an event and compares each frame with a reference set to produce annotations. Produces an annotated dataset along with array of frames in the event windows along with barplots of UI trajectory counts.

For detailed information, see:

```text
Pipelines/Screengetter/screengetter_README.md
```

## Running the project

Before running the project, review the input paths and configurable parameters
defined in each pipeline's main script.

Run all pipelines in their required order from the project root using:

```bash
uv run python -m main
```

The complete workflow runs:

```text
Standardise Data
        ↓
Data Combination
        ↓
Feelings Investigation
        ↓
BERTopic
        ↓
Event Statistics
```

Each pipeline depends on data produced by earlier stages. Consequently, the
complete workflow should be run in the documented order unless the required
upstream outputs already exist.

BERTopic training may require substantial processing time and memory. The
configured sentence-transformer model must also be available locally or
downloadable when the pipeline runs.

### Running individual pipelines

Individual pipelines can be run from the project root using:

```bash
uv run python -m Pipelines.Standardise_Data.standardise_data_main
uv run python -m Pipelines.Data_Combination.data_combination_main
uv run python -m Pipelines.Feelings_Investigation.feelings_investigation_main
uv run python -m Pipelines.Bertopic.bertopic_main
uv run python -m Pipelines.Event_Statistics.event_statistics_main
```

When running a pipeline individually, all required input data and upstream
pipeline outputs must already exist.

## Configuration

Changeable paths and processing parameters are defined in the relevant
pipeline main scripts rather than within their function scripts.

Before running the complete project, review the following configuration:

- Set `INPUT_DIR_BASE` in `standardise_data_main.py` to the user-specific
  location of the raw iMotions data.
- Check the input and output paths used by each subsequent pipeline.
- Set the manual-registration input path in `event_statistics_main.py`.
- Select the required facial-expression certainty thresholds.
- Select the feeling columns included in the analyses.
- Configure the preceding and succeeding transcription context.
- Configure the BERTopic parameter lists.
- Configure the feeling-confirmation time window.

The BERTopic parameters are stored as lists, even when only one value is
configured. Additional values can be added to these lists to train models
using multiple parameter combinations.

## Outputs

Datasets shared between pipelines are written to the project-level `Data/`
directory. Files intended for final delivery can be written to `Output/`.

Pipeline-specific outputs, such as interactive visualisations and trained
models, are stored in the relevant pipeline's `Data/` directory.

Exact output paths and filenames are documented in the individual pipeline
README files.

## Logging

Each pipeline records its processing stages in its `Logs/` directory.
Individual function logs are combined into the pipeline's
`full_pipeline.log` file when the pipeline finishes.

The individual pipeline README files document the logs generated by each
pipeline.