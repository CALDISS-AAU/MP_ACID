"""Clear generated data and log files from a pipeline.

This module provides a command-line interface for removing all files and
subdirectories from a pipeline's Data and Logs directories.

The Data and Logs directories themselves are preserved, along with their
.gitkeep files.

Usage
-----
Clear a pipeline from the terminal:

    clear-pipeline pipeline_name

Pipeline names may contain spaces, underscores, mixed casing, and numbers.

Example
-------
    clear-pipeline data cleaning
"""

# IMPORTS #
from pathlib import Path
import argparse
import re
import shutil
# _______ #


# STATIC VARIABLES #
FOLDERS_TO_CLEAR = [
    "Data",
    "Logs",
]
# ________________ #


# HELPER FUNCTIONS #
def split_words(text: str) -> list[str]:
    """Split text into alphanumeric words."""
    return re.findall(r"[A-Za-z0-9]+", text)


def to_capital_snake_case(text: str) -> str:
    """Convert text to Capital_Snake_Case."""
    words = split_words(text)
    return "_".join(word.lower().capitalize() for word in words)


def find_project_root() -> Path:
    """Find the nearest parent directory containing pyproject.toml."""
    current_path = Path.cwd()

    for path in [current_path, *current_path.parents]:
        if (path / "pyproject.toml").exists():
            return path

    raise FileNotFoundError(
        "Could not find project root containing pyproject.toml."
    )


def clear_directory(directory_path: Path) -> None:
    """Remove all contents from a directory except .gitkeep.

    Parameters
    ----------
    directory_path : Path
        Directory whose contents should be removed.
    """
    for item_path in directory_path.iterdir():
        if item_path.name == ".gitkeep":
            continue

        if item_path.is_symlink() or item_path.is_file():
            item_path.unlink()
        elif item_path.is_dir():
            shutil.rmtree(item_path)
# ________________ #


# MAIN FUNCTIONALITY #
def clear_pipeline(name: str) -> None:
    """Clear the Data and Logs directories for a pipeline.

    Parameters
    ----------
    name : str
        Name of the pipeline to clear.

    Raises
    ------
    ValueError
        If the supplied pipeline name contains no alphanumeric characters.
    FileNotFoundError
        If the project root or pipeline directory cannot be found.
    """
    folder_name = to_capital_snake_case(name)

    if not folder_name:
        raise ValueError(
            "Pipeline name must contain at least one alphanumeric character."
        )

    project_root = find_project_root()
    pipelines_root = project_root / "Pipelines"
    pipeline_path = pipelines_root / folder_name

    if not pipeline_path.is_dir():
        raise FileNotFoundError(
            f"Pipeline does not exist: {folder_name}"
        )

    cleared_folders: list[str] = []

    for folder_name_to_clear in FOLDERS_TO_CLEAR:
        folder_path = pipeline_path / folder_name_to_clear

        if not folder_path.exists():
            print(
                f"Skipped missing directory: "
                f"{folder_path.relative_to(project_root)}"
            )
            continue

        if not folder_path.is_dir():
            raise NotADirectoryError(
                f"Expected a directory: {folder_path}"
            )

        clear_directory(folder_path)
        cleared_folders.append(folder_name_to_clear)

    if cleared_folders:
        folders_text = " and ".join(cleared_folders)
        print(
            f"Cleared {folders_text} for pipeline: {folder_name}"
        )
    else:
        print(f"No directories were cleared for pipeline: {folder_name}")
# __________________ #


# COMMAND-LINE INTERFACE #
def main() -> None:
    """Run the pipeline-cleaning command-line interface."""
    parser = argparse.ArgumentParser(
        description=(
            "Remove all contents from a pipeline's Data and Logs "
            "directories."
        )
    )

    parser.add_argument(
        "pipeline_name",
        nargs="+",
        help="Name of the pipeline to clear.",
    )

    args = parser.parse_args()
    pipeline_name = " ".join(args.pipeline_name)

    try:
        clear_pipeline(pipeline_name)

    except (
        FileNotFoundError,
        NotADirectoryError,
        PermissionError,
        ValueError,
    ) as error:
        parser.exit(status=1, message=f"Error: {error}\n")


if __name__ == "__main__":
    main()
# ______________________ #