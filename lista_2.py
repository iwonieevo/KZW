from RandomNumberGenerator import RandomNumberGenerator
from dataclasses import dataclass
# https://pypi.org/project/ansicolors/
from colors import color

@dataclass(frozen=True, kw_only=True, order=True)
class Task:
    j: int              # Task ID
    p: list[int]        # Processing times: p[i] = time on machine i+1

    @classmethod
    def from_task(cls, task: Task, **kwargs):
        return cls(
            j=kwargs.get('j', task.j),
            p=kwargs.get('p', task.p.copy()),
        )
    
    def __copy__(self):
        return Task(j=self.j, p=self.p.copy())
    
    def __deepcopy__(self, memo):
        return Task(j=self.j, p=self.p.copy())

    def __str__(self):
        jStr = color(f"j={self.j}", fg="magenta", style="bold")
        pStrs = " | ".join(
            color(f"p{i+1}={pi}", fg="orange")
            for i, pi in enumerate(self.p)
        )
        return f"[ {jStr} | {pStrs} ]"
    
@dataclass(kw_only=True)
class TaskList:
    m: int            # Number of machines
    tasks: list[Task] # List of tasks

    def __post_init__(self):
        assert self.m > 0, "Number of machines must be a positive integer."
        
        for task in self.tasks:
            assert(len(task.p) == self.m, f"Task {task.j} has {len(task.p)} operations, expected {self.m}")

@dataclass(frozen=True)
class Schedule:
    tasks: list[Task]         # J
    __S:     list[list[int]]  # S
    __C:     list[list[int]]  # C
    __cMax:  int              # C_max

if __name__ == "__main__":
    pass

def johnson(J: TaskList):
    l = 1
    k = len(J.tasks)
    N = J.tasks.copy()
    pi = [0] * len(J.tasks)
    while N:
        i, j = min(((i, j) for i in range(N.m) for j in range(len(N))), key=lambda x: N[x[1]].p[x[0]])
        
        if N[j].p[0] < N[j].p[1]:
            pi[l] = j
            l += 1
        else:
            pi[k] = j
            k -= 1
        N.pop(j)
    
    return pi