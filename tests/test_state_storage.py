"""Unit tests for state storage implementation."""

import json
import os
import sys
import unittest
from datetime import datetime, timezone

# Ensure the 'src' directory is on sys.path
THIS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from pydantic import BaseModel

from agent.state_entity import BaseStateEntity
from agent.state_storage import EmbeddingService, InMemoryStateStorage
from agent.types import MutationIntent, FieldDiff


class MockEmbeddingService(EmbeddingService):
    """Mock embedding service for testing."""

    def embed(self, entity: BaseStateEntity) -> list[float]:
        """Return a simple embedding based on entity content."""
        if entity.embedding is not None:
            return entity.embedding

        content_str = str(entity.content)
        hash_val = hash(content_str)

        return [
            ((hash_val + 1) % 1000) / 1000.0,
            ((hash_val + 2) % 1000) / 1000.0,
            ((hash_val + 3) % 1000) / 1000.0,
        ]

    def embed_text(self, text: str) -> list[float]:
        """Return a simple embedding based on text."""
        hash_val = hash(text)
        return [
            ((hash_val + 1) % 1000) / 1000.0,
            ((hash_val + 2) % 1000) / 1000.0,
            ((hash_val + 3) % 1000) / 1000.0,
        ]

    def embed_batch(self, entities: list[BaseStateEntity]) -> list[list[float]]:
        """Batch embed entities."""
        return [self.embed(entity) for entity in entities]


class TestContent(BaseModel):
    """Test content model for unit tests."""
    value: str


class TestEntity(BaseStateEntity[TestContent]):
    """Test entity for unit tests."""
    pass


