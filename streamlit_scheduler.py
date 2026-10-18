from dataclasses import dataclass
from typing import Literal, Optional, Sequence


AlgorithmId = Literal["fcfs", "sjf", "srtf", "rr", "srr"]


@dataclass(frozen=True)
class ProcessInput:
    id: str
    arrival: int
    burst: int


@dataclass
class ProcessMetrics:
    id: str
    arrival: int
    burst: int
    finish: int
    turnaround: int
    waiting: int
    normalized: float


@dataclass
class SimulationStep:
    time: int
    running: Optional[str]
    remaining: dict[str, int]
    ready: list[str]
    new_arrivals: list[str]
    last_executed: Optional[str]
    accepted: list[str]
    new_queue: list[str]
    priorities: dict[str, int]
    explanation: str


@dataclass
class SimulationResult:
    algorithm: AlgorithmId
    timeline: list[Optional[str]]
    metrics: list[ProcessMetrics]
    steps: list[SimulationStep]
    total_time: int


SAMPLE_PROCESSES = [
    ProcessInput("A", 2, 1),
    ProcessInput("B", 3, 5),
    ProcessInput("C", 0, 4),
    ProcessInput("D", 5, 3),
    ProcessInput("E", 9, 2),
    ProcessInput("F", 7, 4),
    ProcessInput("G", 12, 1),
]


ALGORITHM_INFO: dict[AlgorithmId, dict[str, str]] = {
    "fcfs": {
        "name": "FCFS",
        "description": "Ejecuta cada proceso hasta terminar, respetando el orden de llegada.",
    },
    "sjf": {
        "name": "SJF",
        "description": "Elige el proceso disponible con menor tiempo de CPU.",
    },
    "srtf": {
        "name": "SRTF",
        "description": "Revisa cada unidad y puede interrumpir al proceso actual.",
    },
    "rr": {
        "name": "Round Robin",
        "description": "Rota la CPU entre procesos con un quantum configurable.",
    },
    "srr": {
        "name": "Selfish Round Robin",
        "description": "Los nuevos aumentan +2 y los aceptados +1 hasta ser admitidos.",
    },
}


def ordered_processes(processes: Sequence[ProcessInput]) -> list[ProcessInput]:
    return sorted(processes, key=lambda process: (process.arrival, process.id))


def metrics_for(
    processes: Sequence[ProcessInput], timeline: Sequence[Optional[str]]
) -> list[ProcessMetrics]:
    metrics: list[ProcessMetrics] = []
    for process in processes:
        finish = 0
        for time, process_id in enumerate(timeline):
            if process_id == process.id:
                finish = time + 1
        turnaround = finish - process.arrival
        metrics.append(
            ProcessMetrics(
                id=process.id,
                arrival=process.arrival,
                burst=process.burst,
                finish=finish,
                turnaround=turnaround,
                waiting=turnaround - process.burst,
                normalized=turnaround / process.burst,
            )
        )
    return metrics


def empty_step(
    time: int, running: Optional[str], remaining: dict[str, int]
) -> SimulationStep:
    return SimulationStep(
        time=time,
        running=running,
        remaining=remaining.copy(),
        ready=[],
        new_arrivals=[],
        last_executed=None,
        accepted=[],
        new_queue=[],
        priorities={},
        explanation="",
    )


