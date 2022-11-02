from typing import Any, Callable


TaskContext = Any

ExecuteCallback = Callable[[TaskContext], None]
CompansateCallback = Callable[[TaskContext], None]


class Task:
    """ Interface for task objects, that represents a single task to be executed in the context of a Saga. """

    def execute(self, context: TaskContext) -> None:
        """ Executes the task logic.

        Should be implemented in an atomic way, meaning that this method's side-effects
        are either fully carried out or not at all. Failure to do so can leave the Saga
        in an inconsistent state, non-atomic tasks can cause errors during compensation
        actions.

        Parameters
        ----------
        context : TaskContext
            Context object that is created by the Saga engine, which can be used to pass
            information between execute and compensate steps.
        """
        raise NotImplementedError()

    def compensate(self, context : TaskContext) -> None:
        """ Executes the compensation logic for the task.

        Compensation logic should restore the state of system as if the execute was never
        called. 

        This method is only called by the Saga engine if the task executes successfully but
        some later task fails, causing a Saga compensation.

        Should be implemented in an atomic way, meaning that this method's side-effects
        are either fully carried out or not at all. Failure to do so can leave the Saga
        in an inconsistent state, non-atomic tasks can cause errors during compensation
        actions.

        Parameters
        ----------
        context : TaskContext
            Context object that is created by the Saga engine, which can be used to pass
            information between execute and compensate steps.
        """
        raise NotImplementedError()

    def create_context(self) -> TaskContext:
        """ Create a context object that can be used to pass data between execution and
        compensation steps.

        This method is called by the Saga engine before executing the task. Task implementations
        can override this method to customize the type and value of the context object.

        A unique object should be returned for each invocation as it will represent the context
        of a single execution of this task (task objects may be reused multiple times in the same Saga).
        
        By default, this method returns None, meaning that the Saga will not have a context.

        Returns
        -------
        TaskContext
            The task context to use when executing/compensating this task.
        """
        return None

class CallableTask(Task):
    """ Task defined by two callable actions: one for execute and one for compensate.
    """
    
    def __init__(self, execute_action: ExecuteCallback, compensate_action: CompansateCallback = None):
        self.execute_action = execute_action
        self.compensate_action = compensate_action

    def execute(self, context: TaskContext):
        self.execute_action(context)

    def compensate(self, context: TaskContext):
        if self.compensate_action:
            self.compensate_action(context)