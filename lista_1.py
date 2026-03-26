from RandomNumberGenerator import RandomNumberGenerator
from dataclasses import dataclass
from collections import deque
import heapq
# https://pypi.org/project/ansicolors/
from colors import color

@dataclass(order=True, frozen=True, kw_only=True)
class Task():
    j: int = -1 # Task ID
    r: int = 0  # Release time
    p: int = 0  # Processing time
    q: int = 0  # Delivery time

    @classmethod
    def from_task(cls, task: Task, **kwargs):
        return cls(
            j=kwargs.get('j', task.j),
            r=kwargs.get('r', task.r),
            p=kwargs.get('p', task.p),
            q=kwargs.get('q', task.q)
        )

    def __copy__(self):
        return Task(j=self.j, r=self.r, p=self.p, q=self.q)
    
    def __deepcopy__(self, memo):
        return Task(j=self.j, r=self.r, p=self.p, q=self.q)

    def __str__(self):
        jStr = color(f"j={self.j}", fg="magenta", style="bold")
        rStr = color(f"r={self.r}", fg="orange")
        pStr = color(f"p={self.p}", fg=(78, 220, 78)) # bright green
        qStr = color(f"q={self.q}", fg="yellow")

        return f"[ {jStr} | {rStr} | {pStr} | {qStr} ]"
    
    
class Schedule:
    def __init__(self, tasks: list[Task]):
        self.__tasks           : list[Task] = tasks # J
        self.__startTimes      : list[int]  = []    # S
        self.__completionTimes : list[int]  = []    # C
        self.__deliveryTimes   : list[int]  = []    # C + q
        self.__cMax            : int        = 0     # C_max
        self.__compute()

    def __iter__(self):
        return iter(zip(self.tasks, self.startTimes, self.completionTimes, self.deliveryTimes))

    def __compute(self):
        for i, task in enumerate(self.tasks):
            start      : int = task.r if i == 0 else max(task.r, self.completionTimes[i-1])
            completion : int = start + task.p
            delivery   : int = completion + task.q

            self.__startTimes.append(start)
            self.__completionTimes.append(completion)
            self.__deliveryTimes.append(delivery)
            self.__cMax = max(self.cMax, delivery)

    @property
    def tasks(self):
        return self.__tasks
    
    @property
    def startTimes(self):
        return self.__startTimes
    
    @property
    def completionTimes(self):
        return self.__completionTimes
    
    @property
    def deliveryTimes(self):
        return self.__deliveryTimes
    
    @property
    def cMax(self):
        return self.__cMax

    def display(self):
        colWidth = len(str(self.cMax))
        labelWidth = 9
        frameColor = "cyan"
        horDiv = color("-"*(labelWidth + 1) + "+-" + "-+-".join("-" * colWidth for _ in self.tasks) + "-+", fg=frameColor)
        rows = [("j",         [t.j for t in self.tasks], "magenta"),
                ("S_j",       self.startTimes,           "blue"), 
                ("C_j",       self.completionTimes,      "green"), 
                ("C_j + q_j", self.deliveryTimes,        "yellow")]
        
        print(horDiv)
        for label, row, fgColor in rows:
            labelStr = color(f"{label:^{labelWidth}}", fg=fgColor, style="bold")
            vertDiv = color(" | ", fg=frameColor)
            rowStr = vertDiv.join(color(f"{cell:^{colWidth}}", fg=fgColor) for cell in row)
            
            print(f"{labelStr}{vertDiv}{rowStr}{vertDiv}")
            print(horDiv)
        
        print(color(f"C_max: {self.cMax}\n", fg="red", style="bold"))


def schrage(J: list[Task]) -> tuple[list[Task], int]:
    if not J:
        return [], 0

    N        : deque                  = deque(sorted(J, key=lambda t: t.r))
    G        : list[tuple[int, Task]] = []
    t        : int                    = N[0].r
    cMax     : int                    = 0
    pi       : list[Task]             = []

    while G or N:
        while N and N[0].r <= t:
            task = N.popleft()
            heapq.heappush(G, (-task.q, task))

        if G:
            _, task = heapq.heappop(G)
            pi.append(task)

            t += task.p
            cMax = max(cMax, t + task.q)
        else:
            t = N[0].r

    return pi, cMax

