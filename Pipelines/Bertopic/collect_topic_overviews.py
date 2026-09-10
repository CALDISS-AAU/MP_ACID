"""Collect selected BERTopic overview plots into a download-friendly structure.

Run from the project root with:
    uv run python -m Pipelines.Bertopic.collect_topic_overviews

By default this creates:
    Pipelines/Bertopic/Data/Visualisations/
        pc75/
            Matched_1_params/
            ...
            Matched_5_params/
        pc85/
            Matched_1_params/
            ...
            Matched_5_params/
        manifest.csv

and:
    Pipelines/Bertopic/Data/Visualisations.zip

Only plots matching at least one preferred parameter are collected.

Preferred parameters:
    pc85: nn=15, nc=5, mcs=50, md=0.8, ngr=1-2
    pc75: nn=15, nc=5, mcs=40, md=0.8, ngr=1-2
"""

import argparse
import csv
import logging
import re
import shutil
from pathlib import Path


DEFAULT_SOURCE_DIR = Path("Pipelines/Bertopic/Data")
DEFAULT_DESTINATION_DIR = Path(
    "Pipelines/Bertopic/Data/Visualisations_Matched"
)

CONFIGURATION_PATTERN = re.compile(
    r"^pc(?P<pc>\d+)"
    r"_pre(?P<pre>\d+)"
    r"_post(?P<post>\d+)"
    r"_nn(?P<nn>\d+)"
    r"_nc(?P<nc>\d+)"
    r"_mcs(?P<mcs>\d+)"
    r"_md(?P<md>[^_]+)"
    r"_ngr(?P<ngram_min>\d+)-(?P<ngram_max>\d+)$"
)

OVERVIEW_FILENAMES = {
    "topics_overview.html",
}

PREFERRED_SETTINGS = {
    "85": {
        "nn": "15",
        "nc": "5",
        "mcs": "50",
        "md": "0.8",
        "ngram_min": "1",
        "ngram_max": "2",
    },
    "75": {
        "nn": "15",
        "nc": "5",
        "mcs": "40",
        "md": "0.8",
        "ngram_min": "1",
        "ngram_max": "2",
    },
}


def _setup_logger() -> logging.Logger:
    """Create a console logger for this utility."""

    logger = logging.getLogger(
        "bertopic.collect_visualisations"
    )
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s"
            )
        )
        logger.addHandler(handler)

    return logger


def _find_configuration_directory(
    overview_path: Path,
) -> tuple[Path, re.Match[str]]:
    """Find and parse the configuration directory above a plot."""

    for parent in overview_path.parents:
        match = CONFIGURATION_PATTERN.fullmatch(parent.name)

        if match is not None:
            return parent, match

    raise ValueError(
        "No recognized BERTopic configuration directory was found "
        f"above {overview_path}."
    )


def _discover_overviews(source_dir: Path) -> list[Path]:
    """Find overview HTML files below the BERTopic data directory."""

    return sorted(
        path
        for path in source_dir.rglob("*.html")
        if path.name in OVERVIEW_FILENAMES
    )


def _get_matched_conditions(
    settings: dict[str, str],
) -> list[str]:
    """Return the preferred parameters matched by a configuration."""

    preferred_settings = PREFERRED_SETTINGS.get(settings["pc"])

    if preferred_settings is None:
        return []

    matched_conditions: list[str] = []

    if settings["nn"] == preferred_settings["nn"]:
        matched_conditions.append("nn")

    if settings["nc"] == preferred_settings["nc"]:
        matched_conditions.append("nc")

    if settings["mcs"] == preferred_settings["mcs"]:
        matched_conditions.append("mcs")

    if settings["md"] == preferred_settings["md"]:
        matched_conditions.append("md")

    ngram_matches = (
        settings["ngram_min"]
        == preferred_settings["ngram_min"]
        and settings["ngram_max"]
        == preferred_settings["ngram_max"]
    )

    if ngram_matches:
        matched_conditions.append("ngr")

    return matched_conditions


