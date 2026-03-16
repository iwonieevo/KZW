from RandomNumberGenerator import RandomNumberGenerator
from dataclasses import dataclass

@dataclass
class Task():
    j: int
    p: int
    r: int

    def __str__(self):
        return f"Task(j={self.j}, r={self.r}, p={self.p})"

def getSchedule(orderedTasksList: list[Task]):
    S = [0] * len(orderedTasksList)
    C = [0] * len(orderedTasksList)
    for i, task in enumerate(orderedTasksList):
        if i == 0:
            S[i] = task.r
        else:
            S[i] = max(task.r, C[i-1])
        
        C[i] = S[i] + task.p

    j_str = ["j"] + [str(task.j) for task in orderedTasksList]
    S_str = ["S_j"] + [str(s_i) for s_i in S]
    C_str = ["C_j"] + [str(c_i) for c_i in C]
    col_width = max(len(cell) for cell in j_str + S_str + C_str)

    def format_row(row):
        return " | ".join(f"{cell:>{col_width}}" for i, cell in enumerate(row))
    
    sep_row = "-+-".join("-" * col_width for _ in range(len(j_str)))

    print("\n" + sep_row)
    print(format_row(j_str))
    print(sep_row)
    print(format_row(S_str))
    print(sep_row)
    print(format_row(C_str))
    print(sep_row + "\n")

    return S, C

if __name__ == '__main__':
    n = 10
    Z = 1
    randGen = RandomNumberGenerator(Z)

    tasksList: list[Task] = [Task(j=j, p=randGen.nextInt(1, 29), r=0) for j in range(1, n+1)]
    A: int = sum([task.p for task in tasksList])
    for task in tasksList:
        task.r = randGen.nextInt(1, A)
        print(task)
        
    getSchedule(tasksList)
    getSchedule(sorted(tasksList, key=lambda task: task.r))