class TestInMemoryStateStorage(unittest.TestCase):
    """Tests for InMemoryStateStorage."""

    def test_add_entity(self):
        """Test adding an entity to storage."""
        storage = InMemoryStateStorage(MockEmbeddingService())
        entity = TestEntity(content=TestContent(value="Test content"))

        intents = storage.add_entities([entity])

        # Verify intents were returned
        assert len(intents) == 1
        assert isinstance(intents[0], MutationIntent)

        # Verify entity was added
        assert storage.get_current_version() == 1
        all_entities = storage.get_all()
        assert len(all_entities) == 1
        assert all_entities[0].content.value == "Test content"

    def test_chronological_order(self):
        """Test that entities are stored in chronological order."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        entity1 = TestEntity(content=TestContent(value="First"))
        entity2 = TestEntity(content=TestContent(value="Second"))
        entity3 = TestEntity(content=TestContent(value="Third"))

        storage.add_entities([entity1, entity2, entity3])

        all_entities = storage.get_all(chronological=True)

        assert len(all_entities) == 3
        assert all_entities[0].content.value == "First"
        assert all_entities[1].content.value == "Second"
        assert all_entities[2].content.value == "Third"

    def test_chronological_pagination(self):
        """Test chronological retrieval with pagination."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        entities = [
            TestEntity(content=TestContent(value=f"Entity {i}"))
            for i in range(10)
        ]
        storage.add_entities(entities)

        first_5 = storage.get_chronological_range(0, 5)
        next_5 = storage.get_chronological_range(5, 5)

        assert len(first_5) == 5
        assert len(next_5) == 5
        assert first_5[0].content.value == "Entity 0"
        assert next_5[0].content.value == "Entity 5"

    def test_similarity_search(self):
        """Test similarity-based search."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        entity1 = TestEntity(content=TestContent(value="Entity 1"))
        entity1.embedding = [1.0, 0.0, 0.0]

        entity2 = TestEntity(content=TestContent(value="Entity 2"))
        entity2.embedding = [0.9, 0.1, 0.0]

        entity3 = TestEntity(content=TestContent(value="Entity 3"))
        entity3.embedding = [0.0, 0.0, 1.0]

        storage.add_entities([entity1, entity2, entity3])

        query = TestEntity(content=TestContent(value="Query"))
        query.embedding = [1.0, 0.0, 0.0]

        results = storage.get_similar(query, threshold=0.8, limit=10)

        assert len(results) >= 1
        assert results[0][1] >= results[-1][1]

    def test_similarity_search_with_chronological_ordering(self):
        """Test that similarity search can return results in chronological order."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        entity1 = TestEntity(content=TestContent(value="Task A"))
        entity1.embedding = [0.8, 0.2, 0.0]

        entity2 = TestEntity(content=TestContent(value="Task B"))
        entity2.embedding = [0.9, 0.1, 0.0]

        entity3 = TestEntity(content=TestContent(value="Task C"))
        entity3.embedding = [0.7, 0.3, 0.0]

        storage.add_entities([entity1, entity2, entity3])

        query = TestEntity(content=TestContent(value="Query"))
        query.embedding = [1.0, 0.0, 0.0]

        results_by_similarity = storage.get_similar(
            query, threshold=0.6, order_by="similarity"
        )
        assert len(results_by_similarity) == 3
        assert results_by_similarity[0][0].content.value == "Task B"
        assert results_by_similarity[1][0].content.value == "Task A"
        assert results_by_similarity[2][0].content.value == "Task C"

        results_by_chrono = storage.get_similar(
            query, threshold=0.6, order_by="chronological"
        )
        assert len(results_by_chrono) == 3
        assert results_by_chrono[0][0].content.value == "Task A"
        assert results_by_chrono[1][0].content.value == "Task B"
        assert results_by_chrono[2][0].content.value == "Task C"

    def test_json_serialization_preserves_order(self):
        """Test that JSON serialization/deserialization preserves insertion order."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        entities = []
        for i in range(5):
            entity = TestEntity(content=TestContent(value=f"Entity {i}"))
            entity.embedding = [float(i), 0.0, 0.0]
            entities.append(entity)

        storage.add_entities(entities)

        json_data = storage.to_json()

        json_str = json.dumps(json_data)
        assert json_str is not None

        restored_storage = InMemoryStateStorage.from_json(
            json_data, MockEmbeddingService()
        )

        original_entities = storage.get_all(chronological=True)
        restored_entities = restored_storage.get_all(chronological=True)

        assert len(original_entities) == len(restored_entities)
        for i, (orig, restored) in enumerate(zip(original_entities, restored_entities)):
            assert orig.content.value == f"Entity {i}"

    def test_json_serialization_preserves_embeddings(self):
        """Test that embeddings are correctly preserved through serialization."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        entity = TestEntity(content=TestContent(value="Test Entity"))
        entity.embedding = [0.1, 0.2, 0.3]
        storage.add_entities([entity])

        json_data = storage.to_json()
        restored_storage = InMemoryStateStorage.from_json(
            json_data, MockEmbeddingService()
        )

        restored_entities = restored_storage.get_all()
        assert len(restored_entities) == 1

        query = TestEntity(content=TestContent(value="Test Query"))
        query.embedding = [0.1, 0.2, 0.3]
        results = restored_storage.get_similar(query, threshold=0.99)

        assert len(results) == 1
        assert results[0][1] > 0.99

    def test_empty_storage_serialization(self):
        """Test that empty storage can be serialized and deserialized."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        # Serialize empty storage
        json_data = storage.to_json()
        assert json_data["entities"] == []

        # Deserialize
        restored_storage = InMemoryStateStorage.from_json(
            json_data, MockEmbeddingService()
        )
        assert len(restored_storage.get_all()) == 0

    def test_get_by_id_not_found(self):
        """Test getting entity by ID when it doesn't exist."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        result = storage.get_by_id("nonexistent-id")
        assert result is None

    def test_chronological_range_out_of_bounds(self):
        """Test chronological range with out-of-bounds indices."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        entities = [
            TestEntity(content=TestContent(value=f"Entity {i}"))
            for i in range(3)
        ]
        storage.add_entities(entities)

        result = storage.get_chronological_range(10, 5)
        assert len(result) == 0

        result = storage.get_chronological_range(1, 10)
        assert len(result) == 2

    def test_similarity_threshold_filtering(self):
        """Test that similarity threshold correctly filters results."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        entity1 = TestEntity(content=TestContent(value="Very similar"))
        entity1.embedding = [0.95, 0.05, 0.0]

        entity2 = TestEntity(content=TestContent(value="Somewhat similar"))
        entity2.embedding = [0.7, 0.3, 0.0]

        entity3 = TestEntity(content=TestContent(value="Not similar"))
        entity3.embedding = [0.1, 0.1, 0.8]

        storage.add_entities([entity1, entity2, entity3])

        query = TestEntity(content=TestContent(value="Query"))
        query.embedding = [1.0, 0.0, 0.0]

        results_high = storage.get_similar(query, threshold=0.9, limit=10)
        assert len(results_high) <= 2

        results_low = storage.get_similar(query, threshold=0.5, limit=10)
        assert len(results_low) >= len(results_high)

    def test_auto_embedding_generation(self):
        """Test that embeddings are automatically generated when not present."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        entity = TestEntity(content=TestContent(value="Test content"))

        storage.add_entities([entity])

        stored_entities = storage.get_all()
        assert len(stored_entities) == 1
        assert stored_entities[0].embedding is not None
        assert len(stored_entities[0].embedding) > 0

    def test_version_tracking(self):
        """Test that state versions are properly tracked."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        assert storage.get_current_version() == 0

        entity1 = TestEntity(content=TestContent(value="First"))
        storage.add_entities([entity1])
        assert storage.get_current_version() == 1
        assert storage.get_version_timestamp(1) is not None

        entity2 = TestEntity(content=TestContent(value="Second"))
        storage.add_entities([entity2])
        assert storage.get_current_version() == 2

        all_entities = storage.get_all()
        assert len(all_entities) == 2

    def test_multiple_entities_same_version(self):
        """Test that multiple entities in one update share the same version."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        entities = [
            TestEntity(content=TestContent(value=f"Entity {i}"))
            for i in range(3)
        ]
        intents = storage.add_entities(entities)

        assert len(intents) == 3
        assert storage.get_current_version() == 1

    def test_version_serialization(self):
        """Test that version information is preserved through serialization."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        entity1 = TestEntity(content=TestContent(value="Version 1 Entity"))
        entity1.embedding = [1.0, 0.0, 0.0]
        storage.add_entities([entity1])

        entity2 = TestEntity(content=TestContent(value="Version 2 Entity"))
        entity2.embedding = [0.0, 1.0, 0.0]
        storage.add_entities([entity2])

        json_data = storage.to_json()

        assert "current_version" in json_data
        assert json_data["current_version"] == 2
        assert "version_timestamps" in json_data
        assert "1" in json_data["version_timestamps"]
        assert "2" in json_data["version_timestamps"]

        restored_storage = InMemoryStateStorage.from_json(
            json_data, MockEmbeddingService()
        )

        assert restored_storage.get_current_version() == 2
        assert restored_storage.get_version_timestamp(1) is not None
        assert restored_storage.get_version_timestamp(2) is not None

        all_entities = restored_storage.get_all()
        assert len(all_entities) == 2

    def test_controller_version_increment(self):
        """Test that BaseStateController properly increments versions."""
        from agent.state_controller import BaseStateController

        controller = BaseStateController()

        assert controller.storage.get_current_version() == 0

        entities1 = [
            TestEntity(content=TestContent(value="Entity 1")),
            TestEntity(content=TestContent(value="Entity 2")),
        ]

        controller.update_state(entities1)
        assert controller.storage.get_current_version() == 1

        entities2 = [
            TestEntity(content=TestContent(value="Entity 3")),
        ]

        controller.update_state(entities2)
        assert controller.storage.get_current_version() == 2

        all_entities = controller.storage.get_all()
        assert len(all_entities) == 3


