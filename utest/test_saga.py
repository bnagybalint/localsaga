from typing import Any
from dataclasses import dataclass

from pysaga import (
    CallableTask,
    Saga,
    SagaStatus,
)


def fails(ctx: Any) -> None:
    raise Exception()

def succeeds(ctx: Any) -> None:
    pass

@dataclass
class TaskStat:
    execute_called: bool = False
    compensate_called: bool = False

def executor(stat: TaskStat) -> None:
    def impl(ctx: Any) -> None:
        stat.execute_called = True
    return impl

def compensator(stat: TaskStat) -> None:
    def impl(ctx: Any) -> None:
        stat.compensate_called = True
    return impl

def compound(*args):
    def impl(ctx: Any):
        for fn in args:
            fn(ctx)
    return impl


def test_empty() -> None:
    saga = Saga()
    assert saga.status == SagaStatus.UNFINISHED

    saga.run()
    assert saga.status == SagaStatus.SUCCESS

def test_single() -> None:
    s1 = TaskStat()
    saga = Saga()
    saga.add_task(
        CallableTask(
            execute_action=compound(executor(s1), succeeds),
            compensate_action=compensator(s1),
        )
    )
    saga.run()

    assert saga.status == SagaStatus.SUCCESS
    assert s1.execute_called
    assert not s1.compensate_called

def test_execute_fails() -> None:
    s1 = TaskStat()
    saga = Saga()
    saga.add_task(
        CallableTask(
            execute_action=compound(executor(s1), fails),
            compensate_action=compound(compensator(s1), succeeds),
        )
    )
    saga.run()

    assert saga.status == SagaStatus.COMPENSATED
    assert s1.execute_called
    assert not s1.compensate_called, "Task compensation should only be called for successfully executed tasks"

def test_multi_success() -> None:
    s1 = TaskStat()
    s2 = TaskStat()
    saga = Saga()
    saga.add_task(
        CallableTask(
            execute_action=compound(executor(s1), succeeds),
            compensate_action=compound(compensator(s1), succeeds),
        )
    )
    saga.add_task(
        CallableTask(
            execute_action=compound(executor(s2), succeeds),
            compensate_action=compound(compensator(s2), succeeds),
        )
    )
    saga.run()

    assert saga.status == SagaStatus.SUCCESS
    assert s1.execute_called
    assert not s1.compensate_called
    assert s2.execute_called
    assert not s2.compensate_called

def test_exit_on_first_failure() -> None:
    s1 = TaskStat()
    s2 = TaskStat()
    saga = Saga()
    saga.add_task(
        CallableTask(
            execute_action=compound(executor(s1), fails),
            compensate_action=compound(compensator(s1), succeeds),
        )
    )
    saga.add_task(
        CallableTask(
            execute_action=compound(executor(s2), succeeds),
            compensate_action=compound(compensator(s2), succeeds),
        )
    )
    saga.run()

    assert saga.status == SagaStatus.COMPENSATED
    assert s1.execute_called and not s1.compensate_called
    assert not s2.execute_called and not s2.compensate_called, "Later tasks are not started"

def test_compensate_previous_tasks_on_failure() -> None:
    s1 = TaskStat()
    s2 = TaskStat()
    saga = Saga()
    saga.add_task(
        CallableTask(
            execute_action=compound(executor(s1), succeeds),
            compensate_action=compound(compensator(s1), succeeds),
        )
    )
    saga.add_task(
        CallableTask(
            execute_action=compound(executor(s2), fails),
            compensate_action=compound(compensator(s2), succeeds),
        )
    )
    saga.run()

    assert saga.status == SagaStatus.COMPENSATED
    assert s1.execute_called and s1.compensate_called, "Finished tasks are compensated if a later task fails"
    assert s2.execute_called and not s2.compensate_called, "Task compensation should only be called for successfully executed tasks"

def test_all_compensators_are_called_even_if_some_fail() -> None:
    s1 = TaskStat()
    s2 = TaskStat()
    s3 = TaskStat()
    s4 = TaskStat()
    saga = Saga()
    saga.add_task(
        CallableTask(
            execute_action=compound(executor(s1), succeeds),
            compensate_action=compound(compensator(s1), succeeds),
        )
    )
    saga.add_task(
        CallableTask(
            execute_action=compound(executor(s2), succeeds),
            compensate_action=compound(compensator(s2), fails),
        )
    )
    saga.add_task(
        CallableTask(
            execute_action=compound(executor(s3), succeeds),
            compensate_action=compound(compensator(s3), succeeds),
        )
    )
    saga.add_task(
        CallableTask(
            execute_action=compound(executor(s4), fails),
            compensate_action=compound(compensator(s4), succeeds),
        )
    )
    saga.run()

    assert saga.status == SagaStatus.FAILED
    assert s1.execute_called and s2.execute_called and s3.execute_called and s4.execute_called
    assert s2.compensate_called, "Second task should have compensated with a failure, causing a saga compensation failure"
    assert s1.compensate_called and s3.compensate_called, "Even though the compensation of the second task fails, all other tasks should be compensated"
    assert not s4.compensate_called, "Task compensation should only be called for successfully executed tasks"
