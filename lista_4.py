from RandomNumberGenerator import RandomNumberGenerator
from dataclasses import dataclass
from typing import Iterator, Iterable
# https://pypi.org/project/ansicolors/
from colors import color
# https://pypi.org/project/rgb-gradient/
from rgb_gradient import get_linear_gradient
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
            "[" + color(f"[k={self.k}]", fg='#FF00A0') +
            color(f"[j={self.j}]", fg='#00FFFF') +
            color(f"[m={self.m}]", fg='#0040FF') +
            color(f"[p={self.p}]", fg='#911eb4') +"]"
        )
    
@dataclass(frozen=True, kw_only=True, order=True)
class ScheduledOperation(Operation):
    start: int

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.start < 0:
            raise ValueError("Start must be non-negative")
        
    def __str__(self) -> str:
        return super().__str__() + " @ [" + color(f"[Start={self.start}]", fg='#00FF00') + color(f"[End={self.end}]", fg='#FF8000') +"]"

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
        j_ops: dict[int, ScheduledOperation] = {}
        
        for operation in operations:
            prev_m_op = m_ops.get(operation.m)
            prev_j_op = j_ops.get(operation.j)
            curr_op = ScheduledOperation.from_operation(
                operation, 
                max(prev_m_op.end if prev_m_op else 0, prev_j_op.end if prev_j_op else 0)
            )
            m_ops[operation.m] = curr_op
            j_ops[operation.j] = curr_op
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
            if not self.scheduled_operations:
                return

            tasks = sorted(self.tasks)
            machines = sorted(self.machines)

            print()
            print(color(f" OPERATIONS BY MACHINE ".center(50, '='), bg='#a9a9a9', fg='black', style='bold'))
            for m in machines:
                ops = sorted([o for o in self.scheduled_operations if o.m == m], key=lambda x: x.start)
                
                print(color(f" MACHINE {m} ".center(30, '-'), fg='black', bg='#d3d3d3'))
                for op in ops:
                    print(op)

            print()
            print(color(f" OPERATIONS BY TASK ".center(50, '='), bg='#a9a9a9', fg='black', style='bold'))
            for t in tasks:
                ops = sorted([o for o in self.scheduled_operations if o.j == t], key=lambda x: x.start)
                
                print(color(f" TASK {t} ".center(30, '-'), fg='black', bg='#d3d3d3'))
                for op in ops:
                    print(op)
            
            print(f"\n{color(f"C_max: {self.c_max}", fg='white', bg='#e6194B', style='bold')}\n")


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
    operations = generate_random_operations(n=11, m=7, Z=1)

    print(color(f" Schedule #1: Original Task Order ".center(60, '#'), bg="#ffc800", fg='black', style='bold'))
    operations_schedule = Schedule.from_operations(operations)
    operations_schedule.display()