def collect_topic_overviews(
    source_dir: Path,
    destination_dir: Path,
    create_archive: bool,
    logger: logging.Logger,
) -> int:
    """Copy, organize, and optionally archive selected overview plots."""

    source_dir = source_dir.resolve()
    destination_dir = destination_dir.resolve()

    if not source_dir.is_dir():
        raise FileNotFoundError(
            "BERTopic data directory does not exist: "
            f"{source_dir}"
        )

    logger.info(
        "Searching for topic overviews below %s.",
        source_dir,
    )
    overview_paths = _discover_overviews(source_dir)

    if not overview_paths:
        raise FileNotFoundError(
            "No topic overview HTML files were found below "
            f"{source_dir}."
        )

    logger.info(
        "Found %d topic overview files.",
        len(overview_paths),
    )

    destination_dir.mkdir(parents=True, exist_ok=True)

    manifest_rows: list[dict[str, str | int]] = []
    destination_paths: set[Path] = set()

    unrecognized_count = 0
    unsupported_pc_count = 0
    no_matches_count = 0

    for source_path in overview_paths:
        try:
            configuration_dir, match = (
                _find_configuration_directory(source_path)
            )
        except ValueError as error:
            unrecognized_count += 1
            logger.warning("%s Skipping file.", error)
            continue

        settings = match.groupdict()

        if settings["pc"] not in PREFERRED_SETTINGS:
            unsupported_pc_count += 1
            continue

        matched_conditions = _get_matched_conditions(settings)
        matched_count = len(matched_conditions)

        if matched_count == 0:
            no_matches_count += 1
            continue

        matched_directory = (
            destination_dir
            / f"pc{settings['pc']}"
            / f"Matched_{matched_count}_params"
        )
        matched_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination_path = matched_directory / (
            f"{configuration_dir.name}_topics_overview.html"
        )

        if destination_path in destination_paths:
            raise RuntimeError(
                "More than one overview maps to the same "
                f"destination: {destination_path}"
            )

        destination_paths.add(destination_path)
        shutil.copy2(source_path, destination_path)

        manifest_rows.append(
            {
                "pc": settings["pc"],
                "matched_parameter_count": matched_count,
                "matched_parameters": ",".join(
                    matched_conditions
                ),
                "pre": settings["pre"],
                "post": settings["post"],
                "n_neighbours": settings["nn"],
                "n_components": settings["nc"],
                "min_cluster_size": settings["mcs"],
                "max_df": settings["md"],
                "ngram_min": settings["ngram_min"],
                "ngram_max": settings["ngram_max"],
                "source": str(source_path),
                "collected_file": str(
                    destination_path.relative_to(
                        destination_dir
                    )
                ),
            }
        )

    if not manifest_rows:
        raise RuntimeError(
            "No overview files matched any preferred parameters."
        )

    manifest_rows.sort(
        key=lambda row: (
            int(row["pc"]),
            -int(row["matched_parameter_count"]),
            str(row["collected_file"]),
        )
    )

    manifest_path = destination_dir / "manifest.csv"

    with manifest_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(manifest_rows[0]),
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    logger.info(
        "Copied %d matching overview files.",
        len(manifest_rows),
    )
    logger.info(
        "Skipped %d files with no matching parameters.",
        no_matches_count,
    )
    logger.info(
        "Skipped %d files with unsupported pc values.",
        unsupported_pc_count,
    )
    logger.info(
        "Skipped %d files with unrecognized configurations.",
        unrecognized_count,
    )
    logger.info(
        "Manifest saved to %s.",
        manifest_path,
    )

    if create_archive:
        archive_path = Path(
            shutil.make_archive(
                base_name=str(destination_dir),
                format="zip",
                root_dir=destination_dir.parent,
                base_dir=destination_dir.name,
            )
        )
        logger.info(
            "Download archive created at %s.",
            archive_path,
        )

    return len(manifest_rows)


def _parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Collect BERTopic topic-overview HTML files that "
            "match preferred parameters."
        )
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
        help=(
            "BERTopic data directory "
            f"(default: {DEFAULT_SOURCE_DIR})."
        ),
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=DEFAULT_DESTINATION_DIR,
        help=(
            "Collected visualizations directory "
            f"(default: {DEFAULT_DESTINATION_DIR})."
        ),
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help=(
            "Do not create a ZIP archive after collecting "
            "the files."
        ),
    )

    return parser.parse_args()


def main() -> None:
    """Run the topic-overview collection utility."""

    arguments = _parse_arguments()
    logger = _setup_logger()

    try:
        collect_topic_overviews(
            source_dir=arguments.source,
            destination_dir=arguments.destination,
            create_archive=not arguments.no_archive,
            logger=logger,
        )
    except Exception:
        logger.exception(
            "Topic-overview collection failed."
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()