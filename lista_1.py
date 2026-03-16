from RandomNumberGenerator import RandomNumberGenerator
from dataclasses import dataclass
from collections import deque
import heapq

@dataclass(order=True)
class Task():
    task_id         : int     # j
    processing_time : int     # p
    release_time    : int = 0 # r
    delivery_time   : int = 0 # q

    def __str__(self):
        return f"Task(j={self.task_id}, r={self.release_time}, p={self.processing_time}, q={self.delivery_time})"
    
class Schedule:
    def __init__(self, tasks: list[Task]):
        self.tasks            : list[Task] = tasks # J
        self.start_times      : list[int]  = []    # S
        self.completion_times : list[int]  = []    # C
        self.delivery_times   : list[int]  = []    # C + q
        self.cmax             : int        = 0     # Cmax

    def __iter__(self):
        return iter(self.tasks)

    def compute(self):
        self.start_times      = []
        self.completion_times = []
        self.delivery_times   = []
        self.cmax             = 0

        for i, task in enumerate(self.tasks):
            start      : int = task.release_time if i == 0 else max(task.release_time, self.completion_times[i-1])
            completion : int = start + task.processing_time
            delivery   : int = completion + task.delivery_time

            self.start_times.append(start)
            self.completion_times.append(completion)
            self.delivery_times.append(delivery)
            self.cmax = max(self.cmax, delivery)

    def display(self):
        rows = [
            ["j"]         + [str(t.task_id) for t    in self.tasks],
            ["S_j"]       + [str(s_i)       for s_i  in self.start_times],
            ["C_j"]       + [str(c_i)       for c_i  in self.completion_times],
            ["C_j + q_j"] + [str(cq_i)      for cq_i in self.delivery_times]
        ]

        col_width = max(len(cell) for row in rows for cell in row)
        separator = "-+-".join("-" * col_width for _ in rows[0])

        for row in rows:
            print(" | ".join(f"{cell:>{col_width}}" for cell in row))
            print(separator)
        
        print(f"Cmax: {self.cmax}\n")

def schrage(tasks: list[Task]) -> tuple[list[Task], int]:
    if not tasks:
        return [], 0

    N        : deque                  = deque(sorted(tasks, key=lambda t: t.release_time))
    G        : list[tuple[int, Task]] = []
    t        : int                    = N[0].release_time
    cmax     : int                    = 0
    schedule : list[Task]             = []

    while G or N:
        while N and N[0].release_time <= t:
            task = N.popleft()
            heapq.heappush(G, (-task.delivery_time, task))

        if G:
            _, task = heapq.heappop(G)
            schedule.append(task)

            t += task.processing_time
            cmax = max(cmax, t + task.delivery_time)
        else:
            t = N[0].release_time

    return schedule, cmax

def generate_random_tasks(n: int, Z: int) -> list[Task]:
    randGen = RandomNumberGenerator(Z)
    tasks: list[Task] = [Task(task_id=j, processing_time=randGen.nextInt(1, 29)) for j in range(1, n+1)]
    A: int = sum(task.processing_time for task in tasks)
    X: int = 29
    for task in tasks:
        task.release_time = randGen.nextInt(1, A)
    for task in tasks:
        task.delivery_time = randGen.nextInt(1, X)
    
    return tasks
    
if __name__ == '__main__':
    tasks = generate_random_tasks(n=10, Z=1)

    for t in tasks:
        print(t)
    
    og_schedule = Schedule(tasks)
    og_schedule.compute()
    og_schedule.display()

    schrage_schedule = Schedule(schrage(tasks)[0])
    schrage_schedule.compute()
    schrage_schedule.display()

    