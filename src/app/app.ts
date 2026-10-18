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
