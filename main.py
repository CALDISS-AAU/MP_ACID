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
from Pipelines.Standardise_Data.standardise_data_main import main as standardise_data
from Pipelines.Feelings_Investigation.feelings_investigation_main import main as investigate_feelings
from Pipelines.Data_Combination.data_combination_main import main as combine_data
from Pipelines.Screengetter.screengetter_main import main as screengetter
from Pipelines.Bertopic.bertopic_main import main as BERTopic
from Pipelines.Event_Statistics.event_statistics_main import main as event_statistics
## _______ ##

## MAIN FUNCTION ##
def main() -> None:
    standardise_data()
    investigate_feelings()
    combine_data()
    screengetter()
    BERTopic()
    event_statistics()
    
## _____________ ##

## CALL OF MAIN FUNCTION ##
if __name__ == "__main__":
    main()
