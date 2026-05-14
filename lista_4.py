from RandomNumberGenerator import RandomNumberGenerator
from dataclasses import dataclass
from typing import Iterator
# https://pypi.org/project/ansicolors/
from colors import color


@dataclass(frozen=True, kw_only=True, order=True)
class Operation:
    """Single operation: belongs to task j, runs on machine m for p time units."""
    k: int          # operation index within the task (1-based)
    j: int          # task index (1-based)
    m: int          # machine index (1-based)
    p: int          # processing time

    def __str__(self) -> str:
        return (
            color(f"o({self.k})", fg="cyan") +
            color(f"j={self.j}", fg="magenta") +
            f" m={color(str(self.m), fg='yellow')} p={color(str(self.p), fg='orange')}"
        )


@dataclass(frozen=True, kw_only=True, order=True)
class Task:
    """A task is an ordered sequence of operations with a fixed technological route."""
    j: int
    O: tuple[Operation, ...]

    @property
    def num_operations(self) -> int:
        return len(self.O)

    @property
    def total_processing_time(self) -> int:
        return sum(op.p for op in self.O)

    def __str__(self) -> str:
        ops = "  ".join(
            color(f"[m{op.m}|p={op.p}]", fg="orange")
            for op in self.O
        )
        return (
            color(f"j={self.j}", fg="magenta", style="bold") +
            f"  ops={color(str(self.num_operations), fg='cyan')}  " +
            ops
        )


@dataclass(frozen=True, kw_only=True)
class JobList:
    """Unscheduled collection of tasks."""
    tasks: tuple[Task, ...]

    @property
    def n(self) -> int:
        return len(self.tasks)

    @property
    def machines(self) -> frozenset[int]:
        return frozenset(op.m for t in self.tasks for op in t.O)

    @property
    def m(self) -> int:
        return len(self.machines)

    def __iter__(self) -> Iterator[Task]:
        return iter(self.tasks)

    def __len__(self) -> int:
        return self.n

    def display(self) -> None:
        """Pretty-print the task list (unscheduled view)."""
        title = f"n={self.n}  m={self.m}  machines={sorted(self.machines)}"
        print(color(title, fg="green", style="bold"))

        # column widths
        col_j   = max(3, max(len(str(t.j)) for t in self.tasks) + 1)
        col_ops = max(4, max(len(str(t.num_operations)) for t in self.tasks) + 1)
        col_sum = max(5, max(len(str(t.total_processing_time)) for t in self.tasks) + 1)

        sep = color(" | ", fg="cyan")
        div_base = f"-+-".join(["-" * col_j, "-" * col_ops, "-" * col_sum])

        print(sep.join([
            color(f"{'j':^{col_j}}", fg="magenta", style="bold"),
            color(f"{'ops':^{col_ops}}", fg="cyan", style="bold"),
            color(f"{'Σp':^{col_sum}}", fg="red", style="bold"),
            color("route  (machine → p)", fg="yellow", style="bold"),
        ]))
        print(color(div_base + "-+---------------------------", fg="cyan"))

        for t in self.tasks:
            route = "  →  ".join(
                color(f"M{op.m}", fg="yellow") + color(f"({op.p})", fg="orange")
                for op in t.O
            )
            print(sep.join([
                color(f"{t.j:^{col_j}}", fg="magenta"),
                color(f"{t.num_operations:^{col_ops}}", fg="cyan"),
                color(f"{t.total_processing_time:^{col_sum}}", fg="red"),
                route,
            ]))


@dataclass(frozen=True, kw_only=True, order=True)
class ScheduledOperation:
    """An operation placed on the time-line."""
    operation: Operation
    start:     int

    @property
    def m(self) -> int:
        return self.operation.m

    @property
    def j(self) -> int:
        return self.operation.j

    @property
    def p(self) -> int:
        return self.operation.p
    
    @property
    def end(self) -> int:
        return self.start + self.operation.p


