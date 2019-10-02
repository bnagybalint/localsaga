from .task import Task, TaskContext

class TaskFailure:
    def __init__(self, task_index : int, task_name : str, error : Exception):
        self.task_index = task_index
        self.task_name = task_name
        self.error = error

class SagaFailed(Exception):
    def __init__(self, failure : TaskFailure, compensation_failures : list):
        self.failure = failure
        self.compensation_failures = compensation_failures

    def __str__(self):
        num_comp_failed = len(self.compensation_failures)
        if num_comp_failed == 0:
            compensation_message = 'was successful'
        else:
            compensation_message = 'failed: {} tasks failed to compensate'.format(num_comp_failed)
        return 'Task #{} ({}) failed. Compensation {}. Root cause for Saga failure: {}'.format(
            self.failure.task_index,
            self.failure.task_name,
            compensation_message,
            str(self.failure.error))

class TaskInfo:
    def __init__(self, index : int, name : str, task : Task, context : TaskContext):
        self.index = index
        self.name = name
        self.task = task
        self.context = context

class LocalSaga:
    def __init__(self):
        self.tasks = []

    def execute(self, task : Task, name : str = None):
        try:
            index = len(self.tasks)
            if name == None:
                name = '<task_{:03d}>'.format(index)
            context = TaskContext()
            taskinfo = TaskInfo(index, name, task, context)

            task.execute(context)

            self.tasks.append(taskinfo)
        except Exception as e:
            failed_list = self._compensate(self.tasks)
            raise SagaFailed(
                failure=self._create_failure(taskinfo, e),
                compensation_failures=[self._create_failure(ti,te) for ti,te in failed_list])

    def _compensate(self, tasks : list) -> list:
        failed_list = []
        for info in self.tasks:
            try:
                info.task.compensate(info.context)
            except Exception as e:
                failed_list.append((info, e))
        return failed_list
    
    def _create_failure(self, taskinfo : TaskInfo, error : Exception) -> TaskFailure:
        return TaskFailure(taskinfo.index, taskinfo.name, error)