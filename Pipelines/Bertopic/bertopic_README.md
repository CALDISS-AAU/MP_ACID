# BERTopic Pipeline

## Overview

The `Bertopic` pipeline trains topic models from transcription intervals
associated with detected feelings. It combines multilingual sentence
embeddings, UMAP dimensionality reduction, HDBSCAN clustering, and BERTopic
representation methods to identify and describe recurring topics.

Each configured hyperparameter combination produces a separately saved model
and an interactive topic-overview visualisation.

## Processing

For each hyperparameter combination, the pipeline:

1. Loads the `transcription_text` column from the configured JSON dataset.
2. Converts the transcription text to lowercase.
3. Extends the default Danish stop-word collection with project-specific
   stop words.
4. Configures the embedding, UMAP, HDBSCAN, vectorisation, and topic
   representation models.
5. Trains a BERTopic model on the transcription texts.
6. Saves the trained model using safetensors serialization.
7. Creates an interactive topic-overview visualisation.

## Input

The input is configured in `bertopic_main.py` and is read relative to
`INPUT_BASE`, which defaults to the project root:

```text
Data/Data_Combination/combined_data_when_feelings_pc85_pre0_post0.json
```

The JSON dataset must contain a `transcription_text` column. It is generated
by the `Data_Combination` pipeline using an FEA certainty threshold of `85`,
with no additional preceding or succeeding sentences.

## Model configuration

The pipeline uses the following components:

| Component | Implementation |
| --- | --- |
| Embeddings | `intfloat/multilingual-e5-large` |
| Dimensionality reduction | UMAP with cosine distance |
| Clustering | HDBSCAN with leaf cluster selection |
| Vectorisation | `CountVectorizer` with Danish stop words |
| Topic representation | `KeyBERTInspired` |

The current hyperparameter lists are:

| Variable | Current values |
| --- | --- |
| `N_NEIGHBOURS` | `[10]` |
| `N_COMPONENTS` | `[10]` |
| `MIN_CLUSTER_SIZE` | `[40]` |
| `MIN_SAMPLES` | `[5]` |
| `MAX_DF` | `[0.8]` |
| `NGRAM_RANGE` | `[(1, 2)]` |

Although each list currently contains one option, the list structure is
intentional. Additional values can be added to explore more configurations.
The pipeline trains a model for every combination of the listed values. With
the current settings, one model is trained.

The UMAP random state is fixed to `3092026` to support reproducible dimension
reduction.

## Outputs

Trained models are saved beneath:

```text
Pipelines/Bertopic/Data/trained_model/
```

Topic-overview visualisations are saved beneath:

```text
Pipelines/Bertopic/Data/visualisations/
```

Each configuration receives its own directory. Directory names encode the
values used for UMAP neighbours and components, HDBSCAN cluster size and
samples, maximum document frequency, and n-gram range.

The trained models include their c-TF-IDF data and embedding-model reference.
Each visualisation directory contains an interactive `topics_overview.html`
file.

## Running the pipeline

Run the pipeline from the project root:

```bash
uv run python -m Pipelines.Bertopic.bertopic_main
```

The sentence-transformer model must be available locally or downloadable when
the pipeline runs. Training duration and memory use depend on the dataset size
and number of configured hyperparameter combinations.

## Logging

Model-training messages are written to:

```text
Pipelines/Bertopic/Logs/train_model.log
```

The training log is incorporated into:

```text
Pipelines/Bertopic/Logs/full_pipeline.log
```
