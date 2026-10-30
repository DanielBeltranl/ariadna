"""Build the SONDA-format proposal (.docx) from propuesta.json and print the CoE card.

Usage: python build_propuesta.py --json propuesta.json --output "Propuesta X.docx"
Schema by example: examples/propuesta.json
"""
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "sonda"))

import build_manual  # noqa: E402  (vendored, unmodified copy of the sonda-user-manual generator)
import coe  # noqa: E402
from spec_io import check_items, fail, load_spec, parse_args, save, today  # noqa: E402
import json  # noqa: E402

REQUIRED = {
    "iniciativa": str,
    "contexto": str,
    "objetivo_general": str,
    "objetivos_especificos": list,
    "alcance": list,
    "fuera_de_alcance": list,
    "observaciones": list,
    "evaluacion_coe": dict,
}


def initiative_name(initiative):
    """'19-N1-COM-CL | Nombre | MON' -> 'Nombre'; any other text is used as is."""
    parts = [p.strip() for p in initiative.split("|")]
    return parts[1] if len(parts) >= 3 and parts[1] else initiative.strip()


def show(value):
    return coe.PENDING if value is None else str(value)


def body(spec, result):
    systems = ", ".join(spec.get("sistemas") or []) or coe.PENDING
    blocks = [
        {"h1": "Contexto"},
        {"p": spec["contexto"]},
        {"table": {"header": ["Atributo", "Detalle"], "widths": [1, 3], "rows": [
            ["Iniciativa", spec["iniciativa"]],
            ["Torre", spec.get("torre") or coe.PENDING],
            ["Solicitante", spec.get("solicitante") or coe.PENDING],
            ["Sistemas involucrados", systems],
        ]}},
        {"h1": "Objetivos"},
        {"h2": "Objetivo general"},
        {"p": spec["objetivo_general"]},
        {"h2": "Objetivos específicos"},
        {"bullets": spec["objetivos_especificos"] or [coe.PENDING]},
        {"h1": "Alcance"},
    ]
    if spec["alcance"]:
        blocks.append({"table": {"header": ["ID", "Caso de uso", "Acotación técnica"], "widths": [1, 3, 4],
                                 "rows": [[c["id"], c["titulo"], c.get("acotacion", "")] for c in spec["alcance"]]}})
    else:
        blocks.append({"p": "No se seleccionaron casos de uso viables."})
    blocks.append({"h1": "Fuera de alcance"})
    if spec["fuera_de_alcance"]:
        blocks.append({"table": {"header": ["ID", "Caso de uso", "Justificación"], "widths": [1, 3, 4],
                                 "rows": [[c["id"], c["titulo"], c.get("justificacion", "")] for c in spec["fuera_de_alcance"]]}})
    else:
        blocks.append({"p": "Todos los casos de uso identificados quedaron dentro del alcance."})
    blocks += [
        {"h1": "Observaciones"},
        {"bullets": spec["observaciones"]} if spec["observaciones"] else {"p": "Sin observaciones."},
        {"h1": "Valorización CoE"},
        {"p": "Evaluación preliminar según la rúbrica del CoE de Automatización TI. Es una estructura inicial que debe ser revisada por el comité."},
        {"table": {"header": ["Dimensión", "Score (1-5)", "Peso", "Puntos", "Justificación"], "widths": [3, 1.3, 1, 1.2, 5],
                   "align": ["left", "center", "center", "center", "left"],
                   "rows": [[d["nombre"], show(d["score"]), d["peso"], show(d["puntos"]), d["detalle"]]
                            for d in result["dimensiones"]]}},
        {"table": {"header": ["Métrica", "Valor"], "widths": [2, 3], "rows": [
            ["Volumen mensual", f"{show(result['volumen_mensual'])} eventos/mes"],
            ["Tiempo promedio por ejecución", f"{show(result['tiempo_minutos_por_ejecucion'])} min/evento"],
            ["% Automatización", f"{show(result['pct_automatizacion'])}%"],
            ["HH mensuales calculadas", f"{show(result['hh_mensual'])} HH/mes"],
        ]}},
        {"table": {"header": ["Resultado", "Valor"], "widths": [2, 3], "rows": [
            ["Score final", show(result["score"])],
            ["Prioridad", result["prioridad"]],
            ["Decisión tomada", ""],
            ["Responsable definido", ""],
        ]}},
        {"note": coe.GOVERNANCE_NOTICE},
    ]
    return blocks


def main():
    args = parse_args("Genera la propuesta técnica en formato SONDA (.docx)")
    spec = load_spec(args.json, REQUIRED)
    check_items(spec["alcance"], "alcance", ["id", "titulo"])
    check_items(spec["fuera_de_alcance"], "fuera_de_alcance", ["id", "titulo"])
    try:
        result = coe.evaluate(spec["evaluacion_coe"])
    except coe.CoeError as err:
        fail(str(err))

    manual_spec = {
        "title": f"Propuesta Técnica: {initiative_name(spec['iniciativa'])}",
        "subtitle": spec["iniciativa"],
        "version": "1.0",
        "version_date": today(),
        "author": spec.get("autor") or "[Ingresar autor]",
        "change": "Creación del documento",
        "change_date": today("%d-%m-%Y"),
        "body": body(spec, result),
    }
    with tempfile.TemporaryDirectory() as tmp:
        manual_path = Path(tmp) / "spec.json"
        manual_path.write_text(json.dumps(manual_spec, ensure_ascii=False), encoding="utf-8")
        save(lambda: build_manual.main(manual_path, args.output), args.output)

    card = coe.render_card(
        spec["iniciativa"], spec.get("torre"), ", ".join(spec.get("sistemas") or []),
        [c["id"] for c in spec["alcance"]], [c["id"] for c in spec["fuera_de_alcance"]], result,
    )
    # Also saved as a file: the agent shows it from there, safe from console encoding issues.
    card_path = Path(args.output).with_name("tarjeta-coe.txt")
    save(lambda: card_path.write_text(card + "\n", encoding="utf-8"), card_path)
    print(card)


if __name__ == "__main__":
    main()
