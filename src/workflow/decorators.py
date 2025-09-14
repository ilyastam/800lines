"""
Decorators for simplifying workflow creation.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, List, Optional, TypeVar

from .core import Task

F = TypeVar('F', bound=Callable[..., Any])


def task(
    name: Optional[str] = None,
    description: Optional[str] = None,
    dependencies: Optional[List[str]] = None,
    retry_count: int = 0,
    timeout: Optional[float] = None,
) -> Callable[[F], Task]:
    """Decorator to create a Task from a function."""
    def decorator(func: F) -> Task:
        task_name = name or func.__name__
        task_description = description or func.__doc__ or f"Task: {task_name}"
        
        return Task(
            name=task_name,
            func=func,
            description=task_description,
            dependencies=dependencies,
            retry_count=retry_count,
            timeout=timeout,
        )
    
    return decorator


def pipeline(name: Optional[str] = None, description: Optional[str] = None) -> Callable[[F], F]:
    """Decorator to mark a function as a pipeline builder."""
    def decorator(func: F) -> F:
        func._is_pipeline = True  # type: ignore
        func._pipeline_name = name or func.__name__  # type: ignore
        func._pipeline_description = description or func.__doc__  # type: ignore
        return func
    
    return decorator


def workflow(name: Optional[str] = None, description: Optional[str] = None) -> Callable[[F], F]:
    """Decorator to mark a function as a workflow builder."""
    def decorator(func: F) -> F:
        func._is_workflow = True  # type: ignore
        func._workflow_name = name or func.__name__  # type: ignore
        func._workflow_description = description or func.__doc__  # type: ignore
        return func
    
    return decorator


def retry(max_attempts: int = 3, delay: float = 1.0) -> Callable[[F], F]:
    """Decorator to add retry logic to a function."""
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Implementation here
            pass
        
        return wrapper  # type: ignore
    
    return decorator

