export type AlgorithmId = 'fcfs' | 'sjf' | 'srtf' | 'rr' | 'srr';

export type ProcessInput = {
  id: string;
  arrival: number;
  burst: number;
};

export type AlgorithmConfig = {
  quantum: number;
};

export type ProcessMetrics = ProcessInput & {
  finish: number;
  turnaround: number;
  waiting: number;
  normalized: number;
};

export type SimulationStep = {
  time: number;
  running: string | null;
  remaining: Record<string, number>;
  ready: string[];
  newArrivals: string[];
  lastExecuted: string | null;
  accepted: string[];
  newQueue: string[];
  priorities: Record<string, number>;
  explanation: string;
};

export type SimulationResult = {
  algorithm: AlgorithmId;
  timeline: (string | null)[];
  metrics: ProcessMetrics[];
  steps: SimulationStep[];
  totalTime: number;
};

export const SAMPLE_PROCESSES: ProcessInput[] = [
  { id: 'A', arrival: 2, burst: 1 },
  { id: 'B', arrival: 3, burst: 5 },
  { id: 'C', arrival: 0, burst: 4 },
  { id: 'D', arrival: 5, burst: 3 },
  { id: 'E', arrival: 9, burst: 2 },
  { id: 'F', arrival: 7, burst: 4 },
  { id: 'G', arrival: 12, burst: 1 },
];

export const DEFAULT_CONFIG: AlgorithmConfig = { quantum: 1 };

export const ALGORITHM_INFO: Record<AlgorithmId, { name: string; short: string; description: string }> = {
  fcfs: { name: 'FCFS', short: 'Primero en llegar', description: 'Ejecuta cada proceso hasta terminar, respetando el orden de llegada.' },
  sjf: { name: 'SJF', short: 'Proceso más corto', description: 'Elige el proceso disponible con menor tiempo de CPU.' },
  srtf: { name: 'SRTF', short: 'Menor tiempo restante', description: 'Revisa cada unidad y puede interrumpir al proceso actual.' },
  rr: { name: 'Round Robin', short: 'Listos / Nuevos / Último', description: 'Rota la CPU entre procesos con un quantum configurable.' },
  srr: { name: 'Selfish Round Robin', short: 'Aceptados / Nuevos', description: 'Los nuevos aumentan +2 y los aceptados +1 hasta ser admitidos.' },
};

function orderedProcesses(processes: ProcessInput[]) {
  return [...processes].sort((a, b) => a.arrival - b.arrival || a.id.localeCompare(b.id));
}

function metricsFor(processes: ProcessInput[], timeline: (string | null)[]): ProcessMetrics[] {
  return processes.map((process) => {
    const finish = timeline.reduce((last, id, time) => id === process.id ? time + 1 : last, 0);
    const turnaround = finish - process.arrival;
    return { ...process, finish, turnaround, waiting: turnaround - process.burst, normalized: turnaround / process.burst };
  });
}

function emptyStep(time: number, running: string | null, remaining: Record<string, number>): SimulationStep {
  return { time, running, remaining: { ...remaining }, ready: [], newArrivals: [], lastExecuted: null, accepted: [], newQueue: [], priorities: {}, explanation: '' };
}

