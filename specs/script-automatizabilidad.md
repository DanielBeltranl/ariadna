# Script: build_automatizabilidad.py

Genera el análisis de automatizabilidad en formato SONDA (`.docx`) e imprime un veredicto por caso de uso. Ejemplo completo: `examples/automatizabilidad.json`. Criterios: `templates/criterios_automatizabilidad.md`.

```text
python "<SKILL_DIR>/scripts/build_automatizabilidad.py" --json "<automatizabilidad.json>" --output "<Analisis de Automatizabilidad X.docx>"
```

## Contrato `automatizabilidad.json`
`{"iniciativa": "...", "autor": "...", "casos": [ ... ]}` (`autor` opcional; `version` y `cambio` opcionales, por defecto `1.0` y `Creación del documento`), cada caso con:

| Campo | Contenido |
| :--- | :--- |
| `id`, `titulo` | Mismos IDs y títulos de los casos de uso preliminares |
| `criterios` | Objeto con las 9 claves: `reglas`, `entradas`, `estabilidad`, `volumen`, `excepciones`, `sistemas`, `optimizacion`, `medible`, `riesgo` |

Cada criterio: `{"estado": "cumple|parcial|no_cumple|sin_evidencia", "evidencia": "... [fuente: X]", "pregunta": "..."}` (`pregunta` obligatoria si el estado es `sin_evidencia`; opcional en los demás).

## Lo que hace el script
- Calcula el veredicto y el score (0–100, nivel Alto/Medio/Bajo) con las reglas fijas de `templates/criterios_automatizabilidad.md`.
- Secciones: Criterios de evaluación, Resumen (veredicto y score por caso) y una sección por caso con estado y evidencia de cada criterio, observación si `sistemas` no cumple, y preguntas pendientes.
- Imprime una línea por caso: `UC-01: <veredicto> (score <N>/100, <nivel>) — <motivo>`.
- Errores (código 1): campo obligatorio ausente, criterio faltante, estado inválido, `sin_evidencia` sin pregunta, archivo abierto en Word.
