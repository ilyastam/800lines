"""Embedding service for generating vector embeddings from state entities."""

from abc import ABC, abstractmethod
from agent.state_entity import BaseStateEntity


class EmbeddingService(ABC):
    """Abstract interface for embedding generation services."""

    @abstractmethod
    def embed(self, entity: BaseStateEntity) -> list[float]:
        """
        Generate embedding for a single entity.

        Args:
            entity: The state entity to embed

        Returns:
            List of floats representing the embedding vector
        """
        pass

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for raw text.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding vector
        """
        pass

    @abstractmethod
    def embed_batch(self, entities: list[BaseStateEntity]) -> list[list[float]]:
        """
        Generate embeddings for multiple entities (for efficiency).

        Args:
            entities: List of state entities to embed

        Returns:
            List of embedding vectors
        """
        pass


class DefaultEmbeddingService(EmbeddingService):
    """
    Default embedding service implementation.

    Note: This is a placeholder implementation. In production, you would
    use an actual embedding model like OpenAI's embeddings, sentence-transformers,
    or other embedding providers.
    """

    def __init__(self, model: str = "text-embedding-3-small"):
        """
        Initialize the embedding service.

        Args:
            model: Name of the embedding model to use
        """
        self.model = model

    def embed(self, entity: BaseStateEntity) -> list[float]:
        """
        Generate embedding for single entity.

        Args:
            entity: The entity to embed

        Returns:
            List of floats representing the embedding vector
        """
        text = self._entity_to_text(entity)
        return self.embed_text(text)

    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for text.

        Note: This is a placeholder implementation that returns a simple hash-based
        embedding. In production, replace this with actual embedding generation.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding vector
        """
        # Placeholder: Simple hash-based embedding for demonstration
        # In production, use actual embedding API like:
        # response = self.client.embeddings.create(model=self.model, input=text)
        # return response.data[0].embedding

        # Simple deterministic embedding based on text hash
        hash_val = hash(text)
        # Create a simple 384-dimensional embedding (common size for small models)
        embedding = []
        for i in range(384):
            val = ((hash_val + i * 7919) % 1000) / 1000.0  # Normalize to [0, 1]
            embedding.append(val)

        # Normalize the vector
        import numpy as np
        arr = np.array(embedding)
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm

        return arr.tolist()

    def embed_batch(self, entities: list[BaseStateEntity]) -> list[list[float]]:
        """
        Batch embed for efficiency.

        Args:
            entities: List of entities to embed

        Returns:
            List of embedding vectors
        """
        # For placeholder implementation, just call embed on each entity
        # In production, use batch API for efficiency
        return [self.embed(entity) for entity in entities]

    def _entity_to_text(self, entity: BaseStateEntity) -> str:
        """
        Convert entity to text for embedding.

        Args:
            entity: The entity to convert

        Returns:
            Text representation of the entity
        """
        parts = [
            f"Type: {entity.__class__.__name__}",
            f"Content: {entity.content}",
        ]

        # Include type-specific fields
        for field_name in type(entity).model_fields:
            if field_name not in ['content', 'context', 'embedding', 'date_created_utc']:
                field_value = getattr(entity, field_name, None)
                if field_value is not None:
                    parts.append(f"{field_name}: {field_value}")

        return " | ".join(parts)
