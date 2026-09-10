"""Example helper functions for the pipeline."""

## IMPORTS ##
import logging
from pathlib import Path
from typing import Any

import polars as pl
import xlsxwriter
import plotly.graph_objects as go
from plotly.subplots import make_subplots
## _______ ##

## STATIC VARIABLES ##
FEELING_COLUMNS = [
    "Anger",
    "Contempt",
    "Confusion",
    "Disgust",
    "Engagement",
    "Fear",
    "Joy",
    "Sadness",
    "Surprise",
]

DISPLAY_COLUMNS = FEELING_COLUMNS + ["Total"]

PLOT_FEELING_COLUMNS = [
    feeling
    for feeling in FEELING_COLUMNS
    if feeling not in {"Joy", "Engagement"}
]
## ________________ ##

## HELPER FUNCTIONS ##
def _import_and_group_data(
    csv_path: str,
    logger: logging.Logger,
) -> dict[str, dict[Any, pl.DataFrame]]:
    logger.info("Reading data from %s", csv_path)

    try:
        df = pl.read_csv(csv_path)
        logger.info(
            "Imported %d rows and %d columns",
            df.height,
            df.width,
        )

        df = df.drop("Row", "Timestamp")
        logger.debug("Dropped columns: Row, Timestamp")

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
                ["group", "task"],
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
        logger.exception("Failed to import and group data from %s", csv_path)
        raise


def _calculate_feeling_sums(
    df: pl.DataFrame,
) -> list[int]:
    """Return the nine feeling sums followed by their total."""
    feeling_sums = [
        int(value) if value is not None else 0
        for value in df.select(
            pl.col(FEELING_COLUMNS).sum()
        ).row(0)
    ]

    return feeling_sums + [sum(feeling_sums)]


def _add_rows(
    rows: list[list[int]],
) -> list[int]:
    """Add several rows of feeling sums column by column."""
    totals = [0] * len(DISPLAY_COLUMNS)

    for row in rows:
        for index, value in enumerate(row):
            totals[index] += value

    return totals


def _convert_to_percentages(
    values: list[int],
) -> list[float]:
    """Convert feeling sums into percentages."""
    total = values[-1]

    if total == 0:
        return [0.0] * len(values)

    return [
        value / total
        for value in values[:-1]
    ] + [1.0]


