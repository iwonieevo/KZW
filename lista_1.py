from RandomNumberGenerator import RandomNumberGenerator
from dataclasses import dataclass
from collections import deque
import heapq
import copy
from colors import color

@dataclass(order=True)
class Task():
    j: int = -1 # Task ID
    r: int = 0  # Release time
    p: int = 0  # Processing time
    q: int = 0  # Delivery time

    def __str__(self):
        j_str = color(f"j={self.j}", fg="magenta", style="bold")
        r_str = color(f"r={self.r}", fg="orange")
        p_str = color(f"p={self.p}", fg=(78, 220, 78)) # bright green
        q_str = color(f"q={self.q}", fg="yellow")

        return f"[ {j_str} | {r_str} | {p_str} | {q_str} ]"
    
    
class Schedule:
    def __init__(self, tasks: list[Task]):
        self.tasks            : list[Task] = tasks # J
        self.start_times      : list[int]  = []    # S
        self.completion_times : list[int]  = []    # C
        self.delivery_times   : list[int]  = []    # C + q
        self.c_max            : int        = 0     # C_max

    def __iter__(self):
        return iter(zip(self.tasks, self.start_times, self.completion_times, self.delivery_times))

    def compute(self):
        self.start_times      = []
        self.completion_times = []
        self.delivery_times   = []
        self.c_max             = 0

        for i, task in enumerate(self.tasks):
            start      : int = task.r if i == 0 else max(task.r, self.completion_times[i-1])
            completion : int = start + task.p
            delivery   : int = completion + task.q

            self.start_times.append(start)
            self.completion_times.append(completion)
            self.delivery_times.append(delivery)
            self.c_max = max(self.c_max, delivery)

    def display(self):
        col_width = len(str(self.c_max))
        label_width = 9
        frame_color = "cyan"
        hor_div = color("-"*(label_width + 1) + "+-" + "-+-".join("-" * col_width for _ in self.tasks) + "-+", fg=frame_color)
        rows = [("j",         [t.j for t in self.tasks], "magenta"),
                ("S_j",       self.start_times,          "blue"), 
                ("C_j",       self.completion_times,     "green"), 
                ("C_j + q_j", self.delivery_times,       "yellow")]
        
        print(hor_div)
        for label, row, fg_color in rows:
            label_str = color(f"{label:^{label_width}}", fg=fg_color, style="bold")
            vert_div = color(" | ", fg=frame_color)
            row_str = vert_div.join(color(f"{cell:^{col_width}}", fg=fg_color) for cell in row)
            
            print(f"{label_str}{vert_div}{row_str}{vert_div}")
            print(hor_div)
        
        print(color(f"C_max: {self.c_max}\n", fg="red", style="bold"))


def schrage(J: list[Task]) -> tuple[list[Task], int]:
    if not J:
        return [], 0

    N        : deque                  = deque(sorted(J, key=lambda t: t.r))
    G        : list[tuple[int, Task]] = []
    t        : int                    = N[0].r
    c_max    : int                    = 0
    schedule : list[Task]             = []

    while G or N:
        while N and N[0].r <= t:
            task = N.popleft()
            heapq.heappush(G, (-task.q, task))

        if G:
            _, task = heapq.heappop(G)
            schedule.append(task)

            t += task.p
            c_max = max(c_max, t + task.q)
        else:
            t = N[0].r

    return schedule, c_max

def preemptive_schrage(J: list[Task]) -> int:
    if not J:
        return 0
    
    N            : deque                  = deque(sorted(J, key=lambda t: t.r))
    G            : list[tuple[int, Task]] = []
    t            : int                    = N[0].r
    c_max        : int                    = 0
    current_task : Task                   = Task(j=-1, r=0, p=0, q=float('inf'))
    
    while G or N:
        while N and N[0].r <= t:
            task = N.popleft()
            heapq.heappush(G, (-task.q, task))

        if G:
            _, task = heapq.heappop(G)
            current_task = copy.deepcopy(task)

            next_r = N[0].r if N else float('inf')
            finish_current = t + current_task.p
            dt = min(next_r, finish_current) - t
            t += dt
            current_task.p -= dt

            if current_task.p > 0:
                heapq.heappush(G, (-current_task.q, current_task))
            else:
                c_max = max(c_max, t + current_task.q)
        else:
            t = N[0].r

    return c_max

