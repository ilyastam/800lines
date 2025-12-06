"""State storage implementations for semantic search and chronological tracking."""

import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime, timezone

import numpy as np

from agent.state_storage.embedding_service import EmbeddingService
from agent.state_storage.similarity_metrics import cosine_similarity
from agent.state_storage.state_change import compare_entities
from agent.state_entity import BaseStateEntity
from agent.types import StateChange


class StateStorage(ABC):
    """Abstract base class for state storage implementations."""

    @abstractmethod
    def add_entities(self, entities: list[BaseStateEntity]) -> list[StateChange]:
        """
        Add multiple entities in a single state update.
        Increments the state version and assigns it to all entities.

        Args:
            entities: List of state entities to add

        Returns:
            List of StateChange objects representing changes made
        """
        pass

    @abstractmethod
    def get_current_version(self) -> int:
        """
        Get the current state version.

        Returns:
            Current version number
        """
        pass

    @abstractmethod
    def increment_version(self) -> int:
        """
        Increment the state version and record the timestamp.

        Returns:
            The new version number
        """
        pass

    @abstractmethod
    def get_version_timestamp(self, version: int) -> datetime | None:
        """
        Get the timestamp when a specific version was created.

        Args:
            version: The version number

        Returns:
            Timestamp of the version, or None if version doesn't exist
        """
        pass

    @abstractmethod
    def get_entity_version(self, entity_id: str) -> int | None:
        """
        Get the version number when an entity was added.

        Args:
            entity_id: The unique identifier of the entity

        Returns:
            Version number, or None if entity doesn't exist
        """
        pass

    @abstractmethod
    def get_similar(
        self,
        entity: BaseStateEntity,
        threshold: float = 0.8,
        limit: int = 10,
        order_by: str = "similarity"
    ) -> list[tuple[BaseStateEntity, float]]:
        """
        Get semantically similar entities with their similarity scores.

        Args:
            entity: The entity to find similar entities for
            threshold: Minimum similarity score (0-1)
            limit: Maximum number of results to return
            order_by: How to order results - "similarity" (default) or "chronological"

        Returns:
            List of (entity, similarity_score) tuples
            - If order_by="similarity": sorted by similarity score descending
            - If order_by="chronological": sorted by insertion order (oldest first)
        """
        pass

    @abstractmethod
    def get_by_id(self, entity_id: str) -> BaseStateEntity | None:
        """
        Get entity by ID.

        Args:
            entity_id: The unique identifier of the entity

        Returns:
            The entity if found, None otherwise
        """
        pass

    @abstractmethod
    def get_all(self, chronological: bool = True) -> list[BaseStateEntity]:
        """
        Get all stored entities.

        Args:
            chronological: If True, return entities in chronological order (oldest first)
                          If False, no specific order guaranteed

        Returns:
            List of all entities
        """
        pass

    @abstractmethod
    def get_chronological_range(
        self,
        start_index: int = 0,
        limit: int | None = None
    ) -> list[BaseStateEntity]:
        """
        Get entities in chronological order with pagination.

        Args:
            start_index: Starting index (0-based)
            limit: Maximum number of entities to return (None = all)

        Returns:
            List of entities in chronological order
        """
        pass

    @abstractmethod
    def to_json(self) -> dict:
        """
        Serialize storage to JSON-compatible dictionary.
        Must preserve insertion order when deserialized.

        Returns:
            JSON-compatible dictionary representation
        """
        pass

    @classmethod
    @abstractmethod
    def from_json(cls, data: dict, embedding_service: EmbeddingService) -> 'StateStorage':
        """
        Deserialize storage from JSON-compatible dictionary.
        Preserves insertion order from serialization.

        Args:
            data: JSON-compatible dictionary from to_json()
            embedding_service: Embedding service to use for the storage

        Returns:
            Reconstructed StateStorage instance
        """
        pass


