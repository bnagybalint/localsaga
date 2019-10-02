class TaskContext:
    pass

class Task:
    def execute(self, context : TaskContext):
        raise RuntimeError('Unimplemented')

    def compensate(self, context : TaskContext):
        raise RuntimeError('Unimplemented')

class FunctionTask(Task):
    def __init__(self, execute_fn, compensate_fn = None):
        self.execute_fn = execute_fn
        self.compensate_fn = compensate_fn

    def execute(self, context : TaskContext):
        self.execute_fn(context)

    def compensate(self, context : TaskContext):
        if self.compensate_fn:
            self.compensate_fn(context)