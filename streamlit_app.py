import html
import json
import math
from dataclasses import asdict
from typing import Any, Optional

import pandas as pd
import streamlit as st

from streamlit_scheduler import (
    ALGORITHM_INFO,
    SAMPLE_PROCESSES,
    AlgorithmId,
    ProcessInput,
    SimulationResult,
    simulate,
)


COLORS = [
    "#9bcf53",
    "#ef4444",
    "#f3e319",
    "#f28c28",
    "#7d3bb2",
    "#16a765",
    "#83c6d9",
    "#f59e0b",
    "#e879f9",
    "#0ea5e9",
    "#e11d48",
    "#65a30d",
]


def records_from_sample() -> list[dict[str, Any]]:
    return [asdict(process) for process in SAMPLE_PROCESSES]


def clear_result() -> None:
    st.session_state.result = None
    st.session_state.step_mode = False
    st.session_state.active_step = 0


def initialize_state() -> None:
    if "process_records" not in st.session_state:
        st.session_state.process_records = records_from_sample()
    if "editor_version" not in st.session_state:
        st.session_state.editor_version = 0
    if "result" not in st.session_state:
        st.session_state.result = None
    if "active_step" not in st.session_state:
        st.session_state.active_step = 0
    if "step_mode" not in st.session_state:
        st.session_state.step_mode = False
    if "quantum" not in st.session_state:
        st.session_state.quantum = 1


def integer_value(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    try:
        if pd.isna(value):
            return None
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric) or not numeric.is_integer():
        return None
    return int(numeric)


def parse_processes(records: list[dict[str, Any]]) -> tuple[list[ProcessInput], list[str]]:
    processes: list[ProcessInput] = []
    errors: list[str] = []

    for index, record in enumerate(records, start=1):
        raw_id = record.get("id", "")
        process_id = "" if raw_id is None or pd.isna(raw_id) else str(raw_id).strip().upper()
        arrival = integer_value(record.get("arrival"))
        burst = integer_value(record.get("burst"))
        if not process_id:
            errors.append(f"La fila {index} necesita un identificador.")
        if arrival is None or not 0 <= arrival <= 20:
            errors.append(f"La llegada del proceso de la fila {index} debe ser un entero entre 0 y 20.")
        if burst is None or not 1 <= burst <= 20:
            errors.append(f"El CPU del proceso de la fila {index} debe ser un entero entre 1 y 20.")
        processes.append(ProcessInput(process_id, arrival or 0, burst or 0))

    ids = [process.id for process in processes]
    if len(ids) != len(set(ids)):
        errors.append("Cada proceso debe tener un identificador unico.")
    return processes, errors


def format_number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.2f}"


def format_queue(items: list[str], priorities: Optional[dict[str, int]] = None) -> str:
    priorities = priorities or {}
    if not items:
        return "-"
    return " · ".join(
        f"{process_id}={priorities[process_id]}" if process_id in priorities else process_id
        for process_id in items
    )


def process_color(processes: list[ProcessInput], process_id: Optional[str]) -> str:
    if process_id is None:
        return "#ffffff"
    index = next(
        (index for index, process in enumerate(processes) if process.id == process_id),
        0,
    )
    return COLORS[index % len(COLORS)]


def render_timeline(
    processes: list[ProcessInput], result: SimulationResult, step_mode: bool, active_step: int
) -> None:
    def visible_process_at(time: int) -> Optional[str]:
        if step_mode and time > active_step:
            return None
        return result.timeline[time]

    header_cells = "".join(f"<th>{time}</th>" for time in range(result.total_time + 1))
    rows = [f"<tr><th class='label'>Proceso</th>{header_cells}</tr>"]
    colors = {process.id: process_color(processes, process.id) for process in processes}

    for process in processes:
        cells = []
        for time in range(result.total_time):
            running_id = visible_process_at(time)
            current = step_mode and time == active_step and running_id == process.id
            background = colors[process.id] if running_id == process.id else "#fafbf9" if time < process.arrival else "#ffffff"
            border = "3px solid #102a43" if current else "1px solid #edf0ed"
            text = html.escape(process.id) if running_id == process.id else ""
            cells.append(
                f"<td style='background:{background};border:{border}'>{text}</td>"
            )
        rows.append(
            f"<tr><th class='label'><span class='dot' style='background:{colors[process.id]}'></span>"
            f"{html.escape(process.id)}</th>{''.join(cells)}</tr>"
        )

    cpu_cells = []
    for time in range(result.total_time):
        running_id = visible_process_at(time)
        current = step_mode and time == active_step
        background = colors.get(running_id, "#ffffff")
        border = "3px solid #102a43" if current else "1px solid #edf0ed"
        text = html.escape(running_id) if running_id else "·"
        cpu_cells.append(
            f"<td style='background:{background};border:{border}'>{text}</td>"
        )
    rows.append(f"<tr class='cpu'><th class='label'>CPU</th>{''.join(cpu_cells)}</tr>")

    st.markdown(
        "<style>"
        ".timeline-wrap { overflow-x: auto; background: white; border: 1px solid #d9e1dc; padding: 14px; }"
        ".timeline-table { border-collapse: collapse; min-width: 760px; width: 100%; table-layout: fixed; }"
        ".timeline-table th, .timeline-table td { height: 32px; min-width: 32px; text-align: center; font: 11px 'monospace'; }"
        ".timeline-table th { color: #71808a; font-weight: 500; }"
        ".timeline-table .label { width: 100px; text-align: left; color: #17324d; white-space: nowrap; }"
        ".timeline-table .dot { display: inline-block; width: 18px; height: 18px; border-radius: 50%; vertical-align: middle; margin-right: 6px; }"
        ".timeline-table .cpu th, .timeline-table .cpu td { border-top: 2px solid #17324d !important; }"
        "</style>"
        f"<div class='timeline-wrap'><table class='timeline-table'>{''.join(rows)}</table></div>",
        unsafe_allow_html=True,
    )


