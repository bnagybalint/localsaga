import enum

from dataclasses import dataclass
from typing import List

from localsaga.task import Task, TaskContext


class SagaStatus(enum.Enum):
    """ Status of a Saga engine

        UNFINISHED: saga has not been started or has not run to completion
        SUCCESS: saga exited successfully
        COMPENSATED: saga encountered a task failure, but was able to compensate all tasks properly
        FAILED: saga encountered a task failure, and was unable to compensate some tasks properly
    """
    UNFINISHED = "unfinished"
    SUCCESS = "success"
    COMPENSATED = "compensated"
    FAILED = "failed"

@dataclass
class TaskStatus:
    execute_called: bool = False
    compensate_called: bool = False
    error: Exception = None

@dataclass
class TaskInfo:
    index: int
    name: int
    task: Task
    context: TaskContext
    status: TaskStatus

class Saga:
    def __init__(self) -> None:
        self.task_infos: List[TaskInfo] = []
        self.status: SagaStatus = SagaStatus.UNFINISHED

    def add_task(self, task: Task) -> None:
        """ Configures a task to be executed as part of the saga

        Parameters
        ----------
        task : Task
            The task to add

        Raises
        ------
        RuntimeError
            In case the task context creation was unsuccessful
        """
        index = len(self.task_infos)
        name = f"Task #{index:03d} ({type(task)})"
        try:
            task_context = task.create_context()
        except Exception as e:
            raise RuntimeError(f"Failed to create task context: {e}") from e

        self.task_infos.append(
            TaskInfo(
                index=index,
                name=name,
                task=task,
                context=task_context,
                status=TaskStatus()
            )
        )

    def run(self) -> None:
        """ Executes the saga.

        Executes the task logic for the configured tasks until the saga finishes or and error
        is encountered in one of the tasks.
        
        In case of an error, the compensation logic is executed on all successfully finished tasks.
        """
        finished: List[TaskInfo] = []
        for ti in self.task_infos:
            try:
                ti.status.execute_called = True
                ti.task.execute(ti.context)
                finished.append(ti)
            except Exception as e:
                ti.status.error = e
                break
        
        if len(finished) == len(self.task_infos):
            self.status = SagaStatus.SUCCESS
            return 

        # compensation
        self.status = SagaStatus.COMPENSATED
        for ti in reversed(finished):
            try:
                ti.status.compensate_called = True
                ti.task.compensate(ti.context)
            except Exception as e:
                ti.status.error = e
                self.status = SagaStatus.FAILED
            