class InMemoryStateStorage(StateStorage):
    """
    In-memory state storage using embeddings for semantic search.
    Maintains insertion order and supports chronological retrieval.
    Tracks state versions for all updates.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        similarity_metric: Callable[[np.ndarray, np.ndarray], float] | None = None
    ):
        """
        Initialize the in-memory storage.

        Args:
            embedding_service: Service for generating embeddings
            similarity_metric: Function to calculate similarity between vectors
                              (defaults to cosine_similarity)
        """
        self.entities: dict[str, BaseStateEntity] = {}
        self.embedding_index: dict[str, np.ndarray] = {}

        # Chronological ordering: list of entity IDs in insertion order
        self.chronological_ids: list[str] = []

        # Version tracking
        self.current_version: int = 0
        self.version_timestamps: dict[int, datetime] = {}
        self.entity_versions: dict[str, int] = {}  # Maps entity_id -> version

        self.embedding_service = embedding_service
        self.similarity_metric = similarity_metric or cosine_similarity

    def get_current_version(self) -> int:
        """
        Get the current state version.

        Returns:
            Current version number
        """
        return self.current_version

    def increment_version(self) -> int:
        """
        Increment the state version and record the timestamp.

        Returns:
            The new version number
        """
        self.current_version += 1
        self.version_timestamps[self.current_version] = datetime.now(timezone.utc)
        return self.current_version

    def get_version_timestamp(self, version: int) -> datetime | None:
        """
        Get the timestamp when a specific version was created.

        Args:
            version: The version number

        Returns:
            Timestamp of the version, or None if version doesn't exist
        """
        return self.version_timestamps.get(version)

    def get_entity_version(self, entity_id: str) -> int | None:
        """
        Get the version number when an entity was added.

        Args:
            entity_id: The unique identifier of the entity

        Returns:
            Version number, or None if entity doesn't exist
        """
        return self.entity_versions.get(entity_id)

    def add_entities(self, entities: list[BaseStateEntity]) -> list[StateChange]:
        """
        Add multiple entities in a single state update.
        Increments the state version and assigns it to all entities.

        Args:
            entities: List of state entities to add

        Returns:
            List of StateChange objects representing changes made
        """
        # First, increment the version (happens before adding any entities)
        version = self.increment_version()

        # Track state changes
        state_changes: list[StateChange] = []

        # Then add all entities with this version
        for entity in entities:
            # For InMemoryStateStorage, all entities are treated as new
            # since we don't have a concept of "updating" existing entities
            # Context ref is the entity's class
            context_ref = type(entity).__name__

            state_change = compare_entities(None, entity, context_ref)
            if state_change:
                state_changes.append(state_change)

            # Add the entity
            self._add_single(entity, version)

        return state_changes

    def _add_single(self, entity: BaseStateEntity, version: int) -> str:
        """
        Internal method to add a single entity with a specific version.

        Args:
            entity: The state entity to add
            version: The state version this entity belongs to

        Returns:
            Unique identifier for the stored entity
        """
        # Generate ID
        entity_id = str(uuid.uuid4())

        # Generate embedding if not present
        if entity.embedding is None:
            entity.embedding = self.embedding_service.embed(entity)

        # Store entity and its embedding
        self.entities[entity_id] = entity
        self.embedding_index[entity_id] = np.array(entity.embedding)

        # Track version for this entity
        self.entity_versions[entity_id] = version

        # Track chronological order
        self.chronological_ids.append(entity_id)

        return entity_id

    def get_similar(
        self,
        entity: BaseStateEntity,
        threshold: float = 0.8,
        limit: int = 10,
        order_by: str = "similarity"
    ) -> list[tuple[BaseStateEntity, float]]:
        """
        Find similar entities using embedding similarity.
        Can return results ordered by similarity score or chronological insertion order.

        Args:
            entity: The entity to find similar entities for
            threshold: Minimum similarity score (0-1)
            limit: Maximum number of results to return
            order_by: How to order results - "similarity" or "chronological"

        Returns:
            List of (entity, similarity_score) tuples
        """
        # Generate embedding for query entity
        if entity.embedding is None:
            entity.embedding = self.embedding_service.embed(entity)

        query_embedding = np.array(entity.embedding)

        # Calculate similarities and track insertion order
        similarities: list[tuple[str, float, int]] = []
        for entity_id, stored_embedding in self.embedding_index.items():
            similarity = self.similarity_metric(query_embedding, stored_embedding)
            if similarity >= threshold:
                # Get chronological index for this entity
                chrono_index = self.chronological_ids.index(entity_id)
                similarities.append((entity_id, similarity, chrono_index))

        # Sort based on requested order
        if order_by == "chronological":
            # Sort by chronological index (oldest first)
            similarities.sort(key=lambda x: x[2])
        else:  # "similarity" or default
            # Sort by similarity (highest first)
            similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top results with entities
        results = [
            (self.entities[entity_id], score)
            for entity_id, score, _ in similarities[:limit]
        ]

        return results

    def get_by_id(self, entity_id: str) -> BaseStateEntity | None:
        """
        Get entity by ID.

        Args:
            entity_id: The unique identifier of the entity

        Returns:
            The entity if found, None otherwise
        """
        return self.entities.get(entity_id)

    def get_all(self, chronological: bool = True) -> list[BaseStateEntity]:
        """
        Get all entities, optionally in chronological order.

        Args:
            chronological: If True, return in insertion order

        Returns:
            List of all entities
        """
        if chronological:
            return [self.entities[entity_id] for entity_id in self.chronological_ids]
        else:
            return list(self.entities.values())

    def get_chronological_range(
        self,
        start_index: int = 0,
        limit: int | None = None
    ) -> list[BaseStateEntity]:
        """
        Get entities in chronological order with pagination.

        Args:
            start_index: Starting index (0-based)
            limit: Maximum number of entities to return (None = all)

        Returns:
            List of entities in chronological order
        """
        if limit is None:
            entity_ids = self.chronological_ids[start_index:]
        else:
            entity_ids = self.chronological_ids[start_index:start_index + limit]

        return [self.entities[entity_id] for entity_id in entity_ids]

    def to_json(self) -> dict:
        """
        Serialize storage to JSON-compatible dictionary.
        Uses chronological_ids list to preserve insertion order.
        Includes version tracking information.

        Returns:
            JSON-compatible dictionary
        """
        return {
            "format_version": "1.0",
            "current_version": self.current_version,
            "version_timestamps": {
                str(ver): ts.isoformat()
                for ver, ts in self.version_timestamps.items()
            },
            "entities": [
                {
                    "id": entity_id,
                    "entity": self.entities[entity_id].model_dump(mode='json'),
                    "embedding": self.embedding_index[entity_id].tolist(),
                    "version": self.entity_versions[entity_id]
                }
                for entity_id in self.chronological_ids  # Iterate in insertion order
            ]
        }

    @classmethod
    def from_json(cls, data: dict, embedding_service: EmbeddingService) -> 'InMemoryStateStorage':
        """
        Deserialize storage from JSON-compatible dictionary.
        Reconstructs entities in their original insertion order.
        Restores version tracking information.

        Args:
            data: JSON-compatible dictionary from to_json()
            embedding_service: Embedding service to use for the storage

        Returns:
            Reconstructed InMemoryStateStorage instance
        """
        storage = cls(embedding_service=embedding_service)

        # Restore version tracking
        storage.current_version = data.get("current_version", 0)
        storage.version_timestamps = {
            int(ver): datetime.fromisoformat(ts)
            for ver, ts in data.get("version_timestamps", {}).items()
        }

        # Process entities in the order they appear in the JSON
        # This preserves the original insertion order
        for item in data["entities"]:
            entity_id = item["id"]

            # Reconstruct entity from its data
            entity_data = item["entity"]

            # Dynamically reconstruct the entity
            # Since we don't know the exact type, we'll use BaseStateEntity
            # In practice, you might want to store type information
            entity = BaseStateEntity.model_validate(entity_data)

            # Restore embedding
            embedding = np.array(item["embedding"])

            # Restore version
            entity_version = item.get("version", 0)

            # Manually restore to preserve original IDs and avoid incrementing version
            storage.entities[entity_id] = entity
            storage.embedding_index[entity_id] = embedding
            storage.entity_versions[entity_id] = entity_version
            storage.chronological_ids.append(entity_id)

        return storage