def render_metrics(result: SimulationResult) -> None:
    metrics = pd.DataFrame(
        [
            {
                "Proceso": metric.id,
                "Llegada": metric.arrival,
                "CPU": metric.burst,
                "Final": metric.finish,
                "Retorno": metric.turnaround,
                "Espera": metric.waiting,
                "T Promedio": format_number(metric.normalized),
            }
            for metric in result.metrics
        ]
    )
    st.dataframe(metrics, hide_index=True, use_container_width=True)

    count = len(result.metrics)
    averages = {
        "CPU": sum(metric.burst for metric in result.metrics) / count,
        "Retorno": sum(metric.turnaround for metric in result.metrics) / count,
        "Espera": sum(metric.waiting for metric in result.metrics) / count,
        "T Promedio": sum(metric.normalized for metric in result.metrics) / count,
    }
    st.caption(
        "Promedios: "
        + " | ".join(f"{name}: {format_number(value)}" for name, value in averages.items())
    )


def main() -> None:
    st.set_page_config(page_title="CPU Scheduler Lab", layout="wide")
    initialize_state()

    st.title("CPU Scheduler Lab")
    st.write("Construye una planificación, observa cada decisión y compara sus resultados.")

    algorithm_options = list(ALGORITHM_INFO)
    previous_algorithm = st.session_state.get("last_algorithm")
    algorithm = st.selectbox(
        "Algoritmo",
        algorithm_options,
        index=algorithm_options.index("srtf"),
        format_func=lambda value: ALGORITHM_INFO[value]["name"],
    )
    if previous_algorithm is not None and previous_algorithm != algorithm:
        clear_result()
    st.session_state.last_algorithm = algorithm

    st.info(ALGORITHM_INFO[algorithm]["description"])
    quantum = st.session_state.quantum
    if algorithm == "rr":
        quantum = st.number_input("Quantum", min_value=1, max_value=20, value=quantum, step=1)
        if quantum != st.session_state.quantum:
            clear_result()
        st.session_state.quantum = int(quantum)

    st.subheader("Procesos")
    if st.button("Restaurar ejemplo"):
        st.session_state.process_records = records_from_sample()
        st.session_state.editor_version += 1
        clear_result()
        st.rerun()

    process_table = pd.DataFrame(st.session_state.process_records)
    edited_table = st.data_editor(
        process_table,
        key=f"process_editor_{st.session_state.editor_version}",
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        column_config={
            "id": st.column_config.TextColumn("Proceso", required=True, max_chars=3),
            "arrival": st.column_config.NumberColumn("Llegada", min_value=0, max_value=20, step=1),
            "burst": st.column_config.NumberColumn("CPU", min_value=1, max_value=20, step=1),
        },
    )
    records = edited_table.to_dict(orient="records")
    signature = json.dumps(records, sort_keys=True, default=str)
    previous_signature = st.session_state.get("editor_signature")
    if previous_signature is not None and previous_signature != signature:
        clear_result()
    st.session_state.editor_signature = signature

    if st.button("Ejecutar simulacion", type="primary"):
        processes, errors = parse_processes(records)
        if errors:
            for error in errors:
                st.error(error)
        else:
            result = simulate(processes, algorithm, int(quantum))
            st.session_state.process_records = [asdict(process) for process in processes]
            st.session_state.result = result
            st.session_state.active_step = result.total_time - 1
            st.session_state.step_mode = False

    result: Optional[SimulationResult] = st.session_state.result
    if result is None:
        st.caption(f"{len(records)} procesos cargados")
        return

    processes, errors = parse_processes(records)
    if errors:
        st.warning("La tabla fue modificada. Ejecuta nuevamente la simulacion para actualizar el resultado.")
        processes = [ProcessInput(metric.id, metric.arrival, metric.burst) for metric in result.metrics]

    st.subheader("Ejecucion")
    controls = st.columns([1, 1, 4])
    if controls[0].button("Anterior"):
        if st.session_state.step_mode:
            st.session_state.active_step = max(0, st.session_state.active_step - 1)
        else:
            st.session_state.active_step = max(0, result.total_time - 2)
        st.session_state.step_mode = True
        st.rerun()
    if controls[1].button("Siguiente"):
        if st.session_state.step_mode:
            st.session_state.active_step = min(result.total_time - 1, st.session_state.active_step + 1)
        else:
            st.session_state.active_step = 0
        st.session_state.step_mode = True
        st.rerun()

    active_step = st.session_state.active_step if st.session_state.step_mode else result.total_time - 1
    step = result.steps[active_step]
    if st.session_state.step_mode:
        st.caption(f"Paso {active_step + 1} / {result.total_time} - tiempo {active_step}")
    else:
        st.caption(f"Diagrama completo - {result.total_time} pasos")
    st.write(step.explanation)

    if result.algorithm == "srr":
        st.write(f"**Aceptados:** {format_queue(step.accepted, step.priorities)}")
        st.write(f"**Nuevos:** {format_queue(step.new_queue, step.priorities)}")
    else:
        st.write(f"**Listos:** {format_queue(step.ready)}")
        st.write(f"**Nuevos:** {format_queue(step.new_arrivals)}")
        st.write(f"**Ultimo ejecutado:** {format_queue([step.last_executed] if step.last_executed else [])}")
    st.write(f"**CPU:** {step.running or '-'}")

    render_timeline(processes, result, st.session_state.step_mode, active_step)
    st.subheader("Metricas de la ejecucion")
    render_metrics(result)


if __name__ == "__main__":
    main()
