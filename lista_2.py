from RandomNumberGenerator import RandomNumberGenerator
from dataclasses import dataclass
# https://pypi.org/project/ansicolors/
from colors import color

@dataclass(frozen=True, kw_only=True, order=True)
class Task:
    j: int
    p: tuple[int, ...]

    @classmethod
    def from_task(cls, task: Task, **kwargs):
        return cls(
            j=kwargs.get('j', task.j),
            p=kwargs.get('p', task.p),
        )
    
    @property
    def m(self):
        return len(self.p)

@dataclass(frozen=True, kw_only=True)
class TaskList:
    m     : int
    tasks : list[Task]

    def __post_init__(self):
        assert self.m > 0, "Number of machines must be a positive integer."
        
        object.__setattr__(self, 'tasks', [Task.from_task(t, p=t.p[:self.m] + (0,)*(self.m - t.m)) for t in self.tasks])

    def __iter__(self):
        return iter(self.tasks)
    
    def __len__(self):
        return len(self.tasks)
    
    def display(self):
        headers = ["j"] + [f"p_{i+1}" for i in range(self.m)]
        columns = [[t.j for t in self.tasks]] + [[t.p[i] for t in self.tasks] for i in range(self.m)]
        widths = [max(len(label), max(len(str(v)) for v in vals)) for label, vals in zip(headers, columns)]
        separator = color(" | ", fg="cyan")

        print(color(f"m={self.m}, n={len(self)}", fg="green", style="bold"))
        print(separator.join(
            color(f"{header:^{width}}", fg="magenta" if i == 0 else "red", style="bold")
            for i, (header, width) in enumerate(zip(headers, widths))
        ))
        print(color("-+-".join("-" * w for w in widths), fg="cyan"))
        for row in zip(*columns):
            print(separator.join(
                color(f"{value:^{width}}", fg="pink" if i == 0 else "orange")
                for i, (value, width) in enumerate(zip(row, widths))
            ))
        
@dataclass
class Schedule:
    taskList: TaskList

    def __post_init__(self):
        self.__compute()

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name == "taskList":  
            self.__compute()

    def __iter__(self):
        return iter(zip(self.taskList, zip(*self.startTimes), zip(*self.completionTimes)))
    
    def __compute(self):
        self.__startTimes      = [[0]*len(self.taskList) for _ in range(self.taskList.m)]
        self.__completionTimes = [[0]*len(self.taskList) for _ in range(self.taskList.m)]
        
        for j, task in enumerate(self.taskList):
            for i, p_i in enumerate(task.p):
                self.__startTimes[i][j] = max(
                    self.__completionTimes[i-1][j] if i > 0 else 0,
                    self.__completionTimes[i][j-1] if j > 0 else 0
                )
                self.__completionTimes[i][j] = self.__startTimes[i][j] + p_i
        
        self.__cMax = self.__completionTimes[-1][-1]

    @property
    def startTimes(self):
        return self.__startTimes
    
    @property
    def completionTimes(self):
        return self.__completionTimes
    
    @property
    def cMax(self):
        return self.__cMax
    
    def display(self):
        cellWidth = max(len(str(self.cMax)) + 2, len(f"C_{self.taskList.m}"), 3)

        separator = color(" | ", fg="cyan")
        div       = color("-+-".join(["-"*cellWidth for _ in range(len(self.taskList) + 1)]), fg="cyan")

        print(separator.join(
            [color(f"{'j':<{cellWidth}}", fg="cyan", style="bold")] +
            [color(f"{t.j:^{cellWidth}}", fg="magenta") for t in self.taskList]
        ))
        print(div)

        for i in range(self.taskList.m):
            print(separator.join(
                [color(f"{'S_'+str(i+1):<{cellWidth}}", fg="blue", style="bold")] +
                [color(f"{time:^{cellWidth}}", fg="blue") for time in self.startTimes[i]]
            ))
            print(separator.join(
                [color(f"{'C_'+str(i+1):<{cellWidth}}", fg="green", style="bold")] +
                [color(f"{time:^{cellWidth}}", fg="green") for time in self.completionTimes[i]]
            ))
            print(div)

        print(color(f"C_max: {self.cMax}", fg="red", style="bold"))
                

def generate_random_task_list(n: int, m: int, Z: int) -> TaskList:
    randGen = RandomNumberGenerator(Z)
    return TaskList(m=m, tasks=[Task(j=j+1, p=tuple(randGen.nextInt(1,29) for _ in range(m))) for j in range(n)])

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

    print(f"\n{div}",
          f"\n{middle}",
          f"\n{div}\n")



def johnson(J: TaskList) -> TaskList:
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

    return TaskList(m=J.m, tasks=[J.tasks[i] for i in pi])

if __name__ == "__main__":
    tasks = generate_random_task_list(n=5, m=5, Z=1)

    print_headline("Generated Task List")
    tasks.display()

    print_headline("Schedule #1: Original Task Order")
    scheduleOriginal = Schedule(tasks)
    scheduleOriginal.display()

