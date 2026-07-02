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

# VARIABLES #
folders_to_generate = [
    "Data", 
    "Functions", 
    "Logs", 
    "Tests"
]
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
def create_pipeline(name: str) -> None:
    """Create a standardized pipeline folder structure.

    Generate a new pipeline directory within the project's Pipelines
    folder, including the required subfolders and starter files.

    Parameters
    ----------
    name : str
        Name of the pipeline to create.

    Raises
    ------
    FileExistsError
        If the pipeline directory already exists.
    """
    folder_name = to_capital_snake_case(name)
    file_name = to_snake_case(name)

    project_root = find_project_root()
    pipeline_path = project_root / "Pipelines" / folder_name

    if pipeline_path.exists():
        raise FileExistsError(f"Pipeline already exists: {folder_name}")

    pipeline_path.mkdir(parents=True)

    for folder in folders_to_generate:
        folder_path = pipeline_path / folder
        folder_path.mkdir()
        (folder_path / ".gitkeep").touch()

    script_path = pipeline_path / f"{file_name}_main.py"
    script_path.write_text(f'"""Main script for the {folder_name} pipeline."""\n')

    readme_path = pipeline_path / f"{file_name}_README.md"
    readme_path.write_text(f"# {folder_name} README\n")

    print(f"Created pipeline: {folder_name}")
# ____________________________ #

# FUNCTION MAIN #
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pipeline_name", nargs="+")

    args = parser.parse_args()
    pipeline_name = " ".join(args.pipeline_name)

    try:
        create_pipeline(pipeline_name)

    except (FileExistsError, FileNotFoundError) as error:
        print(error)


if __name__ == "__main__":
    main()
# _____________ #