# Feature: fuentes-multiples (ariadna)
Objective: Stage 1 ingests any set of source files (individual paths or whole folders, any format) as evidence, not only a Teams transcript.
Branch: `feat/fuentes-multiples` · Delivery: single-pr (push branch, ~300 lines) · Test runner: `python -m unittest discover -s tests`.

## Specs
- S1. The skill asks for sources: "que consulte, dame la o las rutas que debo checar si se quiere citar archivos individuales, si no, que si le doy la ruta de una carpeta, lea todos los archivos de esa carpeta." Folder → every file, recursive, skipping hidden and `~$` temp files.
- S2. "que pueda leer cualquier formato, que no se restringa a un txt." Text-like, `.vtt`, `.docx`, `.xlsx`, `.pptx` extracted by script; PDF and images read natively by Claude; unreadable binaries reported, never silently dropped.
- S3. "Pueden ser más que solo transcripciones": every source is evidence; facts cite their source file; what no source supports stays `[PENDIENTE]`.
- S4. Existing behavior kept: Teams option, confirmation data (duration, participants, topic) for transcripts, "la más reciente en Descargas" (assumption: kept via `--latest`).

## Tasks
- [x] T1 S1,S2,S4 — `scripts/extract_sources.py` (multi `--input`, recursive folders, `--latest`, consolidated `fuentes.md`) + tests · inline · RED 3 fail+4 err → GREEN 8/8, suite 32/32
- [x] T2 S1,S3 — `specs/stage-1-ingesta.md`, `SKILL.md`, rubric/spec/stage-4 wording, README · inline · smoke run on repo xlsx + docs/guia-reunion (docx, pdf, json) OK

Route evidence: inline — one understood change, no parallel units, no Writer trigger.

## Log
- L1 (2026-11-05, user): "Primero, que para sacar los casos de uso, pueda leer los archivos que quien use el comando considere necesarios para dar contexto. Y segundo, que pueda leer cualquier formato, que no se restringa a un txt."
- L2 (user): "Pueden ser más que solo transcripciones. Tambien quiero que consulte, dame la o las rutas que debo checar si se quiere citar archivos individuales, si no, que si le doy la ruta de una carpeta, lea todos los archivos de esa carpeta."
- L3 (user): "Si. cuando este listo, lo pusheas al git. Lanzalo con odd"
- L4: Discovery: the extractor already accepted `.txt/.vtt/.docx` but only one transcript (most recent in a folder). Renamed to `extract_sources.py`; consolidated text goes to `fuentes.md` (was `transcripcion.txt`).