def carlier(J: list[Task], UB: int = float('inf')) -> tuple[list[Task], int]:
    best_pi = None
    pi, U = schrage(J)

    if U < UB:
        UB = U
        best_pi = copy.deepcopy(pi)

    sched = Schedule(pi)
    sched.compute()

    b = next(j for j, (_, _, _, d) in enumerate(sched) if d == sched.c_max)
    a = next(j for j in range(b+1) if sum(t.p for t in pi[j:b+1]) + pi[j].r + pi[b].q == sched.c_max)
    c = next((j for j in range(a, b+1) if pi[j].q < pi[b].q), None)

    if c is None:
        return best_pi, UB
    
    K = pi[c:b+1]

    pi_branch = copy.deepcopy(pi)
    r_tmp = pi[c].r
    min_rK = min(t.r for t in K)
    min_qK = min(t.q for t in K)
    pi_branch[c].r = max(r_tmp, min_rK + min_qK)
    LB = preemptive_schrage(pi_branch)
    if LB < UB:
        new_pi, UB = carlier(pi_branch, UB)
        if new_pi:
            best_pi = new_pi

    pi_branch = copy.deepcopy(pi)
    q_tmp = pi_branch[c].q
    pi_branch[c].q = max(q_tmp, min_qK + sum(t.p for t in K))
    LB = preemptive_schrage(pi_branch)
    if LB < UB:
        new_pi, UB = carlier(pi_branch, UB)
        if new_pi:
            best_pi = new_pi

    return best_pi, UB

def generate_random_tasks(n: int, Z: int) -> list[Task]:
    randGen = RandomNumberGenerator(Z)
    tasks: list[Task] = [Task(j=j, p=randGen.nextInt(1, 29)) for j in range(1, n+1)]
    A: int = sum(task.p for task in tasks)
    X: int = A
    for task in tasks:
        task.r = randGen.nextInt(1, A)
    for task in tasks:
        task.q = randGen.nextInt(1, X)
    
    return tasks

def print_headline(headline: str, frame: str = "#", frame_width: int = 1, padding: int = 1, fg: str = "cyan", style: str = "underline+bold"):
    div = color(frame * (len(headline) + 2 * (frame_width + padding)), fg=fg, style="bold")
    frame = frame[0]

    middle = (
        color(frame * frame_width, fg=fg, style="bold") +
        " " * padding +
        color(headline.upper(), fg=fg, style=style) +
        " " * padding +
        color(frame * frame_width, fg=fg, style="bold")
    )
    
    # Print the framed headline
    print("\n" + div)
    print(middle)
    print(div + "\n")

        
if __name__ == '__main__':
    # Generating tasks
    tasks = generate_random_tasks(n=20, Z=1)
    print_headline("Generated tasks")
    for t in tasks:
        print(t)
    
    # Original order schedule
    og_schedule = Schedule(tasks)
    og_schedule.compute()
    print_headline("Schedule #1: Original Task Order")
    og_schedule.display()

    # Schrage non-preemptive schedule
    schrage_schedule = Schedule(schrage(tasks)[0])
    schrage_schedule.compute()
    print_headline("Schedule #2: Schrage (Non-Preemptive)")
    schrage_schedule.display()

    # Schrage preemptive C_max
    print_headline("Preemptive Schrage (C_max only)")
    print(color(f"C_max: {preemptive_schrage(tasks)}\n", fg="red", style="bold"))

    # Original tasks after preemptive shrage
    print_headline("Original tasks after preemptive shrage (unchanged)")
    for t in tasks:
        print(t)

    # Carlier schedule
    carlier_schedule = Schedule(carlier(tasks)[0])
    carlier_schedule.compute()
    print_headline("Schedule #3: Carlier")
    carlier_schedule.display()