def _write_table_sheet(
    workbook: xlsxwriter.Workbook,
    sheet_name: str,
    groups: list[Any],
    tasks: list[Any],
    table_data: dict[
        tuple[Any, Any],
        list[int] | list[float] | None,
    ],
    as_percentage: bool,
) -> None:
    """Write and format one sum or percentage worksheet."""
    worksheet = workbook.add_worksheet(sheet_name)

    number_format = "0%" if as_percentage else "#,##0"

    main_header_format = workbook.add_format(
        {
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "left": 2,
            "right": 2,
            "bg_color": "#D9EAF7",
        }
    )

    group_header_format = workbook.add_format(
        {
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "right": 2,
            "bg_color": "#D9EAF7",
        }
    )

    total_label_format = workbook.add_format(
        {
            "bold": True,
            "align": "left",
            "valign": "vcenter",
            "border": 1,
            "top": 2,
            "right": 2,
            "bg_color": "#E2F0D9",
        }
    )

    format_cache: dict[tuple[Any, ...], Any] = {}

    def get_feeling_header_format(
        thick_left_border: bool,
        thick_right_border: bool,
    ) -> Any:
        """Create or reuse a feeling-header format."""
        cache_key = (
            "header",
            thick_left_border,
            thick_right_border,
        )

        if cache_key not in format_cache:
            format_cache[cache_key] = workbook.add_format(
                {
                    "bold": True,
                    "align": "center",
                    "valign": "bottom",
                    "text_wrap": True,
                    "border": 1,
                    "left": 2 if thick_left_border else 1,
                    "right": 2 if thick_right_border else 1,
                    "bg_color": "#EAF3F8",
                }
            )

        return format_cache[cache_key]

    def get_data_format(
        alternate_row: bool,
        total_row: bool,
        total_task: bool,
        thick_left_border: bool,
        thick_right_border: bool,
        missing: bool,
    ) -> Any:
        """Create or reuse a data-cell format."""
        cache_key = (
            "data",
            alternate_row,
            total_row,
            total_task,
            thick_left_border,
            thick_right_border,
            missing,
        )

        if cache_key not in format_cache:
            if total_row:
                background_colour = "#E2F0D9"
            elif alternate_row:
                background_colour = "#F2F2F2"
            else:
                background_colour = "#FFFFFF"

            format_properties = {
                "bold": total_row or total_task,
                "align": "center",
                "valign": "vcenter",
                "border": 1,
                "left": 2 if thick_left_border else 1,
                "right": 2 if thick_right_border else 1,
                "top": 2 if total_row else 1,
                "bg_color": background_colour,
            }

            if missing:
                format_properties["font_color"] = "#666666"
            else:
                format_properties["num_format"] = number_format

            format_cache[cache_key] = workbook.add_format(
                format_properties
            )

        return format_cache[cache_key]

    # Group header spanning both header rows.
    worksheet.merge_range(
        0,
        0,
        1,
        0,
        "Group",
        group_header_format,
    )

    columns_per_task = len(DISPLAY_COLUMNS)
    task_headers = tasks + ["Total"]

    # Task and feeling headers.
    for task_index, task in enumerate(task_headers):
        first_column = 1 + task_index * columns_per_task
        last_column = first_column + columns_per_task - 1

        worksheet.merge_range(
            0,
            first_column,
            0,
            last_column,
            str(task),
            main_header_format,
        )

        for feeling_index, feeling in enumerate(DISPLAY_COLUMNS):
            column = first_column + feeling_index

            thick_left_border = feeling_index == 0

            # Add a thick line between Total-Surprise and Total-Total.
            if task == "Total" and feeling == "Total":
                thick_left_border = True

            thick_right_border = (
                feeling_index == columns_per_task - 1
            )

            vertical_label = "\n".join(feeling.upper())

            worksheet.write(
                1,
                column,
                vertical_label,
                get_feeling_header_format(
                    thick_left_border=thick_left_border,
                    thick_right_border=thick_right_border,
                ),
            )

    table_groups = groups + ["Total"]

    # Table body.
    for group_index, group in enumerate(table_groups):
        row_index = group_index + 2
        total_row = group == "Total"
        alternate_row = group_index % 2 == 1

        if total_row:
            group_cell_format = total_label_format
        else:
            group_cell_format = workbook.add_format(
                {
                    "align": "left",
                    "valign": "vcenter",
                    "border": 1,
                    "right": 2,
                    "bg_color": (
                        "#F2F2F2"
                        if alternate_row
                        else "#FFFFFF"
                    ),
                }
            )

        worksheet.write(
            row_index,
            0,
            str(group),
            group_cell_format,
        )

        for task_index, task in enumerate(task_headers):
            values = table_data[(group, task)]
            first_column = 1 + task_index * columns_per_task
            total_task = task == "Total"

            for value_index in range(columns_per_task):
                column = first_column + value_index
                feeling = DISPLAY_COLUMNS[value_index]

                thick_left_border = value_index == 0

                # Separate Total-Surprise from Total-Total.
                if total_task and feeling == "Total":
                    thick_left_border = True

                thick_right_border = (
                    value_index == columns_per_task - 1
                )

                missing = values is None

                cell_format = get_data_format(
                    alternate_row=alternate_row,
                    total_row=total_row,
                    total_task=total_task,
                    thick_left_border=thick_left_border,
                    thick_right_border=thick_right_border,
                    missing=missing,
                )

                if missing:
                    worksheet.write(
                        row_index,
                        column,
                        "-",
                        cell_format,
                    )
                else:
                    worksheet.write_number(
                        row_index,
                        column,
                        values[value_index],
                        cell_format,
                    )

    last_row = len(groups) + 2
    last_column = len(task_headers) * columns_per_task

    # Group names.
    worksheet.set_column(0, 0, 16)

    # Set each numeric column wide enough for its largest displayed value.
    for task_index, task in enumerate(task_headers):
        for value_index in range(columns_per_task):
            column = (
                1
                + task_index * columns_per_task
                + value_index
            )

            displayed_lengths = []

            for group in table_groups:
                values = table_data[(group, task)]

                if values is None:
                    displayed_lengths.append(1)
                elif as_percentage:
                    displayed_lengths.append(
                        len(f"{values[value_index]:.0%}")
                    )
                else:
                    displayed_lengths.append(
                        len(f"{values[value_index]:,.0f}")
                    )

            required_width = max(displayed_lengths) + 2

            # Keep columns readable without making small values too wide.
            column_width = max(6, min(required_width, 14))

            worksheet.set_column(
                column,
                column,
                column_width,
            )

    worksheet.set_row(0, 22)
    worksheet.set_row(1, 115)

    worksheet.freeze_panes(2, 1)
    worksheet.set_zoom(80)

    worksheet.set_landscape()
    worksheet.set_paper(9)
    worksheet.fit_to_pages(1, 0)
    worksheet.center_horizontally()

    worksheet.set_margins(
        left=0.25,
        right=0.25,
        top=0.5,
        bottom=0.5,
    )

    worksheet.print_area(
        0,
        0,
        last_row,
        last_column,
    )