function simulateStandard(processes: ProcessInput[], algorithm: Exclude<AlgorithmId, 'srr'>, config: AlgorithmConfig): SimulationResult {
  const ordered = orderedProcesses(processes);
  const remaining = Object.fromEntries(ordered.map((process) => [process.id, process.burst]));
  const timeline: (string | null)[] = [];
  const steps: SimulationStep[] = [];
  const queue: string[] = [];
  let time = 0;
  let lastExecuted: string | null = null;
  let nonPreemptive: string | null = null;
  let running: string | null = null;
  let quantumUsed = 0;

  while (Object.values(remaining).some((value) => value > 0)) {
    const arrivals = ordered.filter((process) => process.arrival === time).map((process) => process.id);
    let explanation = '';
    if (algorithm !== 'rr') running = null;

    if (algorithm === 'fcfs' || algorithm === 'sjf') {
      const available = ordered.filter((process) => process.arrival <= time && remaining[process.id] > 0);
      if (nonPreemptive && remaining[nonPreemptive] > 0) running = nonPreemptive;
      else if (available.length) {
        running = algorithm === 'fcfs'
          ? available[0].id
          : [...available].sort((a, b) => a.burst - b.burst || a.arrival - b.arrival)[0].id;
        nonPreemptive = running;
      }
      explanation = running ? `${running} utiliza la CPU hasta completar su ráfaga.` : 'La CPU está ociosa.';
    } else if (algorithm === 'srtf') {
      const available = ordered.filter((process) => process.arrival <= time && remaining[process.id] > 0);
      running = [...available].sort((a, b) => remaining[a.id] - remaining[b.id] || a.arrival - b.arrival)[0]?.id ?? null;
      explanation = running ? `SRTF selecciona ${running}, que tiene el menor tiempo restante.` : 'La CPU está ociosa.';
    } else {
      queue.push(...arrivals);
      if (running && quantumUsed >= config.quantum) {
        lastExecuted = running;
        queue.push(running);
        running = null;
        quantumUsed = 0;
      }
      if (!running) running = queue.shift() ?? null;
      explanation = running ? `Round Robin ejecuta ${running} (quantum ${config.quantum}).` : 'La CPU está ociosa.';
    }

    const step = emptyStep(time, running, remaining);
    step.newArrivals = arrivals;
    step.lastExecuted = lastExecuted;
    step.ready = algorithm === 'rr'
      ? [...queue]
      : ordered.filter((process) => process.arrival <= time && remaining[process.id] > 0 && process.id !== running).map((process) => process.id);
    step.explanation = explanation;
    timeline.push(running);

    if (running) {
      remaining[running] -= 1;
      if ((algorithm === 'fcfs' || algorithm === 'sjf') && remaining[running] === 0) nonPreemptive = null;
      if (algorithm === 'rr') {
        quantumUsed += 1;
        if (remaining[running] === 0) {
          lastExecuted = running;
          running = null;
          quantumUsed = 0;
        }
      }
    } else {
      lastExecuted = null;
      quantumUsed = 0;
    }
    step.remaining = { ...remaining };
    steps.push(step);
    time += 1;
  }

  return { algorithm, timeline, metrics: metricsFor(processes, timeline), steps, totalTime: timeline.length };
}

function simulateSelfish(processes: ProcessInput[]): SimulationResult {
  const ordered = orderedProcesses(processes);
  const remaining = Object.fromEntries(ordered.map((process) => [process.id, process.burst]));
  const priorities: Record<string, number> = {};
  const accepted: string[] = [];
  const newcomers: string[] = [];
  const timeline: (string | null)[] = [];
  const steps: SimulationStep[] = [];
  let time = 0;
  let lastExecuted: string | null = null;

  while (Object.values(remaining).some((value) => value > 0)) {
    const arrivals = ordered.filter((process) => process.arrival === time).map((process) => process.id);
    arrivals.forEach((id, index) => {
      if (time === 0 && index === 0) { priorities[id] = 1; accepted.push(id); }
      else { priorities[id] = 2; newcomers.push(id); }
    });
    if (time > 0) accepted.forEach((id) => priorities[id] += 1);
    newcomers.filter((id) => !arrivals.includes(id)).forEach((id) => priorities[id] += 2);

    const minimumAccepted = accepted.length ? Math.min(...accepted.map((id) => priorities[id])) : Infinity;
    const admitted = accepted.length
      ? newcomers.filter((id) => priorities[id] >= minimumAccepted)
      : newcomers.length ? [newcomers.slice().sort((a, b) => priorities[b] - priorities[a] || a.localeCompare(b))[0]] : [];
    admitted.forEach((id) => newcomers.splice(newcomers.indexOf(id), 1));
    if (admitted.length) accepted.unshift(...admitted);

    const acceptedBefore = [...accepted];
    const running = accepted.shift() ?? null;
    const step = emptyStep(time, running, remaining);
    step.newArrivals = arrivals;
    step.lastExecuted = lastExecuted;
    step.ready = acceptedBefore.filter((id) => id !== running);
    step.accepted = [...accepted];
    step.newQueue = [...newcomers];
    step.priorities = { ...priorities };
    step.explanation = running ? `Selfish Round Robin ejecuta ${running}; aceptados +1 y nuevos +2.` : 'La CPU está ociosa.';
    timeline.push(running);
    if (running) {
      remaining[running] -= 1;
      if (remaining[running] > 0) accepted.push(running);
      else delete priorities[running];
      lastExecuted = running;
    } else lastExecuted = null;
    step.remaining = { ...remaining };
    steps.push(step);
    time += 1;
  }

  return { algorithm: 'srr', timeline, metrics: metricsFor(processes, timeline), steps, totalTime: timeline.length };
}

export function simulate(processes: ProcessInput[], algorithm: AlgorithmId, config: AlgorithmConfig = DEFAULT_CONFIG): SimulationResult {
  return algorithm === 'srr' ? simulateSelfish(processes) : simulateStandard(processes, algorithm, config);
}
