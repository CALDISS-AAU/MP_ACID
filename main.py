""" This is the main script of the MP_ACID-project.
    This script is reserved for calling and combining pipelines from the
    Pipelines/ folders.
    For a description of the overall functionality of the individual
    pipelines, please consult their respective Pipelines/README.md.

    To run this script, please use this command in the terminal, 
    from the project root:
        uv run python -m main
"""
## IMPORTS ##
# Pipeline mains
from Pipelines.Example_Pipeline.example_pipeline_main import main as example_pipeline_main
## _______ ##

## MAIN FUNCTION ##
def main() -> None:
    example_pipeline_main()
## _____________ ##

## CALL OF MAIN FUNCTION ##
if __name__ == "__main__":
    main()
