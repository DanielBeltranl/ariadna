# Script: build_propuesta.py (+ coe.py)

Genera la propuesta en formato SONDA (`.docx`) e imprime la tarjeta CoE. Ejemplo completo: `examples/propuesta.json`.

```text
python "<SKILL_DIR>/scripts/build_propuesta.py" --json "<propuesta.json>" --output "<Propuesta X.docx>"
```

## Contrato `propuesta.json`
| Campo | Tipo | Obligatorio | Contenido |
| :--- | :--- | :--- | :--- |
| `iniciativa` | texto | sí | Nomenclatura completa: `19-N1-COM-CL \| Nombre \| MON` |
| `torre`, `solicitante` | texto | no | Ausente → `[PENDIENTE]` |
| `sistemas` | lista de textos | no | |
| `autor` | texto | no | Ausente → `[Ingresar autor]` |
| `contexto` | texto | sí | Qué se hace hoy y qué función cumple en la operación |
| `objetivo_general` | texto | sí | |
| `objetivos_especificos` | lista de textos | sí | |
| `alcance` | lista de `{id, titulo, acotacion}` | sí | Casos VIABLES |
| `fuera_de_alcance` | lista de `{id, titulo, justificacion}` | sí | Casos DESCARTADOS |
| `observaciones` | lista de textos | sí | Prerrequisitos, accesos, conectividad, datos pendientes |
| `evaluacion_coe` | objeto | sí | Ver abajo |

## `evaluacion_coe`
- `volumen_mensual`, `tiempo_minutos_por_ejecucion`: número ≥ 0 o `null`. `pct_automatizacion`: número 0–100 o `null`. **Nunca asumir valores**.
- `impacto`, `riesgo`, `escalabilidad`, `alineamiento`, `complejidad`: entero 1–5 según `templates/rubrica_coe.md`, o `null` si la transcripción no da evidencia.
- `<dimension>_justificacion`: definición de la rúbrica aplicada + evidencia de la transcripción.
- La eficiencia NO se informa: la calcula `coe.py` desde las HH.

## Lo que hace el script
- `coe.py` calcula HH/mes, eficiencia por tramo, puntos por dimensión (complejidad resta), score final y prioridad (`≥3.5 Alta | 2.5–3.4 Media | <2.5 Baja`).
- Una dimensión sin dato dice "No hay suficientes datos para establecer una calificación certera" y el score final queda `[PENDIENTE]`.
- Secciones del documento: Contexto, Objetivos (general y específicos), Alcance, Fuera de alcance, Observaciones, Valorización CoE (incluye "Decisión tomada" y "Responsable definido" en blanco).
- Usa la plantilla SONDA en `scripts/sonda/` (copia sin cambios del generador de la skill `sonda-user-manual`).
- Errores (código 1): campo obligatorio ausente, score fuera de 1–5, número inválido, archivo abierto en Word.
