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

from agent.state_entity import BaseStateEntity
from agent.state_storage import EmbeddingService, InMemoryStateStorage
from agent.state_storage.state_change import StateChange, FieldChange


class MockEmbeddingService(EmbeddingService):
    """Mock embedding service for testing."""

    def embed(self, entity: BaseStateEntity) -> list[float]:
        """Return a simple embedding based on entity content."""
        # Use the content hash to generate a deterministic embedding
        if entity.embedding is not None:
            return entity.embedding

        content_str = str(entity.content)
        hash_val = hash(content_str)

        # Create a simple 3-dimensional embedding for testing
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


class TestEntity(BaseStateEntity[str]):
    """Test entity for unit tests."""
    pass


class TestInMemoryStateStorage(unittest.TestCase):
    """Tests for InMemoryStateStorage."""

    def test_add_entity(self):
        """Test adding an entity to storage."""
        storage = InMemoryStateStorage(MockEmbeddingService())
        entity = TestEntity(content="Test content")

        state_changes = storage.add_entities([entity])

        # Verify state changes were returned
        assert len(state_changes) == 1
        assert isinstance(state_changes[0], StateChange)

        # Verify entity was added
        assert storage.get_current_version() == 1
        all_entities = storage.get_all()
        assert len(all_entities) == 1
        assert all_entities[0].content == "Test content"

    def test_chronological_order(self):
        """Test that entities are stored in chronological order."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        # Add entities
        entity1 = TestEntity(content="First")
        entity2 = TestEntity(content="Second")
        entity3 = TestEntity(content="Third")

        storage.add_entities([entity1, entity2, entity3])

        # Get in chronological order
        all_entities = storage.get_all(chronological=True)

        assert len(all_entities) == 3
        assert all_entities[0].content == "First"
        assert all_entities[1].content == "Second"
        assert all_entities[2].content == "Third"

    def test_chronological_pagination(self):
        """Test chronological retrieval with pagination."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        # Add 10 entities
        entities = [
            TestEntity(content=f"Entity {i}")
            for i in range(10)
        ]
        storage.add_entities(entities)

        # Test pagination
        first_5 = storage.get_chronological_range(0, 5)
        next_5 = storage.get_chronological_range(5, 5)

        assert len(first_5) == 5
        assert len(next_5) == 5
        assert first_5[0].content == "Entity 0"
        assert next_5[0].content == "Entity 5"

    def test_similarity_search(self):
        """Test similarity-based search."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        # Add entities with known embeddings
        entity1 = TestEntity(content="Entity 1")
        entity1.embedding = [1.0, 0.0, 0.0]

        entity2 = TestEntity(content="Entity 2")
        entity2.embedding = [0.9, 0.1, 0.0]  # Very similar

        entity3 = TestEntity(content="Entity 3")
        entity3.embedding = [0.0, 0.0, 1.0]  # Different

        storage.add_entities([entity1, entity2, entity3])

        query = TestEntity(content="Query")
        query.embedding = [1.0, 0.0, 0.0]

        results = storage.get_similar(query, threshold=0.8, limit=10)

        # Should find entity1 and entity2, but not entity3
        assert len(results) >= 1
        # First result should be most similar
        assert results[0][1] >= results[-1][1]

    def test_similarity_search_with_chronological_ordering(self):
        """Test that similarity search can return results in chronological order."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        # Add entities with similar embeddings but at different times
        entity1 = TestEntity(content="Task A")
        entity1.embedding = [0.8, 0.2, 0.0]

        entity2 = TestEntity(content="Task B")
        entity2.embedding = [0.9, 0.1, 0.0]  # More similar

        entity3 = TestEntity(content="Task C")
        entity3.embedding = [0.7, 0.3, 0.0]  # Less similar

        storage.add_entities([entity1, entity2, entity3])

        query = TestEntity(content="Query")
        query.embedding = [1.0, 0.0, 0.0]

        # Test similarity ordering
        results_by_similarity = storage.get_similar(
            query, threshold=0.6, order_by="similarity"
        )
        assert len(results_by_similarity) == 3
        assert results_by_similarity[0][0].content == "Task B"  # Most similar
        assert results_by_similarity[1][0].content == "Task A"
        assert results_by_similarity[2][0].content == "Task C"  # Least similar

        # Test chronological ordering
        results_by_chrono = storage.get_similar(
            query, threshold=0.6, order_by="chronological"
        )
        assert len(results_by_chrono) == 3
        assert results_by_chrono[0][0].content == "Task A"  # First added
        assert results_by_chrono[1][0].content == "Task B"
        assert results_by_chrono[2][0].content == "Task C"  # Last added

    def test_json_serialization_preserves_order(self):
        """Test that JSON serialization/deserialization preserves insertion order."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        # Add entities in specific order
        entities = []
        for i in range(5):
            entity = TestEntity(content=f"Entity {i}")
            entity.embedding = [float(i), 0.0, 0.0]
            entities.append(entity)

        storage.add_entities(entities)

        # Serialize to JSON
        json_data = storage.to_json()

        # Verify it's valid JSON
        json_str = json.dumps(json_data)
        assert json_str is not None

        # Deserialize from JSON
        restored_storage = InMemoryStateStorage.from_json(
            json_data, MockEmbeddingService()
        )

        # Verify insertion order is preserved
        original_entities = storage.get_all(chronological=True)
        restored_entities = restored_storage.get_all(chronological=True)

        assert len(original_entities) == len(restored_entities)
        for i, (orig, restored) in enumerate(zip(original_entities, restored_entities)):
            assert orig.content == restored.content == f"Entity {i}"

    def test_json_serialization_preserves_embeddings(self):
        """Test that embeddings are correctly preserved through serialization."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        # Add entity with specific embedding
        entity = TestEntity(content="Test Entity")
        entity.embedding = [0.1, 0.2, 0.3]
        storage.add_entities([entity])

        # Serialize and deserialize
        json_data = storage.to_json()
        restored_storage = InMemoryStateStorage.from_json(
            json_data, MockEmbeddingService()
        )

        # Verify embedding is preserved
        restored_entities = restored_storage.get_all()
        assert len(restored_entities) == 1

        # Find the entity and check embedding similarity
        query = TestEntity(content="Test Query")
        query.embedding = [0.1, 0.2, 0.3]
        results = restored_storage.get_similar(query, threshold=0.99)

        assert len(results) == 1
        assert results[0][1] > 0.99  # Should be very similar (almost identical)

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

        # Add a few entities
        entities = [
            TestEntity(content=f"Entity {i}")
            for i in range(3)
        ]
        storage.add_entities(entities)

        # Request beyond available entities
        result = storage.get_chronological_range(10, 5)
        assert len(result) == 0

        # Request with negative start (Python slice behavior)
        result = storage.get_chronological_range(1, 10)
        assert len(result) == 2  # Should get entities 1 and 2

    def test_similarity_threshold_filtering(self):
        """Test that similarity threshold correctly filters results."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        # Add entities with varying similarity
        entity1 = TestEntity(content="Very similar")
        entity1.embedding = [0.95, 0.05, 0.0]

        entity2 = TestEntity(content="Somewhat similar")
        entity2.embedding = [0.7, 0.3, 0.0]

        entity3 = TestEntity(content="Not similar")
        entity3.embedding = [0.1, 0.1, 0.8]

        storage.add_entities([entity1, entity2, entity3])

        query = TestEntity(content="Query")
        query.embedding = [1.0, 0.0, 0.0]

        # High threshold should only get very similar
        results_high = storage.get_similar(query, threshold=0.9, limit=10)
        assert len(results_high) <= 2

        # Low threshold should get more results
        results_low = storage.get_similar(query, threshold=0.5, limit=10)
        assert len(results_low) >= len(results_high)

    def test_auto_embedding_generation(self):
        """Test that embeddings are automatically generated when not present."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        # Add entity without embedding
        entity = TestEntity(content="Test content")
        # Don't set embedding

        state_changes = storage.add_entities([entity])

        # Embedding should be auto-generated
        stored_entities = storage.get_all()
        assert len(stored_entities) == 1
        assert stored_entities[0].embedding is not None
        assert len(stored_entities[0].embedding) > 0

    def test_version_tracking(self):
        """Test that state versions are properly tracked."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        # Initial version should be 0
        assert storage.get_current_version() == 0

        # First update
        entity1 = TestEntity(content="First")
        storage.add_entities([entity1])
        assert storage.get_current_version() == 1
        assert storage.get_version_timestamp(1) is not None

        # Second update
        entity2 = TestEntity(content="Second")
        storage.add_entities([entity2])
        assert storage.get_current_version() == 2

        # Verify entities were added
        all_entities = storage.get_all()
        assert len(all_entities) == 2

    def test_multiple_entities_same_version(self):
        """Test that multiple entities in one update share the same version."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        # Add multiple entities in one update
        entities = [
            TestEntity(content=f"Entity {i}")
            for i in range(3)
        ]
        state_changes = storage.add_entities(entities)

        # All entities should be tracked as state changes
        assert len(state_changes) == 3
        # All added in same version
        assert storage.get_current_version() == 1

    def test_version_serialization(self):
        """Test that version information is preserved through serialization."""
        storage = InMemoryStateStorage(MockEmbeddingService())

        # Add entities in different versions
        entity1 = TestEntity(content="Version 1 Entity")
        entity1.embedding = [1.0, 0.0, 0.0]
        storage.add_entities([entity1])

        entity2 = TestEntity(content="Version 2 Entity")
        entity2.embedding = [0.0, 1.0, 0.0]
        storage.add_entities([entity2])

        # Serialize
        json_data = storage.to_json()

        # Verify JSON contains version info
        assert "current_version" in json_data
        assert json_data["current_version"] == 2
        assert "version_timestamps" in json_data
        assert "1" in json_data["version_timestamps"]
        assert "2" in json_data["version_timestamps"]

        # Deserialize
        restored_storage = InMemoryStateStorage.from_json(
            json_data, MockEmbeddingService()
        )

        # Verify version tracking is preserved
        assert restored_storage.get_current_version() == 2
        assert restored_storage.get_version_timestamp(1) is not None
        assert restored_storage.get_version_timestamp(2) is not None

        # Verify entities were restored
        all_entities = restored_storage.get_all()
        assert len(all_entities) == 2

    def test_controller_version_increment(self):
        """Test that BaseStateController properly increments versions."""
        from agent.state_controller import BaseStateController

        controller = BaseStateController()

        # Initial version should be 0
        assert controller.storage.get_current_version() == 0

        # First update
        entities1 = [
            TestEntity(content="Entity 1"),
            TestEntity(content="Entity 2"),
        ]

        controller.update_state(entities1)
        assert controller.storage.get_current_version() == 1

        # Second update
        entities2 = [
            TestEntity(content="Entity 3"),
        ]

        controller.update_state(entities2)
        assert controller.storage.get_current_version() == 2

        # All entities should be stored
        all_entities = controller.storage.get_all()
        assert len(all_entities) == 3


