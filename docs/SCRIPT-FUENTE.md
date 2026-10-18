# Script del código fuente

Documento generado con `npm run export:source`. Contiene los archivos principales del proyecto Angular, su motor de simulación y sus pruebas.

## package.json

```json
{
  "name": "proyecto-so",
  "version": "0.0.0",
  "scripts": {
    "ng": "ng",
    "start": "ng serve",
    "build": "ng build",
    "watch": "ng build --watch --configuration development",
    "test": "ng test",
    "export:source": "node scripts/export-source.mjs"
  },
  "private": true,
  "packageManager": "npm@10.9.7",
  "dependencies": {
    "@angular/common": "^21.2.0",
    "@angular/compiler": "^21.2.0",
    "@angular/core": "^21.2.0",
    "@angular/forms": "^21.2.0",
    "@angular/platform-browser": "^21.2.0",
    "@angular/router": "^21.2.0",
    "rxjs": "~7.8.0",
    "tslib": "^2.3.0"
  },
  "devDependencies": {
    "@angular/build": "^21.2.11",
    "@angular/cli": "^21.2.11",
    "@angular/compiler-cli": "^21.2.0",
    "jsdom": "^28.0.0",
    "prettier": "^3.8.1",
    "typescript": "~5.9.2",
    "vitest": "^4.0.8"
  }
}

```

## angular.json

```json
{
  "$schema": "./node_modules/@angular/cli/lib/config/schema.json",
  "version": 1,
  "cli": {
    "packageManager": "npm"
  },
  "newProjectRoot": "projects",
  "projects": {
    "proyectoSO": {
      "projectType": "application",
      "schematics": {},
      "root": "",
      "sourceRoot": "src",
      "prefix": "app",
      "architect": {
        "build": {
          "builder": "@angular/build:application",
          "options": {
            "browser": "src/main.ts",
            "tsConfig": "tsconfig.app.json",
            "assets": [
              {
                "glob": "**/*",
                "input": "public"
              }
            ],
            "styles": [
              "src/styles.css"
            ]
          },
          "configurations": {
            "production": {
              "budgets": [
                {
                  "type": "initial",
                  "maximumWarning": "500kB",
                  "maximumError": "1MB"
                },
                {
                  "type": "anyComponentStyle",
                  "maximumWarning": "8kB",
                  "maximumError": "12kB"
                }
              ],
              "outputHashing": "all"
            },
            "development": {
              "optimization": false,
              "extractLicenses": false,
              "sourceMap": true
            }
          },
          "defaultConfiguration": "production"
        },
        "serve": {
          "builder": "@angular/build:dev-server",
          "configurations": {
            "production": {
              "buildTarget": "proyectoSO:build:production"
            },
            "development": {
              "buildTarget": "proyectoSO:build:development"
            }
          },
          "defaultConfiguration": "development"
        },
        "test": {
          "builder": "@angular/build:unit-test"
        }
      }
    }
  }
}

```

## src/app/scheduler.ts

```ts
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

```

## src/app/app.ts

