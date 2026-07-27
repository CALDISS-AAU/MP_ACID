import logging
from pathlib import Path

def setup_logger(
    output_dir_log: str, 
    logger_name: str, 
    overwrite=True, 
) -> logging.Logger:
    """Set up and return a file logger for data inspection.

    Creates the log directory if it does not exist and configures
    a logger that writes to output_dir_log.

    Args:
        output_dir_log: Full directory where the log file is stored (string)
        logger_name: Name of the current logger instance
        overwrite: True if previous log should be overwritten - False otherwise

    Returns:
        Configured logger instance.
    """
    log_file = Path(output_dir_log)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Remove existing handlers
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

    mode = "w" if overwrite else "a"

    file_handler = logging.FileHandler(log_file, mode=mode)
    file_handler.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(file_handler)

    return logger

from pathlib import Path


def rebuild_pipeline_log(
    step_log_paths: list[str],
    output_dir_log: str,
) -> None:
    """Rebuild a combined pipeline log from individual step logs.

    The output log is overwritten each time the function is called and
    contains the current contents of all existing step logs in the order
    provided by step_log_paths.

    Args:
        step_log_paths:
            Ordered list of log file paths for individual pipeline steps.
        output_dir_log:
            Path to the combined pipeline log.
    """
    combined_log = Path(output_dir_log)
    combined_log.parent.mkdir(parents=True, exist_ok=True)

    with combined_log.open("w", encoding="utf-8") as outfile:
        for step_log_path in step_log_paths:
            step_log = Path(step_log_path)

            if not step_log.exists():
                continue

            outfile.write(step_log.read_text(encoding="utf-8"))

            # Add a newline between step logs
            outfile.write("\n")