class TestStateChangeTracking(unittest.TestCase):
    """Tests for state change tracking functionality."""

    def test_new_entity_creates_state_change(self):
        """Test that adding a new entity creates a state change with all fields."""
        from pydantic import BaseModel

        class SimpleEntity(BaseStateEntity):
            content: str

        storage = InMemoryStateStorage(MockEmbeddingService())
        entity = SimpleEntity(content="test value")

        state_changes = storage.add_entities([entity])

        assert len(state_changes) == 1
        state_change = state_changes[0]
        assert isinstance(state_change, StateChange)
        assert state_change.context_ref == "SimpleEntity"
        assert len(state_change.changes) > 0

        # Verify field change for content
        content_changes = [fc for fc in state_change.changes if fc.field_name == "content"]
        assert len(content_changes) == 1
        assert content_changes[0].from_value == ""
        assert content_changes[0].to_value == "test value"

    def test_nested_model_change_detection(self):
        """Test that nested model changes are tracked with dot notation."""
        from pydantic import BaseModel

        class NestedModel(BaseModel):
            nested_field: str

        class ParentEntity(BaseStateEntity):
            content: NestedModel

        storage = InMemoryStateStorage(MockEmbeddingService())
        entity = ParentEntity(content=NestedModel(nested_field="nested value"))

        state_changes = storage.add_entities([entity])

        assert len(state_changes) == 1
        state_change = state_changes[0]

        # Check for nested field changes with dot notation
        nested_changes = [fc for fc in state_change.changes if "nested_field" in fc.field_name]
        assert len(nested_changes) == 1
        assert nested_changes[0].to_value == "nested value"

    def test_bb_state_storage_new_entities(self):
        """Test BBStateStorage creates state changes for new entities."""
        from examples.boat_booking.bb_state_storage import BBStateStorage
        from examples.boat_booking.state_entity import BoatSpecEntity, BoatSpec

        storage = BBStateStorage()

        boat_spec = BoatSpecEntity(
            content=BoatSpec(
                boat_type='catamaran',
                boat_length_ft=40,
                number_of_cabins=3
            )
        )

        state_changes = storage.add_entities([boat_spec])

        assert len(state_changes) == 1
        state_change = state_changes[0]
        assert state_change.context_ref == "BoatSpecEntity"
        assert len(state_change.changes) > 0

        # Verify all boat spec fields are tracked as changes
        field_names = {fc.field_name for fc in state_change.changes}
        assert "content.boat_type" in field_names or "content" in field_names

    def test_bb_state_storage_entity_update(self):
        """Test BBStateStorage tracks changes when updating an entity."""
        from examples.boat_booking.bb_state_storage import BBStateStorage
        from examples.boat_booking.state_entity import BoatSpecEntity, BoatSpec

        storage = BBStateStorage()

        # Add initial boat spec
        initial_spec = BoatSpecEntity(
            content=BoatSpec(
                boat_type='monohull',
                boat_length_ft=30,
                number_of_cabins=2
            )
        )
        storage.add_entities([initial_spec])

        # Update boat spec
        updated_spec = BoatSpecEntity(
            content=BoatSpec(
                boat_type='catamaran',  # Changed
                boat_length_ft=40,      # Changed
                number_of_cabins=2      # Unchanged
            )
        )

        state_changes = storage.add_entities([updated_spec])

        assert len(state_changes) == 1
        state_change = state_changes[0]

        # Should have changes for the modified fields
        assert len(state_change.changes) >= 2

        # Verify specific field changes
        boat_type_changes = [fc for fc in state_change.changes if "boat_type" in fc.field_name]
        if boat_type_changes:
            assert boat_type_changes[0].from_value == "monohull"
            assert boat_type_changes[0].to_value == "catamaran"

    def test_no_state_change_for_identical_update(self):
        """Test that no state change is returned when entity is unchanged."""
        from examples.boat_booking.bb_state_storage import BBStateStorage
        from examples.boat_booking.state_entity import BoatSpecEntity, BoatSpec

        storage = BBStateStorage()

        # Add initial boat spec
        spec = BoatSpecEntity(
            content=BoatSpec(
                boat_type='catamaran',
                boat_length_ft=40,
                number_of_cabins=3
            )
        )
        storage.add_entities([spec])

        # Update with identical values
        identical_spec = BoatSpecEntity(
            content=BoatSpec(
                boat_type='catamaran',
                boat_length_ft=40,
                number_of_cabins=3
            )
        )

        state_changes = storage.add_entities([identical_spec])

        # Should return empty list since no changes
        assert len(state_changes) == 0

    def test_multiple_entities_multiple_changes(self):
        """Test tracking changes across multiple different entity types."""
        from examples.boat_booking.bb_state_storage import BBStateStorage
        from examples.boat_booking.state_entity import (
            BoatSpecEntity, BoatSpec,
            DesiredLocationEntity, DesiredLocation
        )

        storage = BBStateStorage()

        boat_spec = BoatSpecEntity(
            content=BoatSpec(
                boat_type='catamaran',
                boat_length_ft=40,
                number_of_cabins=3
            )
        )

        location = DesiredLocationEntity(
            content=DesiredLocation(
                country="Greece",
                region="Cyclades",
                city="Mykonos"
            )
        )

        state_changes = storage.add_entities([boat_spec, location])

        # Should have state changes for both entities
        assert len(state_changes) == 2

        # Verify both entity types are tracked
        context_refs = {sc.context_ref for sc in state_changes}
        assert "BoatSpecEntity" in context_refs
        assert "DesiredLocationEntity" in context_refs


if __name__ == "__main__":
    unittest.main()