```ts
import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  ALGORITHM_INFO,
  DEFAULT_CONFIG,
  SAMPLE_PROCESSES,
  type AlgorithmConfig,
  type AlgorithmId,
  type ProcessInput,
  type SimulationResult,
  simulate,
} from './scheduler';

const COLORS = ['#9bcf53', '#ef4444', '#f3e319', '#f28c28', '#7d3bb2', '#16a765', '#83c6d9', '#f59e0b', '#e879f9', '#0ea5e9', '#e11d48', '#65a30d'];
const ALGORITHMS = Object.keys(ALGORITHM_INFO) as AlgorithmId[];

@Component({
  selector: 'app-root',
  imports: [FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  protected readonly algorithms = ALGORITHMS;
  protected readonly algorithmInfo = ALGORITHM_INFO;
  protected readonly colors = COLORS;
  protected readonly algorithm = signal<AlgorithmId>('srtf');
  protected readonly processes = signal<ProcessInput[]>(SAMPLE_PROCESSES.map((process) => ({ ...process })));
  protected readonly result = signal<SimulationResult | null>(null);
  protected readonly activeStep = signal(0);
  protected readonly isStepping = signal(false);
  protected readonly error = signal('');
  protected readonly config = signal<AlgorithmConfig>({ ...DEFAULT_CONFIG });

  protected readonly selected = computed(() => this.algorithmInfo[this.algorithm()]);
  protected readonly currentStep = computed(() => this.result()?.steps[this.activeStep()] ?? null);
  protected readonly averages = computed(() => {
    const result = this.result();
    if (!result) return null;
    const count = result.metrics.length;
    return {
      cpu: result.metrics.reduce((sum, item) => sum + item.burst, 0) / count,
      turnaround: result.metrics.reduce((sum, item) => sum + item.turnaround, 0) / count,
      waiting: result.metrics.reduce((sum, item) => sum + item.waiting, 0) / count,
      normalized: result.metrics.reduce((sum, item) => sum + item.normalized, 0) / count,
    };
  });

  protected formatNumber(value: number) {
    return Number.isInteger(value) ? String(value) : value.toFixed(2);
  }

  protected selectAlgorithm(next: AlgorithmId) {
    this.algorithm.set(next);
    this.clearResult();
  }

  protected updateProcess(index: number, field: keyof ProcessInput, value: string | number) {
    const parsed = field === 'id' ? String(value).toUpperCase() : Number(value);
    this.processes.update((current) => current.map((process, processIndex) => processIndex === index ? { ...process, [field]: parsed } : process));
    this.clearResult();
  }

  protected updateQuantum(value: string | number) {
    this.config.update((current) => ({ ...current, quantum: Number(value) }));
    this.clearResult();
  }

  protected addProcess() {
    const used = new Set(this.processes().map((process) => process.id));
    let nextId = String.fromCharCode(65 + this.processes().length);
    while (used.has(nextId)) nextId = `P${used.size + 1}`;
    this.processes.update((current) => [...current, { id: nextId, arrival: 0, burst: 1 }]);
    this.clearResult();
  }

  protected removeProcess(index: number) {
    if (this.processes().length === 1) return;
    this.processes.update((current) => current.filter((_, processIndex) => processIndex !== index));
    this.clearResult();
  }

  protected restoreExample() {
    this.processes.set(SAMPLE_PROCESSES.map((process) => ({ ...process })));
    this.clearResult();
  }

  protected runSimulation() {
    const processes = this.processes();
    const ids = processes.map((process) => process.id.trim());
    if (ids.some((id) => !id) || new Set(ids).size !== ids.length) return this.error.set('Cada proceso debe tener un identificador único.');
    if (processes.some((process) => !Number.isInteger(process.arrival) || process.arrival < 0 || process.arrival > 20)) return this.error.set('El tiempo de llegada debe ser un entero entre 0 y 20.');
    if (processes.some((process) => !Number.isInteger(process.burst) || process.burst < 1 || process.burst > 20)) return this.error.set('El tiempo de CPU debe ser un entero entre 1 y 20.');
    if (this.algorithm() === 'rr' && (!Number.isInteger(this.config().quantum) || this.config().quantum < 1 || this.config().quantum > 20)) return this.error.set('El quantum debe ser un entero entre 1 y 20.');

    const nextResult = simulate(processes, this.algorithm(), this.config());
    this.error.set('');
    this.result.set(nextResult);
    this.activeStep.set(nextResult.totalTime - 1);
    this.isStepping.set(false);
  }

  protected showNextStep() {
    const result = this.result();
    if (!result) return;
    const wasStepping = this.isStepping();
    this.isStepping.set(true);
    this.activeStep.update((value) => wasStepping ? Math.min(result.totalTime - 1, value + 1) : 0);
  }

  protected showPreviousStep() {
    const result = this.result();
    if (!result) return;
    const wasStepping = this.isStepping();
    this.isStepping.set(true);
    this.activeStep.update((value) => wasStepping ? Math.max(0, value - 1) : Math.max(0, result.totalTime - 2));
  }

  protected clearResult() {
    this.result.set(null);
    this.activeStep.set(0);
    this.isStepping.set(false);
    this.error.set('');
  }

  protected processColor(index: number) {
    return this.colors[index % this.colors.length];
  }

  protected timelineWidth() {
    return Math.max(this.result()?.totalTime ?? 1, 1);
  }

  protected visibleProcessAt(time: number) {
    const timeline = this.result()?.timeline ?? [];
    return this.isStepping() && time > this.activeStep() ? null : timeline[time] ?? null;
  }

  protected cellIsCurrent(time: number, processId: string) {
    return this.isStepping() && time === this.activeStep() && this.visibleProcessAt(time) === processId;
  }

  protected processIndex(id: string | null) {
    return this.processes().findIndex((process) => process.id === id);
  }

  protected timeSlots() {
    return Array.from({ length: this.timelineWidth() }, (_, index) => index);
  }

  protected axisSlots() {
    return Array.from({ length: this.timelineWidth() + 1 }, (_, index) => index);
  }

  protected formatQueue(items: string[], priorities: Record<string, number> = {}) {
    return items.length ? items.map((id) => priorities[id] ? `${id}=${priorities[id]}` : id).join(' · ') : '—';
  }
}

```

