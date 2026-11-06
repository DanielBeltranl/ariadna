# Criterios de Automatizabilidad

Responden si un caso de uso **se puede** automatizar. La rúbrica CoE (`rubrica_coe.md`) responde si **conviene**: no mezclar.

## Reglas
- Evalúa cada caso de uso con los 9 criterios, uno por uno, solo con evidencia de las fuentes. Cita la fuente: `[fuente: <archivo>]`.
- Estados: `cumple`, `parcial`, `no_cumple`, `sin_evidencia`. Sin evidencia nunca es `cumple`.
- Si un criterio no puede responderse (`sin_evidencia`), escribe **obligatoriamente** en `pregunta` lo que hay que preguntar en la próxima reunión para responderlo; el script rechaza el JSON si falta. En `parcial`, agrega la pregunta que cerraría la brecha.
- El veredicto lo calcula `build_automatizabilidad.py`; nunca lo decidas tú.

Prueba práctica: si el proceso se puede dibujar como diagrama de flujo sin cajas que digan «depende» o «lo ve Juan», está cerca de ser automatizable.

## Criterios
| Clave | Criterio | `cumple` cuando | `no_cumple` cuando |
| :--- | :--- | :--- | :--- |
| `reglas` | Reglas claras y explícitas **(eliminatorio)** | Las decisiones se expresan como «si pasa X, hago Y». | Depende del criterio o la intuición de alguien y nadie explica cómo decide. Lo que no se puede describir no se puede automatizar. |
| `entradas` | Entradas estructuradas y predecibles **(eliminatorio)** | Los datos llegan en formato consistente (formularios, campos definidos, archivos con la misma estructura). | Cada caso llega distinto y no hay patrón. Si llegan en formato libre pero con patrón (correos, PDF), es `parcial`: requiere extracción previa, a menudo con IA. |
| `estabilidad` | Estabilidad **(eliminatorio)** | El proceso no cambia con frecuencia. | El proceso todavía se está definiendo o cambia cada mes: generaría retrabajo constante. |
| `volumen` | Volumen y frecuencia suficientes | Se repite lo bastante para que el ahorro justifique construir y mantener. | Ocurre muy pocas veces (por ejemplo, dos veces al año). |
| `excepciones` | Pocas excepciones o bien acotadas **(eliminatorio)** | El 80–90% de los casos sigue el camino feliz y las excepciones se identifican para derivarlas a una persona. | Se nombran o detectan múltiples excepciones que no se pueden identificar de antemano. |
| `sistemas` | Sistemas accesibles | Hay API, base de datos, exportación o conector. | Todo vive en papel o en sistemas cerrados. **No elimina**: el equipo puede proponer una vía de integración; el documento lo deja como observación. |
| `optimizacion` | Proceso optimizado | No hay pasos innecesarios, aprobaciones redundantes ni duplicidades. | Hay pasos que sobran: automatizar un proceso malo solo produce errores más rápido. Recomienda eliminarlos antes. |
| `medible` | Resultado medible y verificable | Se puede saber si salió bien (registro creado, monto que cuadra, correo enviado). | No hay forma de comprobar el resultado ni de detectar fallas. |
| `riesgo` | Riesgo controlado | Un error no tiene consecuencias graves ni irreversibles. | Un error es grave o irreversible (pagos, decisiones legales, salud, caída de servicio crítico): el veredicto pasa a «con revisión humana». |

Distinto de la rúbrica CoE: ahí más riesgo **sube la prioridad**; aquí un error grave **obliga a un punto de revisión humana**.

## Veredicto (lo calcula el script)
1. Algún eliminatorio en `no_cumple` → **No automatizable aún**.
2. Algún eliminatorio en `sin_evidencia` → **Por confirmar**.
3. `riesgo` en `no_cumple` → **Automatizable con revisión humana**.
4. En otro caso → **Automatizable**.

## Score (lo calcula el script)
Cada criterio suma `cumple` 1, `parcial` 0,5, `no_cumple` y `sin_evidencia` 0; los eliminatorios pesan el doble (máximo 13 puntos). Score = puntos / 13 × 100. Nivel: ≥80 Alto, 50–79 Medio, <50 Bajo. El score dice qué tan cerca está el caso; el veredicto, si se puede automatizar.

La gobernanza (dueño del proceso automatizado) no se evalúa aquí: se define después, en el comité.
