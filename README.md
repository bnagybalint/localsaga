# localsaga

Minimal Saga pattern implementation for local tasks

# Install

:hammer: Work in progress

# Usage

## Basic example

The Saga engine provides a 
The Saga engine will execute the configured tasks sequentially, until the saga finishes or an error is encountered.


```Python
from dataclasses import dataclass
import localsaga

@dataclass
class SharedCounter:
    value: int

class MyAdder(localsaga.Task):
    def __init__(self, counter: SharedCounter):
        self.counter = counter
    def execute(self, ctx):
        self.counter += 1
    def compensate(self, ctx):
        self.counter -= 1

counter = SharedCounter(value=42)
saga = localsaga.Saga()
saga.add_task(MyAdder(counter=counter))
saga.run()

print(counter.value) # 43
```

## Handling errors

In case a task fails, the engine will call the compensation logic for all previously successful tasks. The saga will finish and its status will be set to `compensated`.

In case any of the compensators fails, the status will be set to `failed`.

One important note here is that the failing task will not be compensated, therefore all task logic must be atomic, meaning its side-effects are either fully realized or none at all.

```Python
from dataclasses import dataclass
import localsaga

class PrinterTask(localsaga.Task):
    def execute(self, ctx):
        print("execute")
    def compensate(self, ctx):
        print("compensate")

class FailTask(localsaga.Task):
    def execute(self, ctx):
        print("fail!")
        raise Exception("AAAAAH!")
    def compensate(self, ctx):
        print("this method is not called")

saga = localsaga.Saga()
saga.add_task(PrinterTask())
saga.add_task(FailTask())
saga.run()
```

## Using task context

Task contexts are objects created by the task object before execution, with the purpose of passing data between the execute and compensate steps. This feature provides a simple way for the compensator to act on the results of the execute logic.

NOTE: While passing data in fields is also possible, it may make reusing the task object difficult or impossible. In order to reuse task objects, it is recommended to:
- store the execution state in task context
- store the data describing the task itself in data fields
See section [Reusing task objects](## Reusing task objects) for more information on this

```Python
from dataclasses import dataclass
import uuid
import localsaga

@dataclass
class MyTokenContext:
    token: str = None

class MyTokenTask(localsaga.Task):
    def execute(self, ctx: MyTokenContext):
        ctx.token = uuid.uuid4()
        print(f"Adding token {ctx.token}")

    def compensate(self, ctx: MyTokenContext):
        print(f"Removing token {ctx.token}")

    def create_context(self) -> MyTokenContext:
        return MyTokenContext()

class FailTask(localsaga.Task):
    def execute(self, ctx):
        raise Exception("Panic!")

saga = localsaga.Saga()
saga.add_task(MyTokenTask())
saga.add_task(FailTask())
saga.run()
```

## Reusing task objects

It is possible to reuse task objects in a different or the same Saga execution:

```Python
from dataclasses import dataclass
import uuid
import localsaga

@dataclass
class SummonContext:
    id: str = None

class SummonTask(localsaga.Task):
    def __init__(self, msg: str):
        self.msg = msg
    def execute(self, ctx: SummonContext):
        ctx.id = uuid.uuid4()
        print(f"{self.msg} (summon ID: {ctx.id})")
    def compensate(self, ctx: SummonContext):
        print(f"Reverting summon with ID: {ctx.id})")
    def create_context(self) -> SummonContext:
        return SummonContext()

task = SummonTask("Biggy Smalls")

saga = localsaga.Saga()
saga.add_task(task)
saga.add_task(task)
saga.add_task(task)
saga.run() # Butters is in trouble
```