# Feature: evaluacion-proyectos (skill de Claude Code)
Objective: implement the `/evaluacion-proyectos` skill defined in `especificaci_n_t_cnica_pipeline_claude_code.md`.
Branch: `feat/evaluacion-proyectos` · Delivery: single-pr (new repo, no remote yet) · Test runner: `python -m unittest discover -s tests` (stdlib; pytest not installed).

## Specs
- S1. Command `/evaluacion-proyectos` + transcript path/meeting name; user-level skill installed with `git clone` into `~/.claude/skills/evaluacion-proyectos` ("tiene que ser algo corto como /evaluacion-proyectos + ruta de la transcripcion").
- S2. Stage 1 asks the source first: "quieres que busque en teams o me dejas la transcripcion aca??". Teams: confirm "reunion ... sostenida el 20/12/2026, es la reunion que buscas" (transcript download is blocked by tenant → fall back to file). File: path, folder, or most recent in Downloads; when found (not given directly) "que le muesre un par de datos para confirmar que estas en el archivo que necesita".
- S3. Stage 2 viability gate; Stage 3 JSON + scripts; Stage 4 CoE card + governance notice. One md spec per stage and per script ("seria un md para cada script que genera los archivos").
- S4. Scripts receive a JSON and generate the file "Asi salen siempre con el mimso formato y gasta menos tokens"; the LLM never writes generation code.
- S5. Propuesta in SONDA style with "Objetivo general, objetivo especifico, alcance, fuera de alcance, observaciones y al inicio un contexto de que se hace hoy y que funcion cumple en la operacion" + CoE valuation; "Decisión tomada"/"Responsable" blank.
- S6. Casos de uso `.xlsx` following `Casos de uso ejemplo.xlsx`; Historias `.xlsx` following `Historias de usuario ejemplo.xlsx`.
- S7. Sequence diagram as draw.io XML, "Un unico diagrama general".
- S8. CoE: official rubric and formula; missing data → "No hay suficientes datos para establecer una calificación certera" and final score `[PENDIENTE]`; all arithmetic in Python.

## Tasks
- [ ] T1 S8 — `scripts/coe.py` + tests · inline
- [ ] T2 S4,S5,S8 — `scripts/build_propuesta.py` reusing the SONDA builder/template + tests · inline
- [ ] T3 S4,S6 — `scripts/build_casos_uso.py`, `scripts/build_historias.py` + tests · inline
- [ ] T4 S4,S7 — `scripts/build_diagrama.py` + tests · inline
- [ ] T5 S1-S3 — `SKILL.md`, `templates/rubrica_coe.md`, 8 md specs, `requirements.txt`, README · inline
- [ ] T6 all — end-to-end run with sample JSON, open-check outputs · inline

Route evidence: all inline — units are sequential and share conventions; no Writer trigger (no parallel independent units launched together, context well below backstop).

## Log
- L1 (2026-10-30, user): "Estamos para que con odd ejecutes todo? parece harto, pero creo que se puede hacer en una run porque es mas texto que otra cosa" → "Si, inicializa".
- L2: Discovery: SONDA `build_manual.py` is stdlib-only (zipfile), so `python-docx` is not needed; only `openpyxl`. pytest absent → unittest.
- L3: Repo initialized at baseline `fddf9f4` on `main`; work on `feat/evaluacion-proyectos`.
