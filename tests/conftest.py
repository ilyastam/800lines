"""Pytest configuration and fixtures."""

from __future__ import annotations

import pytest
from typing import Any, Dict

from workflow import Task, Pipeline, Workflow


@pytest.fixture
def sample_task() -> Task:
    """Create a sample task for testing."""
    def sample_func() -> str:
        return "sample_output"
    
    return Task(name="sample_task", func=sample_func)


@pytest.fixture
def sample_pipeline() -> Pipeline:
    """Create a sample pipeline."""
    return Pipeline("test_pipeline")


@pytest.fixture
def sample_workflow() -> Workflow:
    """Create a sample workflow."""
    return Workflow("test_workflow")

