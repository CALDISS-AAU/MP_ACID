"""Example helper functions for the pipeline."""

## IMPORTS ##
import logging
import polars as pl
from sentence_transformers import SentenceTransformer
## _______ ##


## HELPER FUNCTIONS ##


## MAIN FUNCTIONALITY ##
def validate_model(
    input_dir_data: str,
    input_dir_model:str,
    logger: logging.Logger,
) -> None:
    
    texts_pdf = pl.read(input_dir)["transcription_text"]

    embedding_model = SentenceTransformer('intfloat/multilingual-e5-large')

    final_topics, final_probs = topic_model.transform(texts_pdf)

    texts_pdf["topic"] = final_topics
    texts_pdf["topic_prob"] = final_probs
