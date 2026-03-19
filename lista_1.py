from RandomNumberGenerator import RandomNumberGenerator
from dataclasses import dataclass
from collections import deque
import heapq
import copy

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

def preemptive_schrage(tasks: list[Task]) -> int:
    if not tasks:
        return 0
    
    N            : deque                  = deque(sorted(tasks, key=lambda t: t.release_time))
    G            : list[tuple[int, Task]] = []
    t            : int                    = N[0].release_time
    cmax         : int                    = 0
    current_task : Task                   = Task(task_id=-1, processing_time=0, release_time=0, delivery_time=float('inf'))
    
    while G or N:
        while N and N[0].release_time <= t:
            task = N.popleft()
            heapq.heappush(G, (-task.delivery_time, task))

        if G:
            _, task = heapq.heappop(G)
            current_task = copy.deepcopy(task)

            next_r = N[0].release_time if N else float('inf')
            finish_curr = t + current_task.processing_time
            dt = min(next_r, finish_curr) - t
            t += dt
            current_task.processing_time -= dt

            if current_task.processing_time > 0:
                heapq.heappush(G, (-current_task.delivery_time, current_task))
            else:
                cmax = max(cmax, t + task.delivery_time)
        else:
            t = N[0].release_time

    return cmax

def generate_random_tasks(n: int, Z: int) -> list[Task]:
    randGen = RandomNumberGenerator(Z)
    tasks: list[Task] = [Task(task_id=j, processing_time=randGen.nextInt(1, 29)) for j in range(1, n+1)]
    A: int = sum(task.processing_time for task in tasks)
    X: int = A
    for task in tasks:
        task.release_time = randGen.nextInt(1, A)
    for task in tasks:
        task.delivery_time = randGen.nextInt(1, X)
    
    return tasks
    
if __name__ == '__main__':
    tasks = generate_random_tasks(n=6, Z=1)
    # tasks = [
    #     Task(task_id=1, release_time=1, processing_time=2, delivery_time=5),
    #     Task(task_id=2, release_time=2, processing_time=3, delivery_time=4),
    #     Task(task_id=3, release_time=8, processing_time=1, delivery_time=6),
    #     Task(task_id=4, release_time=7, processing_time=2, delivery_time=3),
    #     Task(task_id=5, release_time=6, processing_time=3, delivery_time=7),
    #     Task(task_id=6, release_time=4, processing_time=4, delivery_time=1)
    # ]
    for t in tasks:
        print(t)
    
    og_schedule = Schedule(tasks)
    og_schedule.compute()
    og_schedule.display()

    schrage_schedule = Schedule(schrage(tasks)[0])
    schrage_schedule.compute()
    schrage_schedule.display()
    print(preemptive_schrage(tasks))
    for t in tasks:
        print(t)

    
def preemptive_schrage(tasks: list[Task]) -> tuple[list[Task], int]:
    # to be commited
    return [], 0


best_solution = [None, float('inf')]

def carlier(tasks: list[Task], UB: int) -> tuple[list[Task], int]:
    pi, U = schrage(tasks)
    
    if U < best_solution[1]:
        best_solution[0] = pi[:]
        best_solution[1] = U
    
    sched = Schedule(pi)
    sched.compute()
    
    b = -1
    for j in range(len(pi)):
        if sched.delivery_times[j] == sched.cmax:
            b = j
    
    a = -1
    for j in range(b + 1):
        p_sum = sum(pi[k].processing_time for k in range(j, b + 1))
        if sched.cmax == pi[j].release_time + p_sum + pi[b].delivery_time:
            a = j
            break
    
    if a == -1:
        return best_solution[0], best_solution[1]
    
    c = -1
    for j in range(a, b):
        if pi[j].delivery_time < pi[b].delivery_time:
            c = j
    
    if c == -1:
        return best_solution[0], best_solution[1]
    
    K = list(range(c + 1, b + 1))
    
    r_min = min(pi[j].release_time for j in K)
    q_min = min(pi[j].delivery_time for j in K)
    p_sum = sum(pi[j].processing_time for j in K)
    
    old_r = pi[c].release_time
    pi[c].release_time = max(pi[c].release_time, r_min + p_sum)
    
    _, LB = preemptive_schrage(pi)
    
    if LB < best_solution[1]:
        carlier(pi, best_solution[1])
        
    pi[c].release_time = old_r
    
    old_q = pi[c].delivery_time
    pi[c].delivery_time = max(pi[c].delivery_time, q_min + p_sum)
    
    _, LB = preemptive_schrage(pi)
    
    if LB < best_solution[1]:
        carlier(pi, best_solution[1])
        
    pi[c].delivery_time = old_q
    
    return best_solution[0], best_solution[1]