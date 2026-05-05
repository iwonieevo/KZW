from RandomNumberGenerator import RandomNumberGenerator
from typing import Iterator
from dataclasses import dataclass
# https://pypi.org/project/ansicolors/
from colors import color
from itertools import permutations
import time


@dataclass(frozen=True, kw_only=True, order=True)
class Task:
    j: int
    p: int
    w: int
    d: int

    @classmethod
    def from_task(cls, task: Task, **kwargs) -> Task:
        return cls(
            j=kwargs.get('j', task.j), 
            p=kwargs.get('p', task.p), 
            w=kwargs.get('w', task.w), 
            d=kwargs.get('d', task.d)
            )
    
    def __str__(self) -> str:
        jStr = color(f"j={self.j}", fg="magenta", style="bold")
        pStr = color(f"p={self.p}", fg="orange")
        wStr = color(f"w={self.w}", fg=(78, 220, 78)) # bright green
        dStr = color(f"d={self.d}", fg="yellow")

        return f"[ {jStr} | {pStr} | {wStr} | {dStr} ]"
    

@dataclass
class Schedule:
    pi: list[Task]

    def __post_init__(self) -> None:
        self.__compute()

    def __setattr__(self, name, value) -> None:
        super().__setattr__(name, value)
        if name == 'pi' and hasattr(self, '_Schedule__F'):  
            self.__compute()

    def __iter__(self) -> Iterator[tuple[Task, int]]:
        return iter(zip(self.pi, self.T))
    
    def __compute(self) -> None:
        self.__C: list[int] = [0] * len(self.pi)
        self.__T: list[int] = [0] * len(self.pi)
        self.__F: int       = 0
        

        for i, task in enumerate(self.pi):
            completion : int = task.p if i == 0 else self.__C[i-1] + task.p
            tardiness  : int = max(completion - task.d, 0)

            self.__C[i] = completion
            self.__T[i] = tardiness

            self.__F += tardiness * task.w

    def display(self) -> None:
        # Calculate weighted tardiness for each task
        weighted_tardiness = [task.w * self.T[i] for i, task in enumerate(self.pi)]
        
        # Calculate cell width based on max value in any cell
        all_values = ([t.j for t in self.pi] + [t.p for t in self.pi] + 
                    [t.w for t in self.pi] + [t.d for t in self.pi] +
                    self.C + self.T + weighted_tardiness)
        cellWidth = max(4, max(len(str(v)) for v in all_values) + 1)
        
        separator = color(" | ", fg="cyan")
        div = color("-+-".join(["-"*cellWidth for _ in range(7)]), fg="cyan")
        
        # Header row
        headers = ["j", "p", "w", "d", "C", "T", "w*T"]
        print(separator.join(
            color(f"{header:^{cellWidth}}", fg="cyan", style="bold")
            for header in headers
        ))
        print(div)
        
        # Rows for each task
        for i, task in enumerate(self.pi):
            wT = task.w * self.T[i]
            row = [task.j, task.p, task.w, task.d, self.C[i], self.T[i], wT]
            colors_for_cols = ["magenta", "orange", (78, 220, 78), "yellow", "green", "red", "white"]
            
            print(separator.join(
                color(f"{str(val):^{cellWidth}}", fg=col)
                for val, col in zip(row, colors_for_cols)
            ))
            print(div)
        
        print(color(f"F (Total Weighted Tardiness): {self.F}\n", fg="red", style="bold"))

    @property
    def C(self) -> list[int]:
        return self.__C
    
    @property
    def T(self) -> list[int]:
        return self.__T
    
    @property
    def F(self) -> int:
        return self.__F
    

def bruteforce(sched: Schedule) -> Schedule:
    perms = [p for p in permutations(sched.pi)]
    best_pi = min(perms, key=lambda p: Schedule(list(p)).F)
    return Schedule(list(best_pi))

def greedy(sched: Schedule) -> Schedule:
    sorted_tasks = sorted(sched.pi, key=lambda t: t.d)
    return Schedule(sorted_tasks)

def dynamic_programming(sched: Schedule) -> Schedule:
    tasks = sched.pi
    n = len(tasks)

    # memory[D] = minimal weighted sum of tardiness for subset D
    # choice[D] = index of task chosen as the last in subset D
    memory: list[int|float] = [0]  * (1 << n)
    choice: list[int] = [-1] * (1 << n)

    for D in range(1, 1 << n):
        # D & (1 << j) - is task j in subset D
        sum_p: int = sum(tasks[j].p for j in range(n) if D & (1 << j))
        memory[D] = float('inf')

        for j in range(n):
            if not (D & (1 << j)):
                continue
            
            # D ^ (1 << j) - subset D without task j
            cost: int = max(sum_p - tasks[j].d, 0) * tasks[j].w + int(memory[D ^ (1 << j)])

            if cost < memory[D]:
                memory[D] = cost
                choice[D] = j

    # Backtracking: recreating the task order
    order: list[Task] = []
    D = (1 << n) - 1

    while D > 0:
        j = choice[D]
        order.append(tasks[j])
        D ^= (1 << j)

    order.reverse()

    return Schedule(order)
 
def generate_random_tasks(n: int, Z: int) -> list[Task]:
    randGen = RandomNumberGenerator(Z)
    pList = [randGen.nextInt(1, 29) for _ in range(n)]
    wList = [randGen.nextInt(1, 9) for _ in range(n)]
    X = 29 # sum(pList)
    return [Task(j=i+1, p=pList[i], w=wList[i], d=randGen.nextInt(1, X)) for i in range(n)]

def print_headline(headline: str, frame: str = "#", frameWidth: int = 1, padding: int = 1, fgColor: str = "cyan", headlineStyle: str = "underline+bold") -> None:
    div = color(frame * (len(headline) + 2 * (frameWidth + padding)), fg=fgColor, style="bold")
    frame = frame[0]

    middle = (
        color(frame * frameWidth, fg=fgColor, style="bold") +
        " " * padding +
        color(headline.upper(), fg=fgColor, style=headlineStyle) +
        " " * padding +
        color(frame * frameWidth, fg=fgColor, style="bold")
    )

    print(f"\n{div}",
          f"\n{middle}",
          f"\n{div}\n")
    

if __name__ == '__main__':
    tasks = generate_random_tasks(n=9, Z=1)

    print_headline("Generated tasks")
    for t in tasks:
        print(t)

    print_headline("Schedule #1: Original Task Order")
    scheduleOriginal = Schedule(tasks)
    scheduleOriginal.display()

    print_headline("Schedule #2: Bruteforce")
    startTime = time.perf_counter()
    scheduleBruteforce = bruteforce(scheduleOriginal)
    duration = time.perf_counter() - startTime
    scheduleBruteforce.display()
    print(color(f"{duration=}s", fg="white", bg="red", style="underline+bold"))

    print_headline("Schedule #3: Greedy")
    startTime = time.perf_counter()
    scheduleGreedy = greedy(scheduleOriginal)
    duration = time.perf_counter() - startTime
    scheduleGreedy.display()
    print(color(f"{duration=}s", fg="white", bg="red", style="underline+bold"))

    print_headline("Schedule #4: Dynamic programming")
    startTime = time.perf_counter()
    scheduleDynamic = dynamic_programming(scheduleOriginal)
    duration = time.perf_counter() - startTime
    scheduleDynamic.display()
    print(color(f"{duration=}s", fg="white", bg="red", style="underline+bold"))