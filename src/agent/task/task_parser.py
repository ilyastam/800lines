from __future__ import annotations

from openai import OpenAI
from pydantic import BaseModel, Field

from agent.task.base_task import BaseTask


class LlmTaskList(BaseModel):
    """LLM response format for task-only parsing."""
    tasks: list[str] = Field(
        default_factory=list,
        description="List of tasks the user wants the agent to perform"
    )


class TaskParser:
    def __init__(self, client: OpenAI | None = None):
        self.client: OpenAI = client or OpenAI()

    def parse_tasks(self, input_text: str) -> list[BaseTask]:
        system_prompt = """Extract any tasks or actions the user wants performed.
A task is something the user wants the agent to DO (search, find, look up, calculate, etc).

Only extract explicit action requests. Do not infer tasks from statements.
If there are no tasks, return an empty list."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text},
        ]

        completion = self.client.chat.completions.parse(
            model="gpt-4o",
            messages=messages,
            response_format=LlmTaskList,
            temperature=0.0
        )

        llm_response: LlmTaskList = completion.choices[0].message.parsed

        return [BaseTask(task=task_str) for task_str in llm_response.tasks]