## src/app/app.html

```html
<main class="app-shell">
  <header class="hero">
    <div class="eyebrow">SISTEMAS OPERATIVOS / ANGULAR 21</div>
    <h1>CPU Scheduler <em>Lab</em></h1>
    <p>Construye una planificación, observa cada decisión y compara sus resultados.</p>
  </header>

  <section class="algorithm-picker">
    <div class="section-heading"><span>01</span><div><h2>Elige un algoritmo</h2><p>La simulación se calcula por unidad de tiempo.</p></div></div>
    <div class="algorithm-grid">
      @for (id of algorithms; track id; let index = $index) {
        <button class="algorithm-card" [class.selected]="algorithm() === id" (click)="selectAlgorithm(id)">
          <span class="algorithm-number">0{{ index + 1 }}</span>
          <strong>{{ algorithmInfo[id].name }}</strong>
          <small>{{ algorithmInfo[id].short }}</small>
        </button>
      }
    </div>
  </section>

  <section class="workspace">
    <div class="section-heading"><span>02</span><div><h2>Configura los procesos</h2><p>{{ selected().description }}</p></div></div>
    <div class="workspace-grid">
      <div class="panel process-panel">
        <div class="panel-top"><div><span class="panel-kicker">ENTRADA</span><h3>Tabla de procesos</h3></div><button class="ghost-button" (click)="restoreExample()">Restaurar ejemplo</button></div>
        <div class="process-table-wrap">
          <table class="process-table"><thead><tr><th>Proceso</th><th>Llegada</th><th>CPU</th><th aria-label="Acciones"></th></tr></thead>
            <tbody>
              @for (process of processes(); track $index; let index = $index) {
                <tr>
                  <td><input class="id-input" maxlength="3" [ngModel]="process.id" (ngModelChange)="updateProcess(index, 'id', $event)"></td>
                  <td><input type="number" min="0" max="20" [ngModel]="process.arrival" (ngModelChange)="updateProcess(index, 'arrival', $event)"></td>
                  <td><input type="number" min="1" max="20" [ngModel]="process.burst" (ngModelChange)="updateProcess(index, 'burst', $event)"></td>
                  <td><button class="remove-button" (click)="removeProcess(index)" [attr.aria-label]="'Eliminar ' + process.id">×</button></td>
                </tr>
              }
            </tbody>
          </table>
        </div>
        <div class="panel-actions"><button class="add-button" (click)="addProcess()">+ Agregar proceso</button><span>{{ processes().length }} procesos cargados</span></div>
      </div>

      <div class="panel rules-panel"><span class="panel-kicker">REGLAS ACTIVAS</span><h3>{{ selected().name }}</h3><div class="rule-list">
        @if (algorithm() === 'rr') {
          <div><b>Quantum</b><label class="quantum-control"><input type="number" min="1" max="20" [ngModel]="config().quantum" (ngModelChange)="updateQuantum($event)"><span>unidades (1–20)</span></label></div>
          <div><b>Cola</b><span>Listos → Nuevos → Último</span></div>
        }
        @if (algorithm() === 'srr') {
          <div><b>Aceptados</b><span>Prioridad +1</span></div><div><b>Nuevos</b><span>Prioridad +2</span></div><div><b>Quantum</b><span>1 unidad fija</span></div>
        }
        @if (algorithm() === 'fcfs') { <div><b>Política</b><span>Orden de llegada</span></div> }
        @if (algorithm() === 'sjf') { <div><b>Política</b><span>Menor CPU disponible</span></div> }
        @if (algorithm() === 'srtf') { <div><b>Política</b><span>Menor CPU restante</span></div> }
      </div><p class="tip">Los colores se mantienen en el diagrama para seguir cada proceso.</p></div>
    </div>
    @if (error()) { <div class="error-message">{{ error() }}</div> }
    <button class="run-button" (click)="runSimulation()">Ejecutar simulación <span>→</span></button>
  </section>

  @if (result(); as simulation) {
    @if (currentStep(); as step) {
      <section class="results-section">
        <div class="section-heading"><span>03</span><div><h2>Observa la ejecución</h2><p>{{ step.explanation }}</p></div></div>
        <div class="simulation-controls">
          <div class="time-badge">
            @if (isStepping()) { <span>PASO <strong>{{ activeStep() + 1 }}</strong> / {{ simulation.totalTime }} · tiempo {{ activeStep() }}</span> }
            @else { <span>DIAGRAMA COMPLETO <strong>{{ simulation.totalTime }}</strong> pasos</span> }
          </div>
          <div class="control-buttons"><button (click)="showPreviousStep()">← Anterior</button><button (click)="showNextStep()">Siguiente →</button></div>
        </div>

        <div class="state-strip">
          @if (algorithm() === 'srr') {
            <div class="state-group"><span>Aceptados</span><strong>{{ formatQueue(step.accepted, step.priorities) }}</strong></div>
            <div class="state-group"><span>Nuevos</span><strong>{{ formatQueue(step.newQueue, step.priorities) }}</strong></div>
          } @else {
            <div class="state-group"><span>Listos</span><strong>{{ formatQueue(step.ready) }}</strong></div>
            <div class="state-group"><span>Nuevos</span><strong>{{ formatQueue(step.newArrivals) }}</strong></div>
            <div class="state-group"><span>Último ejecutado</span><strong>{{ formatQueue(step.lastExecuted ? [step.lastExecuted] : []) }}</strong></div>
          }
          <div class="current-process"><span>CPU</span><strong>{{ step.running ?? '—' }}</strong></div>
        </div>

        <div class="timeline-panel"><div class="timeline-scroll"><div class="timeline" [style.--time-count]="timelineWidth()">
          <div class="timeline-axis"><div class="row-label">Proceso</div>@for (time of axisSlots(); track time) { <span>{{ time }}</span> }</div>
          @for (process of processes(); track process.id; let index = $index) {
            <div class="timeline-row"><div class="row-label"><i [style.background]="processColor(index)"></i>{{ process.id }}</div>
              @for (time of timeSlots(); track time) {
                <div class="time-cell" [class.running]="visibleProcessAt(time) === process.id" [class.current-step]="cellIsCurrent(time, process.id)" [class.not-arrived]="time < process.arrival" [style.background]="visibleProcessAt(time) === process.id ? processColor(index) : null">{{ visibleProcessAt(time) === process.id ? process.id : '' }}</div>
              }
            </div>
          }
          <div class="timeline-row cpu-row"><div class="row-label">CPU</div>
            @for (time of timeSlots(); track time) {
              @let runningId = visibleProcessAt(time);
              <div class="time-cell cpu-cell" [class.current-step]="isStepping() && time === activeStep()" [style.background]="runningId ? processColor(processIndex(runningId)) : null">{{ runningId ?? '·' }}</div>
            }
          </div>
        </div></div></div>

        <div class="results-heading"><div><span class="panel-kicker">RESULTADOS</span><h3>Métricas de la ejecución</h3></div><button class="ghost-button" (click)="clearResult()">Editar entrada</button></div>
        <div class="metrics-table-wrap"><table class="metrics-table"><thead><tr><th>Proceso</th><th>Llegada</th><th>CPU</th><th>Final</th><th>Retorno</th><th>Espera</th><th title="Retorno / Tiempo CPU">T Promedio</th></tr></thead>
          <tbody>@for (metric of simulation.metrics; track metric.id; let index = $index) { <tr><td><span class="process-dot" [style.background]="processColor(index)">{{ metric.id }}</span></td><td>{{ metric.arrival }}</td><td>{{ metric.burst }}</td><td class="strong-cell">{{ metric.finish }}</td><td>{{ metric.turnaround }}</td><td>{{ metric.waiting }}</td><td>{{ formatNumber(metric.normalized) }}</td></tr> }</tbody>
          @if (averages(); as average) { <tfoot><tr><td colspan="3">Promedios</td><td>{{ formatNumber(average.cpu) }}</td><td>{{ formatNumber(average.turnaround) }}</td><td>{{ formatNumber(average.waiting) }}</td><td class="average-cell">{{ formatNumber(average.normalized) }}</td></tr></tfoot> }
        </table></div>
      </section>
    }
  }

  <footer>CPU Scheduler Lab · Angular 21 · simulación local para aprender planificación de procesos</footer>
</main>

```

