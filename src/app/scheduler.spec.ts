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
