"""Train and save BERTopic models for the Bertopic pipeline."""

## IMPORTS ##
# Standard
import logging
from pathlib import Path

# Third-party
from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired
from hdbscan import HDBSCAN
import polars as pl
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from spacy.lang.da import Danish
from umap import UMAP
## _______ ##

## HELPER FUNCTIONS ##
def _import_data(
    input_dir: str,
    logger: logging.Logger,
) -> pl.Series:
    """Load and lowercase transcription text from a JSON dataset."""

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
    stopwords_extension: list[str],
    output_dir_model: str,
    output_dir_visualisations: str,
    n_neighbors: int,
    n_components: int,
    min_cluster_size: int,
    min_samples: int,
    max_df: float,
    ngram_range: tuple[int, int],
    logger: logging.Logger,
) -> None:
    """Train, save, and visualise a BERTopic model.

    Args:
        input_dir: JSON file containing the transcription text.
        stopwords_extension: Additional words excluded during vectorisation.
        output_dir_model: Destination for the trained BERTopic model.
        output_dir_visualisations: Base path for generated visualisations.
        n_neighbors: Number of neighbours used by UMAP.
        n_components: Number of dimensions produced by UMAP.
        min_cluster_size: Minimum cluster size used by HDBSCAN.
        min_samples: Minimum sample count used by HDBSCAN.
        max_df: Maximum document frequency used by the vectoriser.
        ngram_range: Minimum and maximum sizes of generated n-grams.
        logger: Logger used to record data-import information.

    """

    texts = _import_data(
        input_dir=input_dir,
        logger=logger,
    )

    nlp = Danish()
    stop_words = list(nlp.Defaults.stop_words)
    stop_words.extend(stopwords_extension)

    embedding_model = SentenceTransformer(
        "intfloat/multilingual-e5-large"
    )

    umap_model = UMAP(
        # Lower values preserve local rather than global structure.
        n_neighbors=n_neighbors,
        # Number of dimensions produced by the reduction.
        n_components=n_components,
        metric="cosine",
        # Controls how tightly neighbouring points may be packed.
        min_dist=0.0,
        low_memory=False,
        random_state=3_092_026,
    )

    hdbscan_model = HDBSCAN(
        # Minimum document count required to form a cluster.
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        cluster_selection_method="leaf",
        cluster_selection_epsilon=0.0,
        metric="euclidean",
        prediction_data=True,
    )

    representation_model = KeyBERTInspired()

    vectorizer_model = CountVectorizer(
        stop_words=stop_words,
        # Minimum frequency required within the dataset.
        min_df=1,
        # Maximum frequency allowed across the dataset.
        max_df=max_df,
        # Minimum and maximum number of words in each n-gram.
        ngram_range=ngram_range,
    )

    topic_model = BERTopic(
        embedding_model=embedding_model,
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        representation_model=representation_model,
        top_n_words=15,
        verbose=True,
    )

    topic_model.fit_transform(texts)

    topic_model.save(
        output_dir_model,
        serialization="safetensors",
        save_ctfidf=True,
        save_embedding_model=embedding_model,
    )

    doc_topics = topic_model.get_document_info(texts)

    doc_topic_outpath = Path(output_dir_model) / "document_to_topic.csv"
    doc_topics.to_csv(doc_topic_outpath, index=False)

    visualisation_directory = Path(
        output_dir_visualisations
    )

    visualisation_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    figure = topic_model.visualize_topics()

    figure.write_html(
        visualisation_directory / "topics_overview.html"
    )