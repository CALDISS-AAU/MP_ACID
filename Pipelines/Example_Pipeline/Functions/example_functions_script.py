"""Example helper functions for the pipeline."""

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