@dataclass
class Schedule:
    """
    Holds a feasible (or candidate) schedule for the Job Shop.

    Parameters
    ----------
    job_list : JobList
        The original unscheduled jobs.
    scheduled_ops : list[ScheduledOperation]
        All operations placed on the timeline.  The constructor validates
        basic consistency and computes Cmax.
    """
    job_list:       JobList
    scheduled_ops:  list[ScheduledOperation]

    def __post_init__(self) -> None:
        self._validate()
        self._cmax: int = max(so.end for so in self.scheduled_ops) if self.scheduled_ops else 0


    def _validate(self) -> None:
        """Light-weight feasibility checks."""
        # no negative starts
        for so in self.scheduled_ops:
            if so.start < 0:
                raise ValueError(f"Negative start time for {so}")
            if so.end != so.start + so.p:
                raise ValueError(f"end != start+p for {so}")

        # machine non-overlap
        by_machine: dict[int, list[ScheduledOperation]] = {}
        for so in self.scheduled_ops:
            by_machine.setdefault(so.m, []).append(so)

        for m, ops in by_machine.items():
            ops_sorted = sorted(ops, key=lambda x: x.start)
            for a, b in zip(ops_sorted, ops_sorted[1:]):
                if b.start < a.end:
                    raise ValueError(
                        f"Machine {m} overlap: job {a.j} ends at {a.end}, "
                        f"job {b.j} starts at {b.start}"
                    )

        by_task: dict[int, list[ScheduledOperation]] = {}
        for so in self.scheduled_ops:
            by_task.setdefault(so.j, []).append(so)

        for task in self.job_list:
            ops = by_task.get(task.j, [])
            ops_sorted = sorted(ops, key=lambda x: x.operation.k)
            for a, b in zip(ops_sorted, ops_sorted[1:]):
                if b.start < a.end:
                    raise ValueError(
                        f"Technological order violated for task {task.j}: "
                        f"op {a.operation.k} ends at {a.end}, "
                        f"op {b.operation.k} starts at {b.start}"
                    )


    @property
    def cmax(self) -> int:
        return self._cmax


    def _ops_by_machine(self) -> dict[int, list[ScheduledOperation]]:
        d: dict[int, list[ScheduledOperation]] = {}
        for so in self.scheduled_ops:
            d.setdefault(so.m, []).append(so)
        for ops in d.values():
            ops.sort(key=lambda x: x.start)
        return d


    def display(self) -> None:
        """
        Print the schedule grouped by machine.
        For each machine: a sorted list of (start, end, task, duration, op-index).
        Also prints a compact ASCII Gantt for a quick visual overview.
        """
        by_machine = self._ops_by_machine()
        machines   = sorted(by_machine.keys())

        # column widths
        w_m     = max(2, max(len(str(m)) for m in machines) + 1)
        w_j     = max(2, max(len(str(so.j))     for so in self.scheduled_ops) + 1)
        w_k     = max(2, max(len(str(so.operation.k)) for so in self.scheduled_ops) + 1)
        w_p     = max(2, max(len(str(so.p))     for so in self.scheduled_ops) + 1)
        w_time  = max(5, len(str(self.cmax)) + 2)

        sep = color(" | ", fg="cyan")

        # header
        headers = ["M", "j", "op", "p", "start", "end"]
        widths  = [w_m, w_j, w_k, w_p, w_time, w_time]
        fg_cols = ["yellow", "magenta", "cyan", "orange", "blue", "green"]

        print(color(f"Cmax = {self.cmax}", fg="red", style="bold"))
        print()
        print(sep.join(
            color(f"{h:^{w}}", fg=f, style="bold")
            for h, w, f in zip(headers, widths, fg_cols)
        ))
        div = color("-+-".join("-" * w for w in widths), fg="cyan")

        for m in machines:
            print(color("═" * (sum(widths) + 3 * (len(widths) - 1) + 2), fg="cyan"))
            for so in by_machine[m]:
                print(sep.join([
                    color(f"{so.m:^{w_m}}",    fg="yellow"),
                    color(f"{so.j:^{w_j}}",    fg="magenta"),
                    color(f"{so.operation.k:^{w_k}}", fg="cyan"),
                    color(f"{so.p:^{w_p}}",    fg="orange"),
                    color(f"{so.start:^{w_time}}", fg="blue"),
                    color(f"{so.end:^{w_time}}",   fg="green"),
                ]))
            print(div)

        print()
        self._display_gantt(by_machine, machines)

    def _display_gantt(
        self,
        by_machine: dict[int, list[ScheduledOperation]],
        machines:   list[int],
        width:      int = 60,
    ) -> None:
        """Compact text Gantt chart scaled to `width` characters."""
        scale = self.cmax / width if self.cmax else 1

        label_w = max(len(f"M{m}") for m in machines) + 1
        bar_colors = [
            "magenta", "orange", "blue", "green",
            "cyan", (200, 100, 255), (255, 200, 50), (50, 220, 180),
        ]

        print(color("GANTT", fg="white", style="bold+underline"))

        # time ruler
        ruler_marks = 5
        step = max(1, self.cmax // ruler_marks)
        ruler = " " * label_w + " "
        ticks = list(range(0, self.cmax + 1, step))
        positions: list[int] = []
        for t in ticks:
            pos = int(t / scale)
            positions.append(pos)
        # build ruler string
        ruler_str = [" "] * width
        for t, pos in zip(ticks, positions):
            s = str(t)
            for i, ch in enumerate(s):
                if pos + i < width:
                    ruler_str[pos + i] = ch
        print(" " * (label_w + 1) + color("".join(ruler_str), fg="white"))
        print(" " * (label_w + 1) + color("─" * width, fg="white"))

        for m in machines:
            bar = [" "] * width
            col_bar = [""] * width

            for so in by_machine[m]:
                c = bar_colors[(so.j - 1) % len(bar_colors)]
                l = int(so.start / scale)
                r = max(l + 1, int(so.end / scale))
                label = str(so.j)
                for i in range(l, min(r, width)):
                    bar[i] = label[0] if (i - l) < len(label) else "█"
                    col_bar[i] = c  # type: ignore[assignment]

            label_str = color(f"M{m:<{label_w - 1}}", fg="yellow", style="bold")
            row = ""
            for ch, c in zip(bar, col_bar):
                if c:
                    row += color(ch, fg=c)
                else:
                    row += color("·", fg=(80, 80, 80))
            print(f"{label_str} {row}")

    

# assume joblist generation is already implemented

# Internal helper to create a Schedule from a task order using greedy earliest-start-time scheduling.
def schedule_from_task_order(job_list: JobList, task_order: list[Task]) -> Schedule:
    """Internal: produce a Schedule from a task ordering using greedy earliest-start-time."""
    scheduled_ops: list[ScheduledOperation] = []
    machine_free_time: dict[int, int] = {m: 0 for m in job_list.machines}
    task_completion_time: dict[int, int] = {}
    
    for task in task_order:
        for op in task.O:
            earliest_start = task_completion_time.get(task.j, 0)
            earliest_start = max(earliest_start, machine_free_time[op.m])
            scheduled_ops.append(ScheduledOperation(operation=op, start=earliest_start))
            op_end = earliest_start + op.p
            machine_free_time[op.m] = op_end
            task_completion_time[task.j] = op_end
    
    return Schedule(job_list, scheduled_ops)


# NEH heuristic implementation by Claude - TODO: testing
def neh(job_list: JobList) -> Schedule:
    """
    NEH (Nawaz, Enscore, Ham) heuristic following the pseudocode.
    
    Builds schedule by processing tasks in order of decreasing processing time,
    inserting each at the position that minimizes Cmax.
    """
    tasks = list(job_list.tasks)
    if not tasks:
        return Schedule(job_list, [])
    
    # Calculate total processing time for each task (ωⱼ in pseudocode)
    processing_times: dict[int, int] = {task.j: task.total_processing_time for task in tasks}
    
    # Priority queue W: tasks ordered by processing time (descending)
    waiting_queue = sorted(tasks, key=lambda t: processing_times[t.j], reverse=True)
    
    # Start with empty schedule
    current_schedule: list[Task] = []
    k = 1
    
    # Process each task from the queue
    while waiting_queue:
        # Get task with max processing time (argmax ωⱼ)
        candidate_task = waiting_queue.pop(0)
        
        # Try inserting at each position from 1 to k
        best_position = 0
        best_cmax = float('inf')
        best_schedule_obj = None
        
        for insert_pos in range(k):  # positions 1 to k (0-indexed: 0 to k-1)
            # π'.INSERT(j*, l) - insert candidate at position l
            temp_order = current_schedule[:insert_pos] + [candidate_task] + current_schedule[insert_pos:]
            temp_schedule = schedule_from_task_order(job_list, temp_order)
            
            # if π'.INSERT(j*,l).Cₘₐₓ < π*.Cₘₐₓ
            if temp_schedule.cmax < best_cmax:
                best_cmax = temp_schedule.cmax
                best_position = insert_pos
                best_schedule_obj = temp_schedule
        
        # π* ← π'.INSERT(j*, l) with best l
        current_schedule.insert(best_position, candidate_task)
        
        # W ← W \ {j*} (already removed by pop)
        k += 1
    
    # Return final schedule
    return schedule_from_task_order(job_list, current_schedule)