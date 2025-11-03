#!/usr/bin/env python3
"""
Script to generate JSON Schema for the Task class from state_entities.py
"""

import json
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from examples.knowledge_base.state_entities import Task
from pydantic import BaseModel
from typing import get_args

def generate_schema_with_info():
    """Generate JSON schema for Task class with additional information"""
    
    # Get the schema
    schema = Task.model_json_schema()
    
    
    # Pretty print the schema
    print("=" * 80)
    print("JSON Schema for Task class")
    print("=" * 80)
    print()
    print(json.dumps(schema, indent=2))
    
    # Show example instance
    print()
    print("=" * 80)
    print("Example Task Instance")
    print("=" * 80)
    print()
    
    # Create an example task
    example_task = Task(
        assignees=["Alice", "Bob"]
    )
    
    print("Python object:")
    print(example_task)
    print()
    print("JSON representation:")
    print(example_task.model_dump_json(indent=2))
    
    # Show the generic type parameters
    print()
    print("=" * 80)
    print("Type Information")
    print("=" * 80)
    print()
    print(f"Base class: {Task.__bases__}")
    print(f"Class definition: {Task.definition}")
    
    # Try to inspect the actual fields
    print()
    print("=" * 80)
    print("Field Information")
    print("=" * 80)
    print()
    print("Model fields:")
    for field_name, field_info in Task.model_fields.items():
        print(f"  - {field_name}: {field_info.annotation}")
    
    # Save schema to file
    schema_file = Path("task_schema.json")
    with open(schema_file, "w") as f:
        json.dump(schema, f, indent=2)
    print()
    print(f"Schema saved to: {schema_file}")
    
    return schema

if __name__ == "__main__":
    generate_schema_with_info()