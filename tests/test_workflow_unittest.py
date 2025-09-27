import os
import sys
import unittest
from unittest.mock import patch

from workflow.durable_workflow import DurableWorkflow, cached_step, InputRequested

# Ensure the 'src' directory is on sys.path so we can import the package without installation
THIS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


class DummyWorkflow(DurableWorkflow):
    def get_expected_user_prompts_count(self) -> int:
        return 0

    def run(self):
        self.step_echo()
        self.step_echo()
        self.complete_workflow()

    
    @cached_step
    def step_echo(self, message: str = "") -> str:
        print("Running step echo")
        self.request_input("message")
        self.echo_calls = getattr(self, "echo_calls", 0) + 1
        return "my echo step"


class TestWorkflowUnittest(unittest.TestCase):
    def setUp(self):
        self.workflow = DummyWorkflow(name="test-workflow")
        self.workflow.echo_calls = 0
        
    def test_initialization(self):
        self.assertEqual(self.workflow.name, "test-workflow")

        while self.workflow.is_running:
            try:
                self.workflow.run()
            except InputRequested as e:
                print(e.user_prompt)    
                self.workflow.set_input("Response")

        # Verify the actual step body executed exactly once
        self.assertEqual(self.workflow.echo_calls, 1)




if __name__ == "__main__":
    # Allow running this file directly: python -m unittest tests/test_workflow_unittest.py
    unittest.main()