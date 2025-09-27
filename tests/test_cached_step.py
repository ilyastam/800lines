
import unittest
from workflow.durable_workflow import DurableWorkflow
from unittest.mock import patch
from workflow.durable_workflow import DurableWorkflow, cached_step, InputRequested, WorkflowStatus


class TestCachedStep(unittest.TestCase):

    def test_no_args(self):
        step_response = "response"
        class TestWorkflow(DurableWorkflow):
            def __init__(self, name=None, state_prefix=None, state=None):
                super().__init__(name=name, state_prefix=state_prefix, state=state)
                self.step_invocations = 0

            @cached_step
            def step(self):
                self.step_invocations += 1 
                return step_response                

        test_workflow = TestWorkflow(name='testwf')   
        self.assertEqual(test_workflow.step(), step_response)
        self.assertEqual(test_workflow.step_invocations, 1)

        self.assertEqual(test_workflow.step(), step_response)
        self.assertEqual(test_workflow.step_invocations, 1)

    def test_with_args(self):
        step_response = "response"
        class TestWorkflow(DurableWorkflow):
            def __init__(self, name=None, state_prefix=None, state=None):
                super().__init__(name=name, state_prefix=state_prefix, state=state)
                self.step_invocations = 0

            @cached_step
            def step(self, arg1=None):
                self.step_invocations += 1 
                return step_response                

        test_workflow = TestWorkflow(name='testwf')   
        self.assertEqual(test_workflow.step(), step_response)
        self.assertEqual(test_workflow.step_invocations, 1)

        self.assertEqual(test_workflow.step(), step_response)
        self.assertEqual(test_workflow.step_invocations, 1)

        self.assertEqual(test_workflow.step("xyz"), step_response)
        self.assertEqual(test_workflow.step_invocations, 2)

        self.assertEqual(test_workflow.step("xyz"), step_response)
        self.assertEqual(test_workflow.step_invocations, 2)

    def test_with_args_in_annotation(self):
        class TestWorkflow(DurableWorkflow):
            def __init__(self, name=None, state_prefix=None, state=None):
                super().__init__(name=name, state_prefix=state_prefix, state=state)
                self.step_invocations = 0

            @cached_step({'arg1'})
            def step(self, arg1, arg2=None):
                self.step_invocations += 1 
                return arg2 or arg1                

        test_workflow = TestWorkflow(name='testwf')   

        self.assertEqual(test_workflow.step("xyz"), "xyz")
        self.assertEqual(test_workflow.step_invocations, 1)

        self.assertEqual(test_workflow.step("xyz"), "xyz")
        self.assertEqual(test_workflow.step_invocations, 1)

        self.assertEqual(test_workflow.step("xyz1", arg2="another arg"), "another arg")
        self.assertEqual(test_workflow.step_invocations, 2)

        self.assertEqual(test_workflow.step("xyz1", arg2="another arg but will be ignored because arg2 is not a cache arg"), "another arg")
        self.assertEqual(test_workflow.step_invocations, 2)


            
            