## src/app/app.css

```css
:host { display: block; }
.app-shell { max-width: 1440px; margin: auto; padding: 42px clamp(20px, 5vw, 80px) 28px; }
.hero { border-bottom: 1px solid #cad6d3; padding-bottom: 44px; margin-bottom: 42px; }
.eyebrow, .panel-kicker { color: #df5a40; font: 500 11px 'DM Mono', monospace; letter-spacing: .13em; }
h1 { color: #102a43; font-size: clamp(42px, 7vw, 92px); letter-spacing: -.07em; line-height: .95; margin: 22px 0 18px; font-weight: 800; }
h1 em { color: #df5a40; font-style: normal; }
.hero p, .section-heading p { color: #617483; font-size: 15px; margin: 0; }
.section-heading { display: flex; gap: 18px; align-items: flex-start; margin-bottom: 24px; }
.section-heading > span { color: #df5a40; font: 500 12px 'DM Mono', monospace; padding-top: 5px; }
h2 { margin: 0 0 4px; color: #102a43; font-size: 22px; letter-spacing: -.04em; }
h3 { color: #102a43; margin: 7px 0 0; font-size: 19px; }
.algorithm-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }
.algorithm-card { text-align: left; background: #e8eeea; border: 1px solid transparent; min-height: 135px; padding: 17px; color: #17324d; transition: .2s ease; }
.algorithm-card:hover, .algorithm-card.selected { background: #17324d; color: white; transform: translateY(-3px); }
.algorithm-card.selected { border-color: #df5a40; box-shadow: 5px 5px 0 #df5a40; }
.algorithm-number { color: #df5a40; display: block; font: 500 11px 'DM Mono', monospace; margin-bottom: 35px; }
.algorithm-card strong { display: block; font-size: 16px; }
.algorithm-card small { opacity: .7; display: block; margin-top: 5px; }
.workspace, .results-section { max-width: 1280px; margin-top: 64px; margin-left: 30px; margin-right: auto; }
.workspace-grid { display: grid; grid-template-columns: 1.7fr 1fr; gap: 15px; }
.panel { background: white; border: 1px solid #d9e1dc; padding: 24px; }
.panel-top, .panel-actions, .results-heading, .simulation-controls { display: flex; justify-content: space-between; align-items: center; gap: 15px; }
.ghost-button { border: 0; background: transparent; color: #df5a40; font: 500 11px 'DM Mono', monospace; text-transform: uppercase; letter-spacing: .05em; padding: 8px 0; }
table { width: 100%; border-collapse: collapse; }
th { color: #71808a; font: 500 11px 'DM Mono', monospace; letter-spacing: .04em; text-align: left; text-transform: uppercase; }
.process-table-wrap, .metrics-table-wrap { overflow-x: auto; }
.process-table th { padding: 18px 10px 10px; border-bottom: 1px solid #d9e1dc; }
.process-table td { padding: 8px 10px; border-bottom: 1px solid #edf0ed; }
input { width: 70px; background: #f5f7f4; border: 1px solid transparent; color: #17324d; padding: 9px 10px; outline: none; }
input:focus { border-color: #df5a40; }
.id-input { font-weight: 800; width: 58px; }
.remove-button { border: 0; background: transparent; color: #a4b0b0; font-size: 22px; }
.remove-button:hover { color: #df5a40; }
.panel-actions { padding-top: 16px; color: #8a9695; font-size: 12px; }
.add-button { border: 0; background: #e9f0e9; color: #39725e; padding: 10px 14px; font-size: 12px; font-weight: 700; }
.rules-panel { background: #17324d; color: white; }
.rules-panel h3 { color: white; font-size: 29px; letter-spacing: -.05em; }
.rule-list { margin-top: 34px; border-top: 1px solid rgba(255,255,255,.18); }
.rule-list div { display: flex; justify-content: space-between; gap: 15px; padding: 14px 0; border-bottom: 1px solid rgba(255,255,255,.18); font-size: 13px; }
.rule-list span { color: #b9c8ce; text-align: right; }
.quantum-control { display: flex; align-items: center; gap: 8px; color: #b9c8ce; }
.quantum-control input { width: 58px; background: rgba(255,255,255,.12); border-color: rgba(255,255,255,.22); color: white; padding: 6px 8px; }
.tip { color: #b9c8ce; font-size: 12px; line-height: 1.6; margin-top: 30px; }
.error-message { background: #fff0ed; color: #b53c2a; padding: 12px 15px; margin-top: 16px; font-size: 13px; }
.run-button { margin-top: 18px; background: #df5a40; color: white; border: 0; padding: 16px 22px; font-weight: 800; font-size: 14px; box-shadow: 4px 4px 0 #b33f2a; }
.run-button span { font-size: 20px; margin-left: 20px; }
.simulation-controls { margin-bottom: 15px; }
.time-badge { color: #71808a; font: 500 11px 'DM Mono', monospace; letter-spacing: .05em; }
.time-badge strong { color: #df5a40; font-size: 18px; margin: 0 4px; }
.control-buttons { display: flex; gap: 8px; }
.control-buttons button { border: 1px solid #cad6d3; background: white; color: #17324d; padding: 9px 13px; font-size: 12px; }
.state-strip { display: grid; grid-template-columns: repeat(3, 1fr) 120px; gap: 1px; margin-bottom: 15px; background: #cbd7d3; border: 1px solid #cbd7d3; }
.state-group, .current-process { background: white; padding: 12px 15px; min-height: 66px; }
.state-group span, .current-process span { display: block; color: #8a9695; font: 500 10px 'DM Mono', monospace; text-transform: uppercase; margin-bottom: 9px; }
.state-group strong { font: 500 13px 'DM Mono', monospace; color: #17324d; }
.current-process { background: #df5a40; color: white; }
.current-process span { color: #ffe1da; }.current-process strong { font-size: 22px; }
.timeline-panel { background: white; border: 1px solid #d9e1dc; padding: 18px; overflow: hidden; }
.timeline-scroll { overflow-x: auto; padding-bottom: 5px; }.timeline { min-width: 750px; }
.timeline-axis, .timeline-row { display: grid; grid-template-columns: 100px repeat(var(--time-count, 20), 1fr); min-height: 34px; }
.timeline-axis { color: #8a9695; font: 10px 'DM Mono', monospace; }
.timeline-axis span { text-align: center; }.row-label { color: #17324d; font-size: 12px; display: flex; align-items: center; gap: 7px; }.row-label i, .process-dot { display: inline-flex; width: 20px; height: 20px; align-items: center; justify-content: center; border-radius: 50%; font-style: normal; font-size: 10px; font-weight: 800; }
.time-cell { border-left: 1px solid #edf0ed; min-height: 34px; display: flex; justify-content: center; align-items: center; color: #17324d; font: 500 11px 'DM Mono', monospace; }.time-cell.not-arrived { background: #fafbf9; }.time-cell.running { color: #17324d; font-weight: 800; }.time-cell.current-step { box-shadow: inset 0 0 0 3px #102a43; position: relative; z-index: 1; }.cpu-row { border-top: 2px solid #17324d; margin-top: 7px; padding-top: 4px; }.cpu-cell { min-height: 30px; color: #17324d; }
.results-heading { margin: 44px 0 15px; }.metrics-table th, .metrics-table td { padding: 11px 9px; border-bottom: 1px solid #d9e1dc; text-align: right; white-space: nowrap; }.metrics-table th:first-child, .metrics-table td:first-child { text-align: left; }.metrics-table th { background: #edf2ed; padding-top: 13px; padding-bottom: 13px; }.metrics-table tbody tr:hover { background: #f8faf7; }.strong-cell { font-weight: 800; }.average-cell { color: #df5a40; font-weight: 800; }.metrics-table tfoot td { background: #17324d; color: white; font-weight: 700; }.metrics-table tfoot .average-cell { color: #ff9a84; }.process-dot { margin-right: 8px; }
footer { border-top: 1px solid #cad6d3; color: #8a9695; font-size: 11px; margin-top: 70px; padding-top: 18px; }
@media (max-width: 1350px) { .workspace, .results-section { margin-left: 0; margin-right: 0; } }
@media (max-width: 900px) { .algorithm-grid { grid-template-columns: repeat(2, 1fr); }.workspace-grid { grid-template-columns: 1fr; }.state-strip { grid-template-columns: 1fr 1fr; }.current-process { grid-column: span 2; } }
@media (max-width: 560px) { .app-shell { padding: 28px 16px; }.algorithm-grid { grid-template-columns: 1fr; }.algorithm-card { min-height: 100px; }.algorithm-number { margin-bottom: 18px; }.panel { padding: 17px; }.panel-top { align-items: flex-start; flex-direction: column; }.section-heading { gap: 10px; }.state-strip { grid-template-columns: 1fr; }.current-process { grid-column: auto; }.simulation-controls { align-items: flex-start; flex-direction: column; } }

```

