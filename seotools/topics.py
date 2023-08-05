import sentence_transformers
from sklearn import cluster

model = sentence_transformers.SentenceTransformer("paraphrase-distilroberta-base-v1")


def get_topic_clusters(topics: list, n_clusters: int = 2) -> dict:
    """
    Group content into the provided number of clusters.

    Args:
        topics (list): A list of topics to cluster.
        n_clusters (int): The number of clusters to create.

    Returns:
        dict: A dictionary of clusters.

    Example:
        ```python
        from seotools.app import Analyzer

        analyzer = Analyzer("https://jamesg.blog/sitemap.xml", load_from_disk=True)

        analyzer.visualize_with_embeddings()
        ```
    """
    embeddings = {v: model.encode(v) for v in topics}

    X = list(embeddings.values())

    kmeans = cluster.KMeans(n_clusters=n_clusters)

    kmeans.fit(X)

    labels = kmeans.labels_

    clusters = {}

    for i, label in enumerate(labels):
        if label not in clusters:
            clusters[label] = []

        clusters[label].append(list(embeddings.keys())[i])

    # transpose keys into str
    clusters = {str(k): v for k, v in clusters.items()}

    return clusters
