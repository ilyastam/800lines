"""
Custom exceptions for the workflow library.
"""

from __future__ import annotations


class WorkflowError(Exception):
    """Base exception for workflow-related errors."""
    pass


class TaskError(WorkflowError):
    """Exception raised when a task fails to execute."""
    
    def __init__(self, task_name: str, message: str, original_exception: Exception | None = None) -> None:
        """Initialize TaskError.
        
        Args:
            task_name: Name of the task that failed
            message: Error message
            original_exception: The original exception that caused this error
        """
        self.task_name = task_name
        self.original_exception = original_exception
        super().__init__(f"Task '{task_name}' failed: {message}")


class PipelineError(WorkflowError):
    """Exception raised when a pipeline fails to execute."""
    
    def __init__(self, pipeline_name: str, message: str) -> None:
        """Initialize PipelineError.
        
        Args:
            pipeline_name: Name of the pipeline that failed
            message: Error message
        """
        self.pipeline_name = pipeline_name
        super().__init__(f"Pipeline '{pipeline_name}' failed: {message}")


class DependencyError(WorkflowError):
    """Exception raised when there are dependency issues."""
    pass


class CircularDependencyError(DependencyError):
    """Exception raised when circular dependencies are detected."""
    
    def __init__(self, task_name: str) -> None:
        """Initialize CircularDependencyError.
        
        Args:
            task_name: Name of the task involved in circular dependency
        """
        self.task_name = task_name
        super().__init__(f"Circular dependency detected involving task: {task_name}")


class ValidationError(WorkflowError):
    """Exception raised when validation fails."""
    pass


