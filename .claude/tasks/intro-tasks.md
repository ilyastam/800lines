# Introducing concept of tasks
We are building a framework for AI agents. In our framework agent is defined as a system 
with desired end-state, and the goal of the agent is to achieve the end state by interacting 
with the user. I.e. by asking follow up questions, etc.

It is common for a user to give agent tasks in order to narrow down their decision as to what 
they are trying to achieve. For example, if agent is a hotel booking assistant - user may ask it 
to look for warm places in December to go, and then based on the result user can choose a country for 
hotels search. 

Therefore, we need to introduce a concept of task as another entity in the system. 

```python

enum TaskStatus:
   NOT_STARTED, IN_PROGRESS, FAILED, COMPLETED

   
class BaseTask(BaseModel):
    task: str = Field(description="description of the task received from the input")
    result: str | None = Field(description="result of the task")
    status: TaskStatus = TaskStatus.NOT_STARTED
```


agent.state.storage.base_state_storage.BaseStateStorage should store a list of tasks.
Each task should be associated with the state version when they were added. 

agent.interaction.input.base_input.BaseInput should also parse into a list of tasks.
Input can carry a list of instructions to do something as well a intent to update a state entity
based on task result, or just by what was provided in the input.

On every turn system must complete all tasks fom current version and generate output for relevant channels
based on task results and state of entities. 

