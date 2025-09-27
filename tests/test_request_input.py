
import unittest
from workflow.durable_workflow import DurableWorkflow
from unittest.mock import patch
from workflow.durable_workflow import DurableWorkflow, cached_step, InputRequested, WorkflowStatus


class TestRequestInput(unittest.TestCase):

    def test_request_input_base_case(self):
        request_input_prompt = "request input"
        class TestWorkflow(DurableWorkflow):
            def run(self):
                self.request_input("request input")

        test_workflow = TestWorkflow(name='testwf')   

        with patch.object(test_workflow, "request_input", wraps=test_workflow.request_input) as spy_request_input:
            try:
                test_workflow.run()
            except InputRequested as e:
                self.assertEqual(test_workflow.get_status(), WorkflowStatus.WAITING_FOR_INPUT)
                self.assertFalse(test_workflow.is_running)
                self.assertEqual(e.user_prompt, request_input_prompt)
                test_workflow.set_input("input")
                self.assertEqual(test_workflow.get_status(), WorkflowStatus.INPUT_SET_BUT_NOT_CONSUMED)
                self.assertTrue(test_workflow.is_running)
                self.assertEqual(spy_request_input.call_count, 1)

            test_workflow.run()
            self.assertEqual(test_workflow.get_status(), WorkflowStatus.RUNNING)
            self.assertEqual(spy_request_input.call_count, 2)

            
            