## src/styles.css

```css
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');

:root { font-family: 'Manrope', sans-serif; color: #17324d; background: #f5f7f4; font-synthesis: none; }
* { box-sizing: border-box; }
body { margin: 0; min-width: 320px; }
button, input { font: inherit; }
button { cursor: pointer; }

```

## src/app/scheduler.spec.ts

```ts
import { describe, expect, it } from 'vitest';
import { DEFAULT_CONFIG, SAMPLE_PROCESSES, simulate } from './scheduler';

describe('motor de planificación', () => {
  it('consume exactamente el CPU solicitado y alinea cada paso con el timeline', () => {
    for (const algorithm of ['fcfs', 'sjf', 'srtf', 'rr', 'srr'] as const) {
      const result = simulate(SAMPLE_PROCESSES, algorithm);
      expect(result.steps.every((step) => result.timeline[step.time] === step.running)).toBe(true);
      for (const process of SAMPLE_PROCESSES) {
        expect(result.timeline.filter((id) => id === process.id)).toHaveLength(process.burst);
      }
      expect(result.metrics.every((metric) => metric.waiting >= 0)).toBe(true);
    }
  });

  it('cambia la secuencia de Round Robin cuando cambia el quantum', () => {
    const quantumOne = simulate(SAMPLE_PROCESSES, 'rr', { ...DEFAULT_CONFIG, quantum: 1 });
    const quantumTwo = simulate(SAMPLE_PROCESSES, 'rr', { ...DEFAULT_CONFIG, quantum: 2 });
    expect(quantumOne.timeline).not.toEqual(quantumTwo.timeline);
  });

  it('reproduce la secuencia reconstruida de Selfish Round Robin', () => {
    const result = simulate(SAMPLE_PROCESSES, 'srr');
    expect(result.timeline.join('')).toBe('CCCACBBBBDBDDFFFFEEG');
    expect(Object.fromEntries(result.metrics.map((metric) => [metric.id, metric.finish]))).toEqual({
      A: 4, B: 11, C: 5, D: 13, E: 19, F: 17, G: 20,
    });
  });
});

```

## src/app/app.spec.ts

```ts
import { TestBed } from '@angular/core/testing';
import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('should render title', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('CPU Scheduler');
  });
});

```