def preemptive_schrage(J: list[Task]) -> int:
    if not J:
        return 0
    
    N            : deque                  = deque(sorted(J, key=lambda t: t.r))
    G            : list[tuple[int, Task]] = []
    t            : int                    = N[0].r
    cMax         : int                    = 0
    
    while G or N:
        while N and N[0].r <= t:
            task = N.popleft()
            heapq.heappush(G, (-task.q, task))

        if G:
            _, task = heapq.heappop(G)
            
            dt = min(N[0].r, t + task.p) - t if N else task.p
            t += dt
            timeLeft = task.p - dt

            if timeLeft > 0:
                heapq.heappush(G, (-task.q, Task.from_task(task, p=timeLeft)))
            else:
                cMax = max(cMax, t + task.q)
        else:
            t = N[0].r

    return cMax

def carlier(J: list[Task], UB: int = float('inf')) -> tuple[list[Task], int]:
    piStar = None
    pi, U = schrage(J)

    if U < UB:
        UB = U
        piStar = pi.copy()

    b = max(j for j, (_, _, _, d) in enumerate(Schedule(pi)) if d == U)
    a = next(j for j in range(b+1) if sum(t.p for t in pi[j:b+1]) + pi[j].r + pi[b].q == U)
    c = next((j for j in range(b-1, a-1, -1) if pi[j].q < pi[b].q), None)

    if c is None:
        return piStar, UB
    
    K = pi[c:b+1]
    minQK = min(t.q for t in K)

    piBranch = pi.copy()
    idx = c # index of the altered task
    def branch(task: Task):
        nonlocal idx, piBranch, UB, piStar
        piBranch[idx] = task
        if preemptive_schrage(piBranch) < UB:
            piNew, _ = carlier(piBranch, UB)
            if piNew:
                idx = next(i for i, t in enumerate(piNew) if t.j == pi[c].j)
                piNew[idx] = pi[c]
                piNewCMax = Schedule(piNew).cMax
                if piNewCMax < UB:
                    UB = piNewCMax
                    piStar = piNew.copy()
                piBranch = piNew.copy()
            else:
                piBranch[idx] = pi[c]
            

    branch(Task.from_task(pi[c], r=max(pi[c].r, min(t.r for t in K) + minQK)))
    branch(Task.from_task(pi[c], q=max(pi[c].q, minQK + sum(t.p for t in K))))

    return piStar, UB

def generate_random_tasks(n: int, Z: int) -> list[Task]:
    randGen = RandomNumberGenerator(Z)
    pList = [randGen.nextInt(1, 29) for _ in range(n)]
    A: int = sum(pList)
    X: int = A
    rList = [randGen.nextInt(1, A) for _ in range(n)]
    return [Task(j=i+1, r=rList[i], p=pList[i], q=randGen.nextInt(1, X)) for i in range(n)]

def print_headline(headline: str, frame: str = "#", frameWidth: int = 1, padding: int = 1, fgColor: str = "cyan", headlineStyle: str = "underline+bold"):
    div = color(frame * (len(headline) + 2 * (frameWidth + padding)), fg=fgColor, style="bold")
    frame = frame[0]

    middle = (
        color(frame * frameWidth, fg=fgColor, style="bold") +
        " " * padding +
        color(headline.upper(), fg=fgColor, style=headlineStyle) +
        " " * padding +
        color(frame * frameWidth, fg=fgColor, style="bold")
    )
    
    # Print the framed headline
    print("\n" + div)
    print(middle)
    print(div + "\n")

        
if __name__ == '__main__':
    # Generating tasks
    tasks = generate_random_tasks(n=6, Z=1)
    print_headline("Generated tasks")
    tasks.sort()
    for t in tasks:
        print(t)
    
    # Original order schedule
    scheduleOriginal = Schedule(tasks)
    print_headline("Schedule #1: Original Task Order")
    scheduleOriginal.display()

    # Schrage non-preemptive schedule
    scheduleSchrage = Schedule(schrage(tasks)[0])
    print_headline("Schedule #2: Schrage (Non-Preemptive)")
    scheduleSchrage.display()

    # Schrage preemptive C_max
    print_headline("Preemptive Schrage (C_max only)")
    print(color(f"C_max: {preemptive_schrage(tasks)}\n", fg="red", style="bold"))

    # Carlier schedule
    scheduleCarlier = Schedule(carlier(tasks)[0])
    print_headline("Schedule #3: Carlier")
    scheduleCarlier.display()

    # Sanity check: are the tasks the same tasks or are they modified?
    sortedCarlierTasks = sorted(scheduleCarlier.tasks)
    print_headline("Carlier sanity check")
    for i in range(len(tasks)):
        bgColor = "red" if tasks[i] != sortedCarlierTasks[i] else "green"
        print(color(f"Task #{i+1}", style="underline+bold"))
        print(color("Original task: ", fg="white", bg=bgColor, style="bold"), tasks[i])
        print(color("Carlier task: ", fg="white", bg=bgColor, style="bold"), sortedCarlierTasks[i])

