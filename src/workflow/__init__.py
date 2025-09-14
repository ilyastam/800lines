"""
Workflow - A Python workflow library.

This library provides tools for building and managing workflows.
"""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Main exports - add your public API here
__all__ = [
    "__version__",
    "Workflow",
    "Task",
    "Pipeline",
]

from .core import Workflow, Task, Pipeline

# Optional: Add convenient imports for common use cases
# from .decorators import task, workflow
# from .exceptions import WorkflowError, TaskError


