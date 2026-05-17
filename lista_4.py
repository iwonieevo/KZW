from RandomNumberGenerator import RandomNumberGenerator
from dataclasses import dataclass
from collections import deque
from typing import Iterator, Iterable, Literal
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

            if prev_j_op and prev_j_op.k > curr_op.k:
                raise ValueError(f"Technological order of J{operation.j} was not maintained.")
            
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
    def jobs(self) -> list[int]:
        return list(set([o.j for o in self.scheduled_operations]))
    
    @property
    def c_max(self) -> int:
        return max(o.end for o in self.scheduled_operations) if self.scheduled_operations else 0

    def display(self, group_by: Literal['job', 'machine'] = 'machine', show_c_max: bool = True) -> None:
            if not self.scheduled_operations:
                return

            match group_by:
                case 'machine':
                    machines = sorted(self.machines)
                    print(color(f" OPERATIONS BY MACHINE ".center(50, '='), bg='#a9a9a9', fg='black', style='bold'))
                    for m in machines:
                        ops = sorted([o for o in self.scheduled_operations if o.m == m], key=lambda x: x.start)
                        
                        print(color(f" MACHINE {m} ".center(30, '-'), fg='black', bg='#d3d3d3'))
                        for op in ops:
                            print(op)
                case 'job':
                    jobs = sorted(self.jobs)
                    print(color(f" OPERATIONS BY JOB ".center(50, '='), bg='#a9a9a9', fg='black', style='bold'))
                    for t in jobs:
                        ops = sorted([o for o in self.scheduled_operations if o.j == t], key=lambda x: x.start)
                        
                        print(color(f" JOB {t} ".center(30, '-'), fg='black', bg='#d3d3d3'))
                        for op in ops:
                            print(op)
                case _:
                    return
            
            if show_c_max:
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

def insa(operations: Iterable[Operation], reinsert: Literal[None, 1, 2, 3, 4] = None) -> Schedule:
    pi_star_schedule = Schedule(())
    pi: tuple[Operation, ...] = ()
    W: deque = deque(sorted(Schedule.from_operations(tuple(operations)).jobs, key=lambda j: sum(o.p for o in operations if o.j == j), reverse=True))

    def insert_job(job: int):
        nonlocal pi_star_schedule, pi
        job_ops = tuple(sorted((o for o in operations if o.j == job), key=lambda o: o.k))
        
        pi_star_schedule = Schedule.from_operations(pi + job_ops)
        best_pi = pi + job_ops

        for i in range(len(pi)):
            new_pi = pi[:i] + job_ops + pi[i:]
            try:
                new_pi_schedule = Schedule.from_operations(new_pi)
                if new_pi_schedule.c_max < pi_star_schedule.c_max:
                    pi_star_schedule = new_pi_schedule
                    best_pi = new_pi
            except ValueError:
                continue

        pi = best_pi

    while W:
        job = W.popleft()
        insert_job(job)

        already_scheduled = set(o.j for o in pi) - {job}
        x = None

        match reinsert:
            case 1|2|3:
                raise NotImplementedError("TODO: implement missing methods")
            case 4:
                x_c_max = float('inf')
                for candidate in already_scheduled:
                    new_pi = tuple(o for o in pi if o.j != candidate)
                    try:
                        new_c_max = Schedule.from_operations(new_pi).c_max
                        if new_c_max < x_c_max:
                            x_c_max = new_c_max
                            x = candidate
                    except ValueError:
                        continue
            case _:
                continue
        
        if x is not None:
            pi = tuple(o for o in pi if o.j != x)
            insert_job(x)

    return pi_star_schedule
    

if __name__ == '__main__':
    operations = generate_random_operations(n=11, m=7, Z=1)

    print(color(f" Schedule #1: Original Operations Order ".center(70, '#'), bg="#ffc800", fg='black', style='bold'))
    operations_schedule = Schedule.from_operations(operations)
    operations_schedule.display(group_by='job', show_c_max=False)
    operations_schedule.display(group_by='machine', show_c_max=True)

    print(color(f" Schedule #2: INSA Operations Order (no reinsert) ".center(70, '#'), bg="#ffc800", fg='black', style='bold'))
    insa_schedule = insa(operations, reinsert=None)
    insa_schedule.display(group_by='machine', show_c_max=True)

    print(color(f" Schedule #3: INSA Operations Order (reinsert [4]) ".center(70, '#'), bg="#ffc800", fg='black', style='bold'))
    insa_schedule = insa(operations, reinsert=4)
    insa_schedule.display(group_by='machine', show_c_max=True)
