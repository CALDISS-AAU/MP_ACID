"""Generate standardized pipeline folder structures for the project.

This module provides functionality for automatically generating new
pipeline directories within the project's Pipelines folder. Generated
pipelines follow the standardized project structure defined by the
CALDISS Python Cookiecutter template.

The module exposes a command-line interface through the
`create-pipeline` command.

Usage
-----
Create a new pipeline from the terminal:

    create-pipeline pipeline_name

Pipeline names may contain spaces, underscores, mixed casing, and
numbers. Only alphanumeric characters will be included in the final
pipeline name. Spaces and special characters are treated as word
separators and converted to underscores.

Example
-------
    create-pipeline data cleaning

This generates:

    Pipelines/
    └── Data_Cleaning/
        ├── Data/
        ├── Functions/
        ├── Logs/
        ├── Tests/
        ├── data_cleaning_main.py
        └── data_cleaning_README.md
"""

# IMPORTS #
from pathlib import Path
import argparse
import re
# _______ #

# STATIC VARIABLES #
FOLDERS_TO_GENERATE = [
    "Data", 
    "Functions", 
    "Logs", 
    "Tests"
]

OPTIONAL_FOLDERS = {
    "model": ["Modelling"],
}

PIPELINE_MAIN_TEXT = '''"""Main script for the {folder_name} pipeline.

To run this script, use the following command from the project root:
    uv run python -m Pipelines.{folder_name}.{file_name}_main
"""

## IMPORTS ##
# Internal
from Shared_Functions.logger_functionality import *
from .Functions.example_functions_script import example_function
## _______ ##


## STATIC VARIABLES ##
# Directories - input
# INPUT_DIR_AAA = "xxx/yyy.zzz"

# Directories - internal output
# OUTPUT_DIR_AAA = "Pipelines/{folder_name}/Data/xxx.zzz"

# Directories - global output
# OUTPUT_DIR_AAA = "./Data/{folder_name}/xxx.zzz"

# Directories - logs
OUTPUT_DIR_LOG_FULL_PIPELINE = "./Pipelines/{folder_name}/Logs/full_pipeline.log"
OUTPUT_DIR_LOG_1 = "./Pipelines/{folder_name}/Logs/example_1.log"
OUTPUT_DIR_LOG_2 = "./Pipelines/{folder_name}/Logs/example_2.log"

## _______________________ ##


## HELPER FUNCTIONS ##
## ________________ ##


## MAIN FUNCTION ##
def main() -> None:
    """Run the full {folder_name} pipeline."""

    example_function(
        input_str="Hello",
        logger=setup_logger(
            output_dir_log=OUTPUT_DIR_LOG_1,
            logger_name="{file_name}.step_1",
        ),
    )

    example_function(
        input_str="World!",
        logger=setup_logger(
            output_dir_log=OUTPUT_DIR_LOG_2,
            logger_name="{file_name}.step_2",
        ),
    )

    rebuild_pipeline_log(
        step_log_paths=[
            OUTPUT_DIR_LOG_1,
            OUTPUT_DIR_LOG_2,
        ],
        output_dir_log=OUTPUT_DIR_LOG_FULL_PIPELINE,
    )


## CALL OF MAIN FUNCTION ##
if __name__ == "__main__":
    main()
'''

PIPELINE_EXAMPLE_FUNCTIONS_SCRIPT_TEXT = '''"""Example helper functions for the pipeline."""

## IMPORTS ##
import logging
## _______ ##


## HELPER FUNCTIONS ##
def _print_str(
    input_str: str,
    logger: logging.Logger,
) -> None:
    """Print a string and log it."""

    print(input_str)
    logger.info("%s has been printed in the terminal.", input_str)


## MAIN FUNCTIONALITY ##
def example_function(
    input_str: str,
    logger: logging.Logger,
) -> None:
    """Example function for new pipelines."""

    _print_str(input_str, logger)
'''
# _________ #

