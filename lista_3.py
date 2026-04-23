from RandomNumberGenerator import RandomNumberGenerator
from typing import Iterator
from dataclasses import dataclass
# https://pypi.org/project/ansicolors/
from colors import color

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

    @property
    def C(self):
        return self.__C
    
    @property
    def T(self):
        return self.__T
    
    @property
    def F(self):
        return self.__F
    

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
    pass