def _create_table(
    datasets: dict[str, dict[Any, pl.DataFrame]],
    output_path: str,
    logger: logging.Logger,
) -> None:
    """Create sum and percentage tables from group-task partitions."""
    output_directory = Path(output_path)
    workbook_path = output_directory / "sum_table.xlsx"

    logger.info(
        "Creating summary workbook at %s",
        workbook_path,
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
            {group for group, _ in partitions},
            key=str,
        )

        tasks = sorted(
            {task for _, task in partitions},
            key=int,
        )

        sum_data: dict[
            tuple[Any, Any],
            list[int] | None,
        ] = {}

        # Calculate every individual group-task combination.
        for group in groups:
            for task in tasks:
                key = (group, task)

                if key not in partitions:
                    sum_data[key] = None
                    logger.warning(
                        "Missing group-task combination: %s",
                        key,
                    )
                    continue

                sum_data[key] = _calculate_feeling_sums(
                    partitions[key]
                )

        # Calculate each group's totals across its existing tasks.
        for group in groups:
            group_rows = [
                sum_data[(group, task)]
                for task in tasks
                if sum_data[(group, task)] is not None
            ]

            sum_data[(group, "Total")] = _add_rows(
                group_rows
            )

        # Calculate each task's totals across its existing groups.
        for task in tasks:
            task_rows = [
                sum_data[(group, task)]
                for group in groups
                if sum_data[(group, task)] is not None
            ]

            sum_data[("Total", task)] = _add_rows(
                task_rows
            )

        # Calculate the grand total from all existing combinations.
        existing_rows = [
            sum_data[(group, task)]
            for group in groups
            for task in tasks
            if sum_data[(group, task)] is not None
        ]

        sum_data[("Total", "Total")] = _add_rows(
            existing_rows
        )

        # Create the percentage table from the completed sums table.
        percentage_data = {
            key: (
                None
                if values is None
                else _convert_to_percentages(values)
            )
            for key, values in sum_data.items()
        }

        logger.info(
            "Calculated tables for %d groups and %d tasks",
            len(groups),
            len(tasks),
        )

        with xlsxwriter.Workbook(workbook_path) as workbook:
            _write_table_sheet(
                workbook=workbook,
                sheet_name="Sums",
                groups=groups,
                tasks=tasks,
                table_data=sum_data,
                as_percentage=False,
            )

            _write_table_sheet(
                workbook=workbook,
                sheet_name="Percentages",
                groups=groups,
                tasks=tasks,
                table_data=percentage_data,
                as_percentage=True,
            )

    except Exception:
        logger.exception(
            "Failed to create summary workbook at %s",
            workbook_path,
        )
        raise

    logger.info(
        "Created summary workbook at %s",
        workbook_path,
    )


def _create_bar_chart(
    datasets: dict[str, dict[Any, pl.DataFrame]],
    output_path: str,
    logger: logging.Logger,
) -> None:
    """
    Create a grouped bar chart of feeling occurrences by task.

    Each bar shows the total number of occurrences across groups.
    Hover information includes group-level summary statistics.
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
            {group for group, _ in partitions},
            key=str,
        )

        tasks = sorted(
            {task for _, task in partitions},
            key=int,
        )

        task_statistics: dict[Any, dict[str, dict[str, float]]] = {}

        for task in tasks:
            group_values = {
                feeling: []
                for feeling in PLOT_FEELING_COLUMNS
            }

            for group in groups:
                partition = partitions.get((group, task))

                if partition is None:
                    continue

                sums = partition.select(
                    pl.col(PLOT_FEELING_COLUMNS).sum()
                ).row(0)

                for feeling, value in zip(
                    PLOT_FEELING_COLUMNS,
                    sums,
                ):
                    group_values[feeling].append(
                        int(value) if value is not None else 0
                    )

            task_statistics[task] = {}

            for feeling, values in group_values.items():
                statistics = pl.Series(values)

                task_statistics[task][feeling] = {
                    "total": sum(values),
                    "mean": float(statistics.mean() or 0),
                    "median": float(statistics.median() or 0),
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
                for feeling in PLOT_FEELING_COLUMNS
            ]

            custom_data = [
                [
                    task_statistics[task][feeling]["mean"],
                    task_statistics[task][feeling]["median"],
                    task_statistics[task][feeling]["groups"],
                ]
                for feeling in PLOT_FEELING_COLUMNS
            ]

            figure.add_trace(
                go.Bar(
                    name=f"Task {task}",
                    x=PLOT_FEELING_COLUMNS,
                    y=totals,
                    marker_color=colours[
                        task_index % len(colours)
                    ],
                    customdata=custom_data,
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        f"Task: {task}<br>"
                        "Total occurrences: %{y:,}<br>"
                        "Mean per group: %{customdata[0]:.2f}<br>"
                        "Median per group: %{customdata[1]:.2f}<br>"
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
                "categoryarray": PLOT_FEELING_COLUMNS,
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


## MAIN FUNCTIONALITY ##
def generate_plots(
    input_dir: str,
    output_path: str,
    logger: logging.Logger,
) -> None:
    """Example function for new pipelines."""
    datasets = _import_and_group_data(
        csv_path=input_dir,
        logger=logger,
    )

    _create_table(
        datasets=datasets,
        output_path=output_path,
        logger=logger,
    )

    _create_bar_chart(
        datasets=datasets,
        output_path=output_path,
        logger=logger,
    )