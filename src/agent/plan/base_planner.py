from __future__ import annotations

from abc import ABC, abstractmethod

from agent.plan.plan_item import PlanItem


class BasePlanner(ABC):
    @abstractmethod
    def plan(self, input_text: str) -> list[PlanItem]:
        """Generate plan items from input text."""
        pass
