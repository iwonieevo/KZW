from RandomNumberGenerator import RandomNumberGenerator
from dataclasses import dataclass
from typing import Iterator, Iterable
# https://pypi.org/project/ansicolors/
from colors import color
import math


@dataclass(frozen=True, kw_only=True, order=True)
class Operation:
    k: int
    j: int
    m: int
    p: int

    def __post_init__(self) -> None:
        if self.p <= 0:
            raise ValueError("Processing time must be positive")
    
    def __str__(self) -> str:
        return (
            "[" + color(f"[k={self.k}]", fg='red') +
            color(f"[j={self.j}]", fg='orange') +
            color(f"[m={self.m}]", fg='yellow') +
            color(f"[p={self.p}]", fg='magenta') +"]"
        )
    
@dataclass(frozen=True, kw_only=True, order=True)
class ScheduledOperation(Operation):
    start: int

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.start < 0:
            raise ValueError("Start must be non-negative")
        
    def __str__(self) -> str:
        return super().__str__() + color(f" @ Start={self.start}", fg='green')

    @classmethod 
    def from_operation(cls, operation: Operation, start: int) -> "ScheduledOperation":
        return cls(k=operation.k,j=operation.j,m=operation.m,p=operation.p,start=start)
    
    @property
    def end(self) -> int:
        return self.start + self.p
    

@dataclass(frozen=True)
class Schedule:
    scheduled_operations: tuple[ScheduledOperation, ...]

    @classmethod
    def from_operations(cls, operations: Iterable[Operation]) -> "Schedule":
        sched_ops: list[ScheduledOperation] = []
        m_ops: dict[int, ScheduledOperation] = {}
        
        for operation in operations:
            prev_m_op = m_ops.get(operation.m)
            curr_op = ScheduledOperation.from_operation(
                operation, 
                prev_m_op.end if prev_m_op else 0
            )
            m_ops[operation.m] = curr_op
            sched_ops.append(curr_op)

        return cls(scheduled_operations=tuple(sched_ops))

    def __len__(self) -> int:
        return len(self.scheduled_operations)
    
    def __iter__(self) -> Iterator[Operation]:
        return iter(self.scheduled_operations)
    
    @property
    def machines(self) -> list[int]:
        return list(set([o.m for o in self.scheduled_operations]))

    @property
    def tasks(self) -> list[int]:
        return list(set([o.j for o in self.scheduled_operations]))
    
    @property
    def c_max(self) -> int:
        return max(o.end for o in self.scheduled_operations) if self.scheduled_operations else 0

    def display(self) -> None:
        pass

def generate_random_operations(n, m, Z) -> list[Operation]:
    randGen = RandomNumberGenerator(Z)

    ret: list[Operation] = []
    p_list: list[list[int]] = [[]] * n
    m_list: list[list[int]] = [[]] * n
    o_list: list[int] = [0] * n

    for j in range(n):
        o_list[j] = randGen.nextInt(1, math.floor(m*1.2))
        for k in range(o_list[j]):
            p_list[j].append(randGen.nextInt(1,29))

    for j in range(n):
        for k in range(o_list[j]):
            m_list[j].append(randGen.nextInt(1,m))
    
    for j in range(n):
        for k in range(o_list[j]):
            ret.append(
                Operation(
                    k=k+1,
                    j=j+1,
                    m=m_list[j][k],
                    p=p_list[j][k]
                )
            )

    return ret
    

if __name__ == '__main__':
    operations = generate_random_operations(n=7, m=3, Z=1)
    for operation in operations:
        print(operation)

    operations_schedule = Schedule.from_operations(operations)
    print(operations_schedule.machines)
    print(operations_schedule.tasks)
    for scheduled_operation in operations_schedule:
        print(scheduled_operation)
    print(operations_schedule.c_max)
