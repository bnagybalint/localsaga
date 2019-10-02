from typing import List, Tuple

from .task import Task, TaskContext

class TaskFailure:
    def __init__(self, task_index : int, task_name : str, error : Exception):
        self.task_index = task_index
        self.task_name = task_name
        self.error = error

class SagaFailed(Exception):
    def __init__(self, failure : TaskFailure, compensation_failures : List[TaskFailure]):
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

class CompensationFailed(Exception):
    def __init__(self, failures : List[TaskFailure]):
        self.failures = failures

    def __str__(self):
        return 'Failed to compensate {} tasks'.format(len(self.failures))

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
        '''
            Execute task, perform compensation if task fails with exception.
            Compensation is called on all previous tasks executed successfully.
            After compensation, a SagaFailed error is raised with detailed
            information about the root cause.
            NOTE: The task and its compensation action should be implemented
            in an atomic way (see Task for details), otherwise the Saga state
            will be inconsistent.
            NOTE: As compensation actions can also fail, the raised error
            contains information about the failed compensation actions.
        '''
        
        index = len(self.tasks)
        if name == None:
            name = '<task_{:03d}>'.format(index)
        context = TaskContext()
        taskinfo = TaskInfo(index, name, task, context)

        try:
            task.execute(context)
        except Exception as e:
            failed_list = self._compensate_tasks(self.tasks)
            raise SagaFailed(
                failure=self._create_failure(taskinfo, e),
                compensation_failures=self._create_failure_list(failed_list))

        self.tasks.append(taskinfo)

    def compensate(self):
        '''
            Compensate the Saga. Compensation is called on all previous tasks
            that were executed successfully. If compensation fails for any
            task, a CompensationFailed error is raised with detailed
            information about the failure.
        '''
        
        failed_list = self._compensate_tasks(self.tasks)
        if len(failed_list) > 0:
            raise CompensationFailed(failures=self._create_failure_list(failed_list))

    def _compensate_tasks(self, tasks : List[TaskInfo]) -> List[TaskFailure]:
        failed_list = []
        for info in self.tasks:
            try:
                info.task.compensate(info.context)
            except Exception as e:
                failed_list.append((info, e))
        return failed_list
    
    def _create_failure(self, taskinfo : TaskInfo, error : Exception) -> TaskFailure:
        return TaskFailure(taskinfo.index, taskinfo.name, error)
    def _create_failure_list(self, tasks_and_errors : List[Tuple[TaskInfo, Exception]]) -> List[TaskFailure]:
        return [self._create_failure(t,e) for t,e in tasks_and_errors]