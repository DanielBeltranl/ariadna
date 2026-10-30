# Rúbrica de Evaluación – CoE Automatización TI

## Reglas del comité
- Evaluar con datos, no percepciones: cada score cita la evidencia de la transcripción. Sin evidencia → `null`.
- Escala 1–5.
- Priorizar Impacto + Reutilización.
- Evitar duplicidad.

Fórmula (la ejecuta `scripts/coe.py`, nunca el agente):
`(Impacto*0.30)+(Eficiencia*0.20)+(Riesgo*0.15)+(Escalabilidad*0.10)+(Alineamiento*0.10)-(Complejidad*0.15)`
Clasificación: `≥3.5 Alta | 2.5–3.4 Media | <2.5 Baja`

Preguntas clave: ¿Impacta al negocio? ¿Cuánto ahorro genera? ¿Se reutiliza? ¿Qué pasa si no se hace?

## 1. Impacto en Negocio (30%)
Cuánto impacta en la operación del negocio, clientes, SLA, continuidad o reputación. ¿Afecta directamente a clientes? ¿Impacta un proceso crítico? ¿Reduce riesgo operacional relevante?

| Score | Definición | Ejemplo |
| :--- | :--- | :--- |
| 5 | Crítico | Recuperación de servicios críticos (caída de red, core bancario, datacenter) |
| 4 | Alto | Gestión de incidentes prioritarios |
| 3 | Medio | Tareas operativas internas |
| 2 | Bajo | Tareas administrativas |
| 1 | Muy bajo | Mejora menor sin impacto visible |

## 2. Eficiencia Operativa (20%) — la calcula el script
| Score | HH ahorradas | Ejemplo |
| :--- | :--- | :--- |
| 5 | >100 hrs/mes | Provisión masiva de servidores |
| 4 | 50–100 hrs/mes | Monitoreo y alertas |
| 3 | 20–50 hrs/mes | Scripts de mantenimiento |
| 2 | 5–20 hrs/mes | Automatización puntual |
| 1 | <5 hrs/mes | Bajo impacto en eficiencia |

## 3. Riesgo Operativo (15%)
Riesgo de NO automatizar (errores humanos, fallas, incumplimiento, dependencia manual). Más riesgo = score más alto = más prioridad. ¿Es propenso a errores? ¿Impacta cumplimiento/auditoría? ¿Depende de personas clave?

| Score | Definición | Ejemplo |
| :--- | :--- | :--- |
| 5 | Alto riesgo | Procesos manuales críticos (configuración de red, accesos privilegiados) |
| 4 | Riesgo relevante | Cambios manuales en producción |
| 3 | Riesgo moderado | Tareas repetitivas con posible error |
| 2 | Riesgo bajo | Actividades simples |
| 1 | Sin riesgo relevante | No afecta operación |

## 4. Escalabilidad / Reutilización (10%)
Potencial de reutilizar en otras filiales, clientes o procesos. ¿Aplica a varios países? ¿Puede ser estándar o componente reusable?

| Score | Definición | Ejemplo |
| :--- | :--- | :--- |
| 5 | Multi-región | Reutilizable en todas las filiales (ej: onboarding servidores) |
| 4 | Multi-país | Aplicable en varios países |
| 3 | Multi-equipo | Reutilizable dentro de un país |
| 2 | Uso limitado | Solo un área |
| 1 | Uso único | Caso puntual |

## 5. Alineamiento Estratégico (10%)
Alineación con objetivos estratégicos (cloud, DevOps, seguridad, eficiencia, AIOps). ¿Está en el roadmap TI? ¿Aporta a iniciativas regionales? ¿Apoya la transformación digital?

| Score | Definición | Ejemplo |
| :--- | :--- | :--- |
| 5 | Totalmente alineado | Proyecto clave del plan estratégico TI |
| 4 | Alto alineamiento | Apoya iniciativas relevantes |
| 3 | Parcial | Aporta indirectamente |
| 2 | Bajo | Poco alineado |
| 1 | No alineado | Iniciativa aislada |

## 6. Complejidad Técnica (15%) — RESTA
Dificultad de implementar los casos VIABLES: nº de sistemas, dependencias externas, madurez tecnológica, tiempo estimado.

| Score | Definición | Ejemplo |
| :--- | :--- | :--- |
| 5 | Muy alta | Integraciones múltiples, APIs no disponibles, alta incertidumbre |
| 4 | Alta | Varias dependencias técnicas |
| 3 | Media | Desarrollo estándar |
| 2 | Baja | Automatización simple |
| 1 | Muy baja | Script directo sin dependencias |
