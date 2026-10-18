# CPU Scheduler Lab - Angular 21

Versión independiente del simulador de planificación de procesos construida
con Angular 21 y TypeScript.

## Incluye

- FCFS.
- SJF.
- SRTF.
- Round Robin con quantum configurable entre `1` y `20`.
- Selfish Round Robin con grupos `Aceptados` y `Nuevos`.
- Tabla editable de procesos con ejemplo A-G.
- Diagrama de CPU completo al ejecutar.
- Recorrido paso a paso con `Siguiente` y `Anterior`.
- Métricas de final, retorno, espera y T Promedio.

## Funcionamiento de los algoritmos

### FCFS - First Come, First Served

Primero en llegar, primero en ser atendido.

- Ordena los procesos por tiempo de llegada.
- Ejecuta el primer proceso disponible.
- El proceso permanece en la CPU hasta terminar.
- No es expropiativo: un proceso nuevo no interrumpe al actual.

### SJF - Shortest Job First

Selecciona el proceso disponible con menor tiempo total de CPU.

- Revisa los procesos que ya llegaron.
- Elige la ráfaga de CPU más corta.
- Ejecuta el proceso hasta terminar.
- No es expropiativo.

### SRTF - Shortest Remaining Time First

Selecciona el proceso con menor tiempo de CPU restante.

- Revisa la selección en cada unidad de tiempo.
- Descuenta una unidad del proceso ejecutado.
- Puede interrumpir el proceso actual.
- Si llega un proceso con menor tiempo restante, la CPU cambia a ese proceso.

### Round Robin

Reparte la CPU mediante turnos de duración limitada.

- Utiliza un quantum configurable entre `1` y `20`.
- Los procesos esperan en una cola circular.
- Si un proceso no termina dentro de su quantum, vuelve al final de la cola.
- La simulación muestra los grupos `Listos`, `Nuevos` y `Último ejecutado`.
- Es expropiativo por finalización del quantum.

El orden utilizado para los procesos nuevos es:

```text
Listos -> Nuevos -> Último ejecutado
```

### Selfish Round Robin

Combina prioridades crecientes con turnos de Round Robin.

- Mantiene los grupos `Aceptados` y `Nuevos`.
- Los procesos aceptados aumentan su prioridad en `+1` por unidad.
- Los procesos nuevos aumentan su prioridad en `+2` por unidad.
- Un proceso nuevo pasa a aceptados cuando alcanza la prioridad mínima aceptada.
- Los aceptados se ejecutan con quantum fijo de `1`.
- La simulación muestra las prioridades de cada grupo.

La variante implementada reproduce la lógica reconstruida del material de clase.
La tabla original contenía algunos resultados inconsistentes, por lo que el
programa evita esperas negativas y calcula nuevamente las métricas a partir del
recorrido real de la CPU.

## Métricas calculadas

```text
T Final = último instante de ejecución + 1
T Retorno = T Final - T Llegada
T Espera = T Retorno - Tiempo CPU
T Promedio = T Retorno / Tiempo CPU
```

La columna `T Promedio` representa técnicamente el retorno normalizado.

## Instalación

Requiere Node.js compatible con Angular 21. En este proyecto se utilizó Node
`22.22.2`.

```bash
npm install --legacy-peer-deps
```

## Desarrollo

```bash
npm start
```

Abrir `http://localhost:4200/`.

## Build de producción

```bash
npm run build
```

La salida se genera en `dist/proyectoSO/`.

## Pruebas

```bash
npm test -- --watch=false
```

Las pruebas verifican el consumo exacto de CPU, la correspondencia entre pasos
y diagrama, Round Robin y Selfish Round Robin.

## Documentación de entrega

- `docs/DOCUMENTACION.html`: documento visual para abrir en el navegador o Word e imprimir a PDF.
- `docs/DOCUMENTACION.md`: versión editable en Markdown.
- `docs/SCRIPT-FUENTE.md`: código fuente principal en un documento único.
- `docs/assets/`: capturas reales de las pantallas del sistema.

Para regenerar el documento del código fuente:

```bash
npm run export:source
```

## Estructura sencilla

```text
src/app/scheduler.ts  # Algoritmos, trazas y métricas
src/app/app.ts        # Estado de la interfaz Angular
src/app/app.html      # Formulario, diagrama y resultados
src/app/app.css       # Diseño visual
```
