# Screengetter

This pipeline processes events data from the Data_Combination pipeline and analyzes what part of the UI the events are occurring. 

Each feeling_timestamp is processed as follows:
- Extract frames every second in the 5 seconds leading up to the event (-500ms buffer to allow for reaction time).
- Aggregate frames based on image similarity into intervals (from, to, frame)
- Annotate frames based on UI location using a reference set
- Aggregate frames into "UI trajectories" (are changing in the UI occurring within the event window?)

Finally, the processed events are analyzed providing the following output: 
- A barplot of number of events associated with unique UI trajectories
- A barplot of number of events associated with unique UI trajectories stratified by task
- A combined dataset (csv) of feeling timestamps and associated frames with their annotation
    - NOTE: Frames are stored separately as individual .npy files. .csv file contains the filename of the frame array.

## Run as a module

From the project root:

```bash
uv run python -m Pipelines.Screengetter.screengetter_main
```

Configure the static variables in `screengetter_main.py` before running; the module takes no command-line arguments.

## Main outputs

Results are saved in `OUTPUT_RESULTS` (default: `Output/Screengetter/`):

- `tag_trajectories_total.html`: interactive barplot of event tag trajectories across all tasks.
- `tag_trajectories_by_task.html`: interactive barplot of event tag trajectories grouped by task.
- `event_frames_tagged.csv`: tagged event frames, including group, task, event timestamp, frame intervals, tags, tag trajectories, and saved frame-array paths.

## Required static variables

| Variable | Purpose |
| --- | --- |
| `INPUT_EVENTS_PATH` | Path to the input events CSV. |
| `INPUT_DIR_SCREENRECS` | Directory containing the corresponding screen recordings. |
| `OUTPUT_REFERENCE` | Reference directory containing the actual image arrays used for comparison and `resolutions.json`. Defaults to `Pipelines/Screengetter/Data/Reference/`. |
| `REFERENCE_SET` | Path to the manually tagged reference JSON. Defaults to `OUTPUT_REFERENCE / "reference_lookup_tagged.json"`. |

A reusable reference requires **both `REFERENCE_SET` and `OUTPUT_REFERENCE`**: the JSON supplies annotations and paths, while the reference directory supplies the image arrays to compare against. Keep `VIDEO_RESOLUTIONS` pointing to the matching `resolutions.json`.

### `create_reference`: manual annotation

Unless an existing reference is provided through `REFERENCE_SET`, the module calls `create_reference`, writes a reference set to `OUTPUT_REFERENCE`, and stops for manual annotation. Reference creation currently samples 10 recordings, so at least 10 supported videos (`.mp4` or `.wmv`) are required.

1. Copy the generated `reference_lookup.json` to `reference_lookup_tagged.json`.
2. Inspect each reference frame and add a `"tag"` key to every entry with the relevant annotation, for example `"tag": "settings"`. Preserve the existing fields.
3. Rerun the module to tag event frames and generate the outputs.

By default, `screengetter_main.py` expects the reference JSON to be named exactly **`reference_lookup_tagged.json`**. If you use another filename or location, update `REFERENCE_SET` accordingly.