# HELPER FUNCTIONS #
def split_words(text: str) -> list[str]:
    """Split text into alphanumeric words."""
    return re.findall(r"[A-Za-z0-9]+", text)


def to_capital_snake_case(text: str) -> str:
    """Convert text to Capital_Snake_Case."""
    words = split_words(text)
    return "_".join(word.lower().capitalize() for word in words)


def to_snake_case(text: str) -> str:
    """Convert text to snake_case."""
    words = split_words(text)
    return "_".join(word.lower() for word in words)

def find_project_root() -> Path:
    """Find the nearest parent directory containing pyproject.toml."""
    current_path = Path.cwd()

    for path in [current_path, *current_path.parents]:
        if (path / "pyproject.toml").exists():
            return path

    raise FileNotFoundError("Could not find project root with pyproject.toml.")
# ________________ #

# COMBINING ALL HELPERFUNTIONS #
def create_pipeline(
    name: str,
    included_folders: list[str] | None = None,
) -> None:
    """Create a standardized pipeline folder structure.

    Parameters
    ----------
    name : str
        Name of the pipeline to create.
    included_folders : list[str] | None
        Optional folder groups to include.

    Raises
    ------
    FileExistsError
        If the pipeline directory already exists.
    ValueError
        If the pipeline name is invalid.
    """
    folder_name = to_capital_snake_case(name)
    file_name = to_snake_case(name)

    if not folder_name:
        raise ValueError(
            "Pipeline name must contain at least one alphanumeric character."
        )

    project_root = find_project_root()
    pipeline_path = project_root / "Pipelines" / folder_name

    if pipeline_path.exists():
        raise FileExistsError(f"Pipeline already exists: {folder_name}")

    folders_to_generate = FOLDERS_TO_GENERATE.copy()

    for inclusion in included_folders or []:
        folders_to_generate.extend(OPTIONAL_FOLDERS[inclusion])

    # Remove duplicates while preserving order.
    folders_to_generate = list(dict.fromkeys(folders_to_generate))

    pipeline_path.mkdir(parents=True)

    for folder in folders_to_generate:
        folder_path = pipeline_path / folder
        folder_path.mkdir()
        (folder_path / ".gitkeep").touch()

    script_path = pipeline_path / f"{file_name}_main.py"
    script_path.write_text(
        PIPELINE_MAIN_TEXT.format(
            folder_name=folder_name,
            file_name=file_name,
        ),
        encoding="utf-8",
    )

    functions_script_path = (
        pipeline_path
        / "Functions"
        / "example_functions_script.py"
    )

    functions_script_path.write_text(
        PIPELINE_EXAMPLE_FUNCTIONS_SCRIPT_TEXT,
        encoding="utf-8",
    )

    readme_path = pipeline_path / f"{file_name}_README.md"
    readme_path.write_text(
        f"# {folder_name} README\n",
        encoding="utf-8",
    )

    print(f"Created pipeline: {folder_name}")
    print(f"Generated folders: {', '.join(folders_to_generate)}")
# ____________________________ #

# FUNCTION MAIN #
def main() -> None:
    """Run the create-pipeline command-line interface."""
    parser = argparse.ArgumentParser(
        description="Create a standardized pipeline structure."
    )

    parser.add_argument(
        "pipeline_name",
        nargs="+",
        help="Name of the pipeline to create.",
    )

    parser.add_argument(
        "-i",
        "--include",
        action="append",
        choices=OPTIONAL_FOLDERS,
        default=[],
        help=(
            "Include an optional folder group. "
            "May be supplied more than once."
        ),
    )

    args = parser.parse_args()
    pipeline_name = " ".join(args.pipeline_name)

    try:
        create_pipeline(
            name=pipeline_name,
            included_folders=args.include,
        )

    except (
        FileExistsError,
        FileNotFoundError,
        ValueError,
    ) as error:
        parser.exit(status=1, message=f"Error: {error}\n")


if __name__ == "__main__":
    main()
# _____________ #