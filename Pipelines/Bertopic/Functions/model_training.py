"""Example helper functions for the pipeline."""

## IMPORTS ##
import logging
import polars as pl
import spacy
from spacy.lang.da import Danish
from sentence_transformers import  SentenceTransformer
from pathlib import Path
# BERTopic related stuff
from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired
from umap import UMAP
from hdbscan import HDBSCAN 
from sklearn.feature_extraction.text import CountVectorizer
## _______ ##


## HELPER FUNCTIONS ##
def _import_data(
    input_dir: str,
    logger: logging.Logger,
) -> pl.Series:
    """Import the relevant data column and convert it to lowercase."""

    texts = (
        pl.read_json(input_dir)
        .get_column("transcription_text")
        .str.to_lowercase()
    )

    logger.info("Data from %s has been loaded.", input_dir)
    logger.info("First 10 texts:\n%s", texts.head(10))

    return texts

## MAIN FUNCTIONALITY ##
def train_model(
    input_dir: str,
    stopwords_extention: list[str],
    output_dir_model: str,
    output_dir_visualisations,
    logger: logging.Logger,
) -> None:
    """Example function for new pipelines."""

    texts_pdf = _import_data(input_dir, logger)

    nlp = Danish()
    stop_words = list(nlp.Defaults.stop_words)
    stop_words.extend(stopwords_extention)

    embedding_model = SentenceTransformer('intfloat/multilingual-e5-large')

    umap_model = UMAP(
        n_neighbors=15, # local (low value) vs global (high value)
        n_components=5, # reduce to n dimensions
        metric='cosine',
        min_dist=0.0, # how tightly points can be packed - how different are the clusters
        low_memory=False,
        random_state=3092026
    )

    hdbscan_model = HDBSCAN(
        min_cluster_size=50, # how big a cluster is before it is regocnised - how many documents before it's recongnised
        min_samples=20,
        cluster_selection_method='leaf',
        cluster_selection_epsilon=0.0,
        metric='euclidean',
        prediction_data=True
    )

    representation_model = KeyBERTInspired()

    vectorizer_model = CountVectorizer(
        stop_words=stop_words, 
        min_df=1, # how often a word needs to be mentioned in a single cluster before it's considered relevant
        max_df=0.8, # how often a word needs to be mentioned acress clusters before it's considered relevant 
        ngram_range=(1, 2) # how many words we want for each topic - e.g. (1,2) is one or two words
    ) 

    topic_model = BERTopic(
        embedding_model=embedding_model,
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        representation_model=representation_model,
        top_n_words=15,
        verbose=True
    )

    topics, probs = topic_model.fit_transform(texts_pdf)

    data_topics = topic_model.get_document_info(texts_pdf)
    data_topics['topic_prob'] = probs

    topics_info = topic_model.get_topic_info()

    topic_model.save(
        output_dir_model, 
        serialization="safetensors", 
        save_ctfidf=True, 
        save_embedding_model=embedding_model
    )

    Path(output_dir_visualisations).mkdir(parents=True, exist_ok=True)
    fig = topic_model.visualize_topics()
    fig.write_html(f"{output_dir_visualisations}/topics_overview.html")