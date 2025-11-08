"""Similarity metrics for comparing embedding vectors."""

import numpy as np


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        v1: First vector
        v2: Second vector

    Returns:
        Similarity score between 0 and 1 (1 being identical)
    """
    dot_product = np.dot(v1, v2)
    norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
    return float(dot_product / norm_product) if norm_product > 0 else 0.0


def euclidean_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Calculate similarity based on euclidean distance (normalized to 0-1).

    Args:
        v1: First vector
        v2: Second vector

    Returns:
        Similarity score (higher is more similar)
    """
    distance = np.linalg.norm(v1 - v2)
    # Convert distance to similarity using negative exponential
    # Maps distance to [0, 1] range
    return float(np.exp(-distance))


def dot_product_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Calculate normalized dot product similarity.

    Args:
        v1: First vector
        v2: Second vector

    Returns:
        Dot product similarity score
    """
    return float(np.dot(v1, v2))