class TestMutationIntentTracking(unittest.TestCase):
    """Tests for mutation intent tracking functionality."""

    def test_new_entity_creates_intent(self):
        """Test that adding a new entity creates a mutation intent with all fields."""
        storage = InMemoryStateStorage(MockEmbeddingService())
        entity = TestEntity(content=TestContent(value="test value"))

        intents = storage.add_entities([entity])

        assert len(intents) == 1
        intent = intents[0]
        assert isinstance(intent, MutationIntent)
        assert intent.model_class_name == "TestEntity"

    def test_bb_state_storage_new_entities(self):
        """Test BBStateStorage creates mutation intents for new entities."""
        from examples.boat_booking.bb_state_storage import BBStateStorage
        from examples.boat_booking.state_entity import BoatSpecEntity, BoatSpec
        from agent.types import MutationIntent, FieldDiff

        storage = BBStateStorage()

        intent = MutationIntent(
            model_class_name='BoatSpecEntity',
            diffs=[
                FieldDiff(field_name='boat_type', new_value='catamaran'),
                FieldDiff(field_name='boat_length_ft', new_value=40),
                FieldDiff(field_name='number_of_cabins', new_value=3)
            ]
        )

        applied_intents = storage.add_intents([intent])

        assert len(applied_intents) == 1
        applied_intent = applied_intents[0]
        assert applied_intent.model_class_name == "BoatSpecEntity"
        assert len(applied_intent.diffs) == 3

    def test_bb_state_storage_entity_update(self):
        """Test BBStateStorage tracks changes when updating an entity."""
        from examples.boat_booking.bb_state_storage import BBStateStorage
        from examples.boat_booking.state_entity import BoatSpecEntity, BoatSpec
        from agent.types import MutationIntent, FieldDiff

        storage = BBStateStorage()

        initial_intent = MutationIntent(
            model_class_name='BoatSpecEntity',
            diffs=[
                FieldDiff(field_name='boat_type', new_value='monohull'),
                FieldDiff(field_name='boat_length_ft', new_value=30),
                FieldDiff(field_name='number_of_cabins', new_value=2)
            ]
        )
        storage.add_intents([initial_intent])

        update_intent = MutationIntent(
            model_class_name='BoatSpecEntity',
            diffs=[
                FieldDiff(field_name='boat_type', new_value='catamaran'),
                FieldDiff(field_name='boat_length_ft', new_value=40),
            ]
        )

        applied_intents = storage.add_intents([update_intent])

        assert len(applied_intents) == 1
        assert applied_intents[0].model_class_name == "BoatSpecEntity"

    def test_multiple_entities_multiple_intents(self):
        """Test tracking intents across multiple different entity types."""
        from examples.boat_booking.bb_state_storage import BBStateStorage
        from agent.types import MutationIntent, FieldDiff

        storage = BBStateStorage()

        boat_intent = MutationIntent(
            model_class_name='BoatSpecEntity',
            diffs=[
                FieldDiff(field_name='boat_type', new_value='catamaran'),
                FieldDiff(field_name='boat_length_ft', new_value=40),
            ]
        )

        location_intent = MutationIntent(
            model_class_name='DesiredLocationEntity',
            diffs=[
                FieldDiff(field_name='country', new_value='Greece'),
                FieldDiff(field_name='region', new_value='Cyclades'),
            ]
        )

        applied_intents = storage.add_intents([boat_intent, location_intent])

        assert len(applied_intents) == 2

        class_names = {intent.model_class_name for intent in applied_intents}
        assert "BoatSpecEntity" in class_names
        assert "DesiredLocationEntity" in class_names


if __name__ == "__main__":
    unittest.main()