def simulate_standard(
    processes: Sequence[ProcessInput], algorithm: AlgorithmId, quantum: int
) -> SimulationResult:
    ordered = ordered_processes(processes)
    remaining = {process.id: process.burst for process in ordered}
    timeline: list[Optional[str]] = []
    steps: list[SimulationStep] = []
    queue: list[str] = []
    time = 0
    last_executed: Optional[str] = None
    non_preemptive: Optional[str] = None
    running: Optional[str] = None
    quantum_used = 0

    while any(value > 0 for value in remaining.values()):
        arrivals = [process.id for process in ordered if process.arrival == time]
        explanation = ""

        if algorithm != "rr":
            running = None

        if algorithm in ("fcfs", "sjf"):
            available = [
                process
                for process in ordered
                if process.arrival <= time and remaining[process.id] > 0
            ]
            if non_preemptive and remaining[non_preemptive] > 0:
                running = non_preemptive
            elif available:
                if algorithm == "fcfs":
                    running = available[0].id
                else:
                    running = min(
                        available,
                        key=lambda process: (process.burst, process.arrival),
                    ).id
                non_preemptive = running
            explanation = (
                f"{running} utiliza la CPU hasta completar su rafaga."
                if running
                else "La CPU esta ociosa."
            )
        elif algorithm == "srtf":
            available = [
                process
                for process in ordered
                if process.arrival <= time and remaining[process.id] > 0
            ]
            running = (
                min(
                    available,
                    key=lambda process: (remaining[process.id], process.arrival),
                ).id
                if available
                else None
            )
            explanation = (
                f"SRTF selecciona {running}, que tiene el menor tiempo restante."
                if running
                else "La CPU esta ociosa."
            )
        else:
            queue.extend(arrivals)
            if running and quantum_used >= quantum:
                last_executed = running
                queue.append(running)
                running = None
                quantum_used = 0
            if running is None and queue:
                running = queue.pop(0)
            explanation = (
                f"Round Robin ejecuta {running} (quantum {quantum})."
                if running
                else "La CPU esta ociosa."
            )

        step = empty_step(time, running, remaining)
        step.new_arrivals = arrivals
        step.last_executed = last_executed
        if algorithm == "rr":
            step.ready = queue.copy()
        else:
            step.ready = [
                process.id
                for process in ordered
                if process.arrival <= time
                and remaining[process.id] > 0
                and process.id != running
            ]
        step.explanation = explanation
        timeline.append(running)

        if running:
            remaining[running] -= 1
            if algorithm in ("fcfs", "sjf") and remaining[running] == 0:
                non_preemptive = None
            if algorithm == "rr":
                quantum_used += 1
                if remaining[running] == 0:
                    last_executed = running
                    running = None
                    quantum_used = 0
        else:
            last_executed = None
            quantum_used = 0

        step.remaining = remaining.copy()
        steps.append(step)
        time += 1

    return SimulationResult(
        algorithm=algorithm,
        timeline=timeline,
        metrics=metrics_for(processes, timeline),
        steps=steps,
        total_time=len(timeline),
    )


def simulate_selfish(processes: Sequence[ProcessInput]) -> SimulationResult:
    ordered = ordered_processes(processes)
    remaining = {process.id: process.burst for process in ordered}
    priorities: dict[str, int] = {}
    accepted: list[str] = []
    newcomers: list[str] = []
    timeline: list[Optional[str]] = []
    steps: list[SimulationStep] = []
    time = 0
    last_executed: Optional[str] = None

    while any(value > 0 for value in remaining.values()):
        arrivals = [process.id for process in ordered if process.arrival == time]
        for index, process_id in enumerate(arrivals):
            if time == 0 and index == 0:
                priorities[process_id] = 1
                accepted.append(process_id)
            else:
                priorities[process_id] = 2
                newcomers.append(process_id)

        if time > 0:
            for process_id in accepted:
                priorities[process_id] += 1
        for process_id in newcomers:
            if process_id not in arrivals:
                priorities[process_id] += 2

        minimum_accepted = (
            min(priorities[process_id] for process_id in accepted)
            if accepted
            else float("inf")
        )
        if accepted:
            admitted = [
                process_id
                for process_id in newcomers
                if priorities[process_id] >= minimum_accepted
            ]
        elif newcomers:
            admitted = [
                sorted(
                    newcomers,
                    key=lambda process_id: (-priorities[process_id], process_id),
                )[0]
            ]
        else:
            admitted = []

        for process_id in admitted:
            newcomers.remove(process_id)
        accepted[0:0] = admitted

        accepted_before = accepted.copy()
        running = accepted.pop(0) if accepted else None
        step = empty_step(time, running, remaining)
        step.new_arrivals = arrivals
        step.last_executed = last_executed
        step.ready = [process_id for process_id in accepted_before if process_id != running]
        step.accepted = accepted.copy()
        step.new_queue = newcomers.copy()
        step.priorities = priorities.copy()
        step.explanation = (
            f"Selfish Round Robin ejecuta {running}; aceptados +1 y nuevos +2."
            if running
            else "La CPU esta ociosa."
        )
        timeline.append(running)

        if running:
            remaining[running] -= 1
            if remaining[running] > 0:
                accepted.append(running)
            else:
                del priorities[running]
            last_executed = running
        else:
            last_executed = None

        step.remaining = remaining.copy()
        steps.append(step)
        time += 1

    return SimulationResult(
        algorithm="srr",
        timeline=timeline,
        metrics=metrics_for(processes, timeline),
        steps=steps,
        total_time=len(timeline),
    )


def simulate(
    processes: Sequence[ProcessInput], algorithm: AlgorithmId, quantum: int = 1
) -> SimulationResult:
    if algorithm == "srr":
        return simulate_selfish(processes)
    return simulate_standard(processes, algorithm, quantum)
