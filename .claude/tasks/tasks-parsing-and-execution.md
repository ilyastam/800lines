UPdate agent.state.controller.base_state_controller.BaseStateController.parse_inputs
so that it works as follows:


```
for each input:
  input_context = input.content
  tasks = get_tasks(input)
  for each task in tasks:
    task_result = execute(task)
    input_context = insert_task_result_under_task(input_context)
    // parse entity state changes
```


the key is to evaluate each task at a time, and update the context with task results
and treat that as a new input for next iteration
  