"""List what is still open in an initiative folder, so the agent can ask it one question at a time.

Usage: python pendientes.py --dir "docs/proyectos/<slug>"
Prints {"pendientes": [{"archivo", "campo", "pregunta"}, ...]}.
"""
import argparse
import json
from pathlib import Path

import coe
from spec_io import fail, utf8_console

ARIADNA_FILES = ("propuesta.json", "automatizabilidad.json", "casos.json", "historias.json", "diagrama.json")
METRICS = {
    "volumen_mensual": "¿Cuántas veces al mes se ejecuta el proceso?",
    "tiempo_minutos_por_ejecucion": "¿Cuántos minutos toma cada ejecución manual?",
    "pct_automatizacion": "¿Qué porcentaje del proceso se puede automatizar?",
}
HEADER = {"torre": "¿A qué torre pertenece la iniciativa?", "solicitante": "¿Quién es el solicitante de la iniciativa?"}


def pending_texts(value, path=""):
    """Yield (path, text) for every string holding the [PENDIENTE] marker."""
    if isinstance(value, str) and coe.PENDING in value:
        yield path, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from pending_texts(item, f"{path}.{key}" if path else key)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from pending_texts(item, f"{path}[{i}]")


def from_proposal(spec):
    for key, question in HEADER.items():
        if not spec.get(key):
            yield key, question
    data = spec.get("evaluacion_coe") or {}
    for key, question in METRICS.items():
        if data.get(key) is None:
            yield f"evaluacion_coe.{key}", question
    for key, name, _ in coe.DIMENSIONS:
        if key != "eficiencia" and data.get(key) is None:  # eficiencia is computed from the metrics
            yield f"evaluacion_coe.{key}", f"¿Qué evidencia permite calificar {name} de 1 a 5 (rúbrica CoE)?"


def from_automatability(spec):
    for caso in spec.get("casos") or []:
        for key, item in (caso.get("criterios") or {}).items():
            if isinstance(item, dict) and str(item.get("pregunta") or "").strip():
                yield f"{caso.get('id')}.{key}", item["pregunta"]


def main():
    utf8_console()
    parser = argparse.ArgumentParser(description="Lista los pendientes de una iniciativa")
    parser.add_argument("--dir", required=True, help="Carpeta docs/proyectos/<slug>")
    folder = Path(parser.parse_args().dir)

    files = [folder / name for name in ARIADNA_FILES if (folder / name).is_file()]
    if not files:
        fail(f"No hay JSON de Ariadna en {folder}: no hay nada que completar")

    items = []
    for path in files:
        try:
            spec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as err:
            fail(f"No se pudo leer {path}: {err}")
        found = list(pending_texts(spec))
        if path.name == "propuesta.json":
            found = list(from_proposal(spec)) + [(p, f"Completar: «{t}»") for p, t in found]
        elif path.name == "automatizabilidad.json":
            found = list(from_automatability(spec))  # its gaps are the open questions, not markers
        else:
            found = [(p, f"Completar: «{t}»") for p, t in found]
        items += [{"archivo": path.name, "campo": field, "pregunta": question} for field, question in found]

    print(json.dumps({"pendientes": items}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
