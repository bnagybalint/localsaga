from typing import Callable

class TaskContext:
    pass

class Task:
    '''
        Represents a single task to be executed in the context of a Saga.
        Both 'execute' and 'compensate' should be implemented in an atomic way,
        meaning that their side-effects are either fully carried out or
        not at all. Failure to do so can leave the Saga in an inconsistent
        state, non-atomic tasks can cause errors during compensation actions

        The execute action can send values to the compensate action via the
        context object that is passed to both of these actions. The context
        object is unique to the task call.
    '''

    def execute(self, context : TaskContext):
        raise RuntimeError('Unimplemented')
    def compensate(self, context : TaskContext):
        raise RuntimeError('Unimplemented')

class CallableTask(Task):
    '''
        Task defined by two callable actions: one for execute and one for compensate.
    '''
    
    def __init__(self, execute_action : Callable, compensate_action : Callable = None):
        self.execute_action = execute_action
        self.compensate_action = compensate_action

    def execute(self, context : TaskContext):
        self.execute_action(context)

    def compensate(self, context : TaskContext):
        if self.compensate_action:
            self.compensate_action(context)