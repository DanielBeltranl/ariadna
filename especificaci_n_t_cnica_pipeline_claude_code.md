# PROPUESTA: PIPELINE DETERMINISTA DE ESTRUCTURACIÓN TÉCNICA Y GOBERNANZA CoE

> Estado: propuesta acordada, sin implementar. Base inicial generada externamente y ajustada; no se sigue al pie de la letra.
> Al implementar, esta propuesta se divide en 8 especificaciones: 4 por stage y 4 por script (ver sección 7).

## 1. CONTEXTO Y OBJETIVO
Equipo de operaciones TI (N1/N2) bajo gobernanza de un Centro de Excelencia (CoE). El pipeline corre en Claude Code y procesa transcripciones `.txt` de reuniones de levantamiento en Microsoft Teams para:

1. Extraer los hechos técnicos y descartar ruido conversacional.
2. Formular Casos de Uso preliminares con una acotación de viabilidad técnica de una línea.
3. Ofrecer una puerta de control para que el usuario elija los Casos de Uso viables.
4. Generar la propuesta (`.docx` formato SONDA), los casos de uso (`.xlsx`), las historias de usuario (`.xlsx`) y un diagrama de secuencia general editable (`.drawio`).
5. Calcular el score preliminar CoE y mostrarlo en terminal con un aviso de gobernanza.

El resultado es una **estructura inicial**: será revisada e intervenida por personas antes de ser definitiva.

---

## 2. PRINCIPIO RECTOR: EL LLM ARMA JSON, LOS SCRIPTS GENERAN ARCHIVOS
- El LLM solo extrae, sintetiza y escribe un JSON por artefacto.
- Cada archivo se genera con su script fijo, como si fuera una herramienta (estilo MCP): recibe un JSON, produce el archivo. El LLM nunca mira los ejemplos ni escribe código de generación en cada corrida.
- Resultado: mismo formato siempre y menor consumo de tokens.
- Ningún cálculo aritmético lo hace el LLM: score CoE, puntos por dimensión y HH los calcula `scripts/coe.py`.
- Patrón tomado de la skill `sonda-user-manual` (JSON → `build_manual.py` → `.docx` sobre plantilla SONDA).

---

## 3. RESTRICCIONES DE ENTORNO
- **Sistema operativo:** Windows (PowerShell). Rutas manejadas con `pathlib`.
- **Runtime:** Python 3.10+ con `openpyxl` y `python-docx`.
- **Aislamiento:** cada iniciativa vive en `docs\proyectos\<slug>\`.
- **Datos ausentes:** se marcan `[PENDIENTE]`; nunca se inventan.

---

## 4. ESTRUCTURA DEL REPOSITORIO

El repositorio ES la skill: se clona directo en `~/.claude/skills/evaluacion-proyectos/` (ver sección 11).

```text
evaluacion-proyectos/
├── SKILL.md                   # comando /evaluacion-proyectos + reglas del agente
├── requirements.txt           # openpyxl, python-docx
├── scripts/
│   ├── coe.py                 # cálculo CoE (único lugar con aritmética)
│   ├── build_propuesta.py     # propuesta.json  -> .docx SONDA
│   ├── build_casos_uso.py     # casos.json      -> .xlsx
│   ├── build_historias.py     # historias.json  -> .xlsx
│   ├── build_diagrama.py      # diagrama.json   -> .drawio
│   └── assets/
│       └── sonda-template.docx  # copiada desde la skill sonda-user-manual
└── templates/
    └── rubrica_coe.md
```

Salida por iniciativa en `docs\proyectos\<slug>\` del proyecto donde se ejecuta el comando (no dentro de la skill):
- `propuesta.json`, `casos.json`, `historias.json`, `diagrama.json`
- `Propuesta <Nombre iniciativa>.docx`
- `Casos de Uso <Nombre iniciativa>.xlsx`
- `Historias de Usuario <Nombre iniciativa>.xlsx`
- `Diagrama de Secuencia <Nombre iniciativa>.drawio`

No hay `CLAUDE.md` ni `AGENTS.md`: las reglas del agente viven dentro de `SKILL.md`, que es lo que Claude Code carga.

---

## 5. STAGES DEL PIPELINE (comando `/evaluacion-proyectos`)
El comando recibe su entrada con `$ARGUMENTS` (no `$1`), porque rutas y nombres de reunión contienen espacios. Uso:

```text
/evaluacion-proyectos Levantamiento enlaces caídos
/evaluacion-proyectos C:\reuniones\levantamiento.txt
```

También se activa en lenguaje natural ("evalúa la reunión de enlaces caídos"), porque la skill se dispara por su descripción.

### Stage 1: Obtención de la transcripción e ingesta
1. Preguntar siempre el origen antes de hacer nada (no adivinar a partir del argumento):
   ```text
   ¿De dónde tomo la transcripción?
   [1] Buscar la reunión en Teams
   [2] Te dejo la transcripción aquí (ruta del archivo)
   ```
   - Opción 1: pedir el nombre de la reunión (o usar el argumento como nombre si vino) y buscarla en Microsoft Teams mediante el conector de Microsoft 365.
   - Opción 2: aceptar cualquiera de estas formas (o usar el argumento si vino):
     - **Ruta a un archivo** (`.txt`, `.vtt` o `.docx`): verificar que exista.
     - **Ruta a una carpeta** (ej. una carpeta que el usuario creó para transcripciones): tomar el archivo de transcripción más reciente de esa carpeta.
     - **"La más reciente en Descargas"**: igual que la carpeta, sobre `$HOME\Downloads`.
     - Cuando el usuario no dio el archivo directo y el agente lo encontró, mostrar datos de su contenido para confirmar antes de usarlo:
       ```text
       Encontré esta transcripción:
       - Archivo: transcripcion SAG.docx (modificado el 20/10/2026 15:05)
       - Duración aprox.: 28 min
       - Participantes: Nelssy Paredes, Nelson Silva, Daniel Beltrán
       - Tema (primeras intervenciones): "...verificar el sistema SAG para integrarlo a una automatización..."
       ¿Es la reunión que necesitas? (sí / no)
       ```
       Duración y participantes se leen de las marcas de tiempo y hablantes de la transcripción; si el formato no los trae, se omite esa línea. Con "no", ofrecer el siguiente archivo más reciente o pedir la ruta.
2. En la opción Teams, confirmar la reunión encontrada antes de seguir:
   ```text
   Encontré: «Levantamiento enlaces caídos», sostenida el 20/12/2026.
   ¿Es la reunión que buscas? (sí / no)
   ```
   - Con "sí": descargar su transcripción y continuar.
   - Con "no": pedir un nombre más preciso.
   - Si hay varias coincidencias: listarlas numeradas (nombre + fecha) y pedir el número.
   - Si no hay conector, no hay acceso, la reunión no tiene transcripción o no se encuentra: informarlo y pedir la ruta del archivo de transcripción. El pipeline nunca inventa contenido.
3. Pedir la nomenclatura formal: `19-N1-COM-CL | Gestión Alerta Enlaces caídos | MON`.
4. Derivar el slug (`19-n1-com-cl`) y crear `docs\proyectos\<slug>\`; guardar ahí la transcripción usada como `transcripcion.txt` para trazabilidad.
5. Leer la transcripción descartando ruido y extraer hechos confirmados: torre, sistemas, qué se hace hoy y qué función cumple en la operación, volumen mensual, minutos por ejecución, riesgo/multas, conectividad, usuarios y accesos.
6. Listar Casos de Uso preliminares, cada uno con su acotación técnica de una línea y su módulo.

### Stage 2: Puerta de viabilidad
1. Mostrar la lista numerada de Casos de Uso con su acotación.
2. Esperar la selección del usuario (`1, 2` o `todos`). Es una pregunta en el chat, no un prompt de consola.
3. Seleccionados = `VIABLES`; el resto = `DESCARTADOS (FUERA DE ALCANCE)` con su justificación.

### Stage 3: Armado de JSON y generación
1. Escribir los 4 JSON según los contratos de la sección 6. Solo los casos viables generan casos de uso, historias y diagrama.
2. Invocar los 4 scripts. Si alguno termina con código distinto de 0, mostrar su `stderr` y detener.

### Stage 4: Cierre y valorización
1. `build_propuesta.py` imprime la tarjeta ASCII de valorización CoE directamente en `stdout`; el LLM solo la muestra, sin recalcular ni reformatear.
2. Listar los archivos generados.
3. Cerrar con el aviso de gobernanza: *"Estos cambios deben ser validados antes de darse por finalizados."*

---

## 6. SCRIPTS Y CONTRATOS

Reglas comunes: entrada `--json <ruta>` y `--output <ruta>`; error claro en `stderr` y código 1 ante JSON inválido o campos obligatorios faltantes; error claro si el archivo de salida está abierto en Excel/Word (Windows bloquea el guardado).

### 6.1. `scripts/coe.py` (módulo compartido)
- Fórmula: `(Impacto*0.30)+(Eficiencia*0.20)+(Riesgo*0.15)+(Escalabilidad*0.10)+(Alineamiento*0.10)-(Complejidad*0.15)`.
- Clasificación: `≥3.5 Alta | 2.5–3.4 Media | <2.5 Baja`.
- Calcula HH/mes = `volumen_mensual * minutos * (pct_automatizacion/100) / 60`; sin ninguno de los tres datos, HH = `null` (sin valor por defecto para `pct_automatizacion`).
- Eficiencia por tramo de HH: `>100 → 5`, `50–100 → 4`, `20–50 → 3`, `5–20 → 2`, `<5 → 1`.
- Scores cualitativos: entero 1–5 o `null`. Fuera de rango o tipo inválido → error.
- Si un score (o la eficiencia) es `null`: su detalle dice **"No hay suficientes datos para establecer una calificación certera"**, y el score final y la prioridad quedan `[PENDIENTE]`.
- Devuelve scores, puntos por dimensión (complejidad en negativo), score final y prioridad.

### 6.2. `scripts/build_propuesta.py` → `.docx` SONDA
Usa la plantilla SONDA y el mismo enfoque de bloques de `build_manual.py` de la skill `sonda-user-manual` (h1, h2, p, bullets, table, note; `**negrita**` en línea). Secciones, en orden:
1. **Contexto:** qué se hace hoy y qué función cumple en la operación, deducido de la reunión.
2. **Objetivo general.**
3. **Objetivos específicos.**
4. **Alcance:** casos de uso viables.
5. **Fuera de alcance:** casos descartados con su justificación.
6. **Observaciones:** prerrequisitos, accesos, conectividad, datos `[PENDIENTE]`.
7. **Valorización CoE:** tabla Dimensión / Score / Peso / Puntos / Justificación, score final, prioridad, métricas (volumen, minutos, % automatización, HH/mes). Campos **Decisión tomada** y **Responsable definido** en blanco (los define el comité).

`propuesta.json` (forma):
```json
{
  "iniciativa": "19-N1-COM-CL | Gestión Alerta Enlaces caídos | MON",
  "torre": "", "solicitante": "", "sistemas": [""],
  "contexto": "",
  "objetivo_general": "",
  "objetivos_especificos": [""],
  "alcance": [{"id": "UC-01", "titulo": "", "acotacion": ""}],
  "fuera_de_alcance": [{"id": "UC-03", "titulo": "", "justificacion": ""}],
  "observaciones": [""],
  "evaluacion_coe": {
    "volumen_mensual": null, "tiempo_minutos_por_ejecucion": null, "pct_automatizacion": null,
    "impacto": 4, "impacto_justificacion": "",
    "riesgo": null, "riesgo_justificacion": "",
    "escalabilidad": 3, "escalabilidad_justificacion": "",
    "alineamiento": 3, "alineamiento_justificacion": "",
    "complejidad": 2, "complejidad_justificacion": ""
  }
}
```
Cada justificación cita la definición de `templates/rubrica_coe.md` aplicada y la evidencia de la transcripción.

### 6.3. `scripts/build_casos_uso.py` → `.xlsx`
Formato según `Casos de uso ejemplo.xlsx`:
- Una hoja por módulo.
- Columnas: **ID | Caso de Uso | Actor | Precondiciones | Flujo de Pasos | Resultado Esperado**.
- IDs `UC-01`, `UC-02`…; pasos numerados en una sola celda, separados por línea en blanco (`1. …\n\n2. …`); texto con ajuste de línea.

`casos.json`: `{"iniciativa": "", "casos": [{"modulo": "", "id": "UC-01", "titulo": "", "actor": "", "precondiciones": "", "pasos": [""], "resultado": ""}]}`

### 6.4. `scripts/build_historias.py` → `.xlsx`
Formato según `Historias de usuario ejemplo.xlsx`:
- Una hoja por módulo.
- Columnas: **N° | Nombre | Descripción | Criterios de Aceptación**; cabecera con relleno `A4C2F4`.
- Numeración `1.0`, `2.0`…; descripción "Como <rol>, quiero <acción> para <beneficio>"; criterios numerados separados por línea en blanco.

`historias.json`: `{"iniciativa": "", "historias": [{"modulo": "", "nombre": "", "rol": "", "accion": "", "beneficio": "", "criterios": [""]}]}`

### 6.5. `scripts/build_diagrama.py` → `.drawio`
- Un único diagrama de secuencia general de la iniciativa (solo casos viables), editable en draw.io.
- XML `mxfile` sin comprimir. El script calcula posiciones con cuadrícula fija: participantes en columnas, líneas de vida verticales, mensajes como flechas en orden descendente; las respuestas en línea punteada.

`diagrama.json`: `{"titulo": "", "participantes": ["Operador N1", "Script", "Zabbix"], "mensajes": [{"de": "Operador N1", "a": "Script", "texto": "", "respuesta": false}]}`

---

## 7. ESPECIFICACIONES A GENERAR EN LA IMPLEMENTACIÓN (8)
| # | Archivo | Contenido |
| :--- | :--- | :--- |
| 1 | `stage-1-ingesta.md` | Sección 5, Stage 1 |
| 2 | `stage-2-viabilidad.md` | Sección 5, Stage 2 |
| 3 | `stage-3-json-y-generacion.md` | Sección 5, Stage 3 |
| 4 | `stage-4-cierre.md` | Sección 5, Stage 4 |
| 5 | `script-propuesta.md` | Secciones 6.1 y 6.2 |
| 6 | `script-casos-uso.md` | Sección 6.3 |
| 7 | `script-historias.md` | Sección 6.4 |
| 8 | `script-diagrama.md` | Sección 6.5 |

---

## 8. RÚBRICA CoE (`templates/rubrica_coe.md`)
Reglas del comité: evaluar con datos, no percepciones; escala 1–5; priorizar Impacto + Reutilización; evitar duplicidad.

| Dimensión | Peso | 5 | 4 | 3 | 2 | 1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Impacto en Negocio (clientes, SLA, continuidad) | 30% | Crítico: recuperación de servicios críticos (red, core bancario, datacenter) | Alto: gestión de incidentes prioritarios | Medio: tareas operativas internas | Bajo: tareas administrativas | Muy bajo: mejora menor sin impacto visible |
| Eficiencia Operativa (calculada) | 20% | >100 hrs/mes | 50–100 hrs/mes | 20–50 hrs/mes | 5–20 hrs/mes | <5 hrs/mes |
| Riesgo Operativo (riesgo de NO automatizar) | 15% | Alto: procesos manuales críticos (red, accesos privilegiados) | Relevante: cambios manuales en producción | Moderado: tareas repetitivas con posible error | Bajo: actividades simples | Sin riesgo relevante |
| Escalabilidad / Reutilización | 10% | Multi-región: todas las filiales | Multi-país | Multi-equipo dentro de un país | Uso limitado: un área | Uso único |
| Alineamiento Estratégico (cloud, DevOps, seguridad, AIOps) | 10% | Proyecto clave del plan TI | Apoya iniciativas relevantes | Aporta indirectamente | Poco alineado | Iniciativa aislada |
| Complejidad Técnica (RESTA) | 15% | Muy alta: integraciones múltiples, APIs no disponibles | Alta: varias dependencias | Media: desarrollo estándar | Baja: automatización simple | Muy baja: script directo sin dependencias |

Preguntas clave: ¿Impacta al negocio? ¿Cuánto ahorro genera? ¿Se reutiliza? ¿Qué pasa si no se hace?

---

## 9. REGLAS DEL AGENTE (dentro de `SKILL.md`)
- Los scripts se invocan por la ruta de la skill (`~/.claude/skills/evaluacion-proyectos/scripts/...`), nunca relativa al proyecto.
- Rol: Tech Lead Senior / Arquitecto de Automatización TI; precisión sobre extensión.
- PowerShell y rutas seguras en Windows.
- No inventar dependencias ni accesos; lo ausente es `[PENDIENTE]`.
- Nunca generar código para crear `.docx`, `.xlsx` o `.drawio`: siempre invocar los scripts de `scripts/`.
- Cada iniciativa aislada en `docs\proyectos\<slug>\`.
- La estructuración solo corre vía `/evaluacion-proyectos <nombre de reunión o ruta>`.

---

## 10. FUERA DE ALCANCE DE ESTA FASE
- Detección de duplicidad contra iniciativas existentes en `docs\proyectos\`.
- Diagramas por caso de uso (solo uno general).
- Llenado de "Decisión tomada" y "Responsable definido" (los define el comité).

---

## 11. INSTALACIÓN Y DISTRIBUCIÓN
**Instalación (una vez por usuario, en PowerShell):**
```powershell
git clone <url-del-repo> "$HOME\.claude\skills\evaluacion-proyectos"
pip install -r "$HOME\.claude\skills\evaluacion-proyectos\requirements.txt"
```
Queda disponible en cualquier proyecto como `/evaluacion-proyectos`, sin prefijo. No requiere instructivo para el agente: Claude Code descubre la skill solo.

**Actualización:** `git pull` dentro de esa carpeta.

**Prerrequisitos:**
- Python 3.10+ en el `PATH`.
- Conector Microsoft 365 autenticado en Claude Code para buscar reuniones en Teams (opcional: sin él se usa la ruta del archivo).

**Alternativa descartada: plugin de Claude Code.** Gestiona actualizaciones por versión, pero todo comando de plugin lleva prefijo obligatorio (`/<plugin>:<skill>`, verificado en la documentación oficial), lo que choca con la exigencia de un comando corto.

**Riesgos a verificar al implementar (antes de construir el resto):**
1. **Verificado el 30/10/2026:** el conector Microsoft 365 SÍ encuentra reuniones en el calendario (nombre, fecha, organizador). La descarga de la transcripción está BLOQUEADA en el tenant de Sonda: Microsoft Graph responde `GraphAccessToTranscriptsDisabled` (deshabilitado por un administrador de Teams). En reuniones organizadas por otra persona, además responde "User does not have access to lookup meeting". Mientras TI no lo habilite, la opción Teams solo sirve para identificar la reunión y aprovechar los datos del calendario (nomenclatura CoE en el asunto, participantes, descripción); ante este error, el pipeline debe informarlo en una línea y pasar a la opción 2. Se descartó leer la transcripción desde OneDrive/SharePoint por la gestión de accesos que implica.
2. Que la skill pueda referenciar sus scripts por una ruta estable en Windows.
