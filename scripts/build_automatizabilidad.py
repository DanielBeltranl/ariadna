"""Build the automatability analysis (.docx) from automatizabilidad.json and print one verdict per use case.

Usage: python build_automatizabilidad.py --json automatizabilidad.json --output "Analisis de Automatizabilidad X.docx"
Schema by example: examples/automatizabilidad.json. Criteria guide: templates/criterios_automatizabilidad.md
"""
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "sonda"))

import build_manual  # noqa: E402  (vendored, unmodified copy of the sonda-user-manual generator)
from spec_io import check_items, fail, load_spec, parse_args, save, today  # noqa: E402

# key -> (name, what it checks). Order is the order shown in the document.
CRITERIA = {
    "reglas": ("Reglas claras y explícitas", "Las decisiones se expresan como «si pasa X, hago Y»."),
    "entradas": ("Entradas estructuradas y predecibles", "Los datos llegan en un formato consistente."),
    "estabilidad": ("Estabilidad", "El proceso no cambia con frecuencia."),
    "volumen": ("Volumen y frecuencia suficientes", "Se repite lo bastante para justificar construir y mantener la automatización."),
    "excepciones": ("Pocas excepciones o bien acotadas", "El 80–90% de los casos sigue el camino feliz y las excepciones se pueden detectar."),
    "sistemas": ("Sistemas accesibles", "Las herramientas permiten integración (API, base de datos, exportación, conector)."),
    "optimizacion": ("Proceso optimizado", "No hay pasos innecesarios, aprobaciones redundantes ni duplicidades."),
    "medible": ("Resultado medible y verificable", "Se puede comprobar si la ejecución salió bien."),
    "riesgo": ("Riesgo controlado", "Un error no tiene consecuencias graves ni irreversibles."),
}
ELIMINATORY = ("reglas", "entradas", "estabilidad", "excepciones")
STATES = {"cumple": "Cumple", "parcial": "Parcial", "no_cumple": "No cumple", "sin_evidencia": "Sin evidencia"}
POINTS = {"cumple": 1, "parcial": 0.5, "no_cumple": 0, "sin_evidencia": 0}
MAX_POINTS = sum(2 if k in ELIMINATORY else 1 for k in CRITERIA)
SYSTEMS_NOTE = "Los sistemas actuales no permiten integración directa: requiere que el equipo proponga una vía de integración."


def verdict(criterios):
    """Return (verdict, reason). Fixed rules: the agent supplies evidence, never the verdict."""
    blocked = [CRITERIA[k][0] for k in ELIMINATORY if criterios[k]["estado"] == "no_cumple"]
    if blocked:
        return "No automatizable aún", "No cumple: " + ", ".join(blocked) + "."
    unknown = [CRITERIA[k][0] for k in ELIMINATORY if criterios[k]["estado"] == "sin_evidencia"]
    if unknown:
        return "Por confirmar", "Sin evidencia en criterios eliminatorios: " + ", ".join(unknown) + "."
    if criterios["riesgo"]["estado"] == "no_cumple":
        return "Automatizable con revisión humana", "Un error tiene consecuencias graves: dejar un punto de control humano."
    return "Automatizable", "Cumple los criterios eliminatorios."


def score(criterios):
    """Return (0-100 score, level, criteria without evidence). Eliminatory criteria weigh double."""
    points = sum(POINTS[criterios[k]["estado"]] * (2 if k in ELIMINATORY else 1) for k in CRITERIA)
    value = int(points * 100 / MAX_POINTS + 0.5)  # round half up, unlike round()
    level = "Alto" if value >= 80 else "Medio" if value >= 50 else "Bajo"
    missing = sum(criterios[k]["estado"] == "sin_evidencia" for k in CRITERIA)
    return value, level, missing


def validate(caso, i):
    criterios = caso.get("criterios")
    if not isinstance(criterios, dict):
        fail(f"casos[{i}].criterios debe ser un objeto")
    for key in CRITERIA:
        item = criterios.get(key)
        if not isinstance(item, dict):
            fail(f"casos[{i}].criterios.{key} ausente: evalúa los 9 criterios (usa sin_evidencia si no hay datos)")
        if item.get("estado") not in STATES:
            fail(f"casos[{i}].criterios.{key}.estado inválido: {item.get('estado')!r} (usa {', '.join(STATES)})")
        if item["estado"] == "sin_evidencia" and not str(item.get("pregunta") or "").strip():
            fail(f"casos[{i}].criterios.{key} sin_evidencia requiere una pregunta para responderlo en la próxima reunión")


def body(spec, results):
    blocks = [
        {"h1": "Criterios de evaluación"},
        {"p": "Cada caso de uso se evalúa con la evidencia de las fuentes. Los criterios eliminatorios son: "
              + ", ".join(CRITERIA[k][0] for k in ELIMINATORY)
              + ". Si alguno no se cumple, el caso no es automatizable tal como está hoy."},
        {"p": "Score de automatizabilidad (0 a 100): cada criterio suma 1 si cumple, 0,5 si es parcial y 0 si no cumple "
              "o no hay evidencia; los eliminatorios pesan el doble. Nivel: 80 o más Alto, 50 a 79 Medio, menos de 50 Bajo. "
              "El score indica qué tan cerca está el caso; el veredicto indica si se puede automatizar."},
        {"table": {"header": ["Criterio", "Qué se verifica"], "widths": [2, 4],
                   "rows": [[name + (" (eliminatorio)" if k in ELIMINATORY else ""), desc]
                            for k, (name, desc) in CRITERIA.items()]}},
        {"h1": "Resumen"},
        {"table": {"header": ["ID", "Caso de uso", "Veredicto", "Score", "Motivo"], "widths": [1, 2.6, 2, 1.2, 3.6],
                   "rows": [[c["id"], c["titulo"], v, f"{s}/100 ({lvl})", reason]
                            for c, (v, reason) in results for s, lvl, _ in [score(c["criterios"])]]}},
    ]
    for caso, (v, reason) in results:
        criterios = caso["criterios"]
        value, level, missing = score(criterios)
        score_text = f"**Score: {value}/100 ({level}).**"
        if missing:
            noun = "criterio sin evidencia cuenta" if missing == 1 else "criterios sin evidencia cuentan"
            score_text += f" {missing} {noun} como 0: completarlos puede subir el score."
        blocks += [
            {"h2": f"{caso['id']}: {caso['titulo']}"},
            {"p": f"**Veredicto: {v}.** {reason}"},
            {"p": score_text},
            {"table": {"header": ["Criterio", "Estado", "Evidencia"], "widths": [2.4, 1.4, 5],
                       "rows": [[CRITERIA[k][0], STATES[criterios[k]["estado"]], criterios[k].get("evidencia") or "-"]
                                for k in CRITERIA]}},
        ]
        if criterios["sistemas"]["estado"] == "no_cumple":
            blocks.append({"note": SYSTEMS_NOTE})
        questions = [criterios[k]["pregunta"] for k in CRITERIA if criterios[k].get("pregunta")]
        if questions:
            blocks += [{"label": "Preguntas pendientes"}, {"bullets": questions}]
    return blocks


def main():
    args = parse_args("Genera el análisis de automatizabilidad en formato SONDA (.docx)")
    spec = load_spec(args.json, {"iniciativa": str, "casos": list})
    if not spec["casos"]:
        fail("casos no puede estar vacío")
    check_items(spec["casos"], "casos", ["id", "titulo", "criterios"])
    for i, caso in enumerate(spec["casos"]):
        validate(caso, i)
    results = [(c, verdict(c["criterios"])) for c in spec["casos"]]

    manual_spec = {
        "title": "Análisis de Automatizabilidad",
        "subtitle": spec["iniciativa"],
        "version": spec.get("version") or "1.0",
        "version_date": today(),
        "author": spec.get("autor") or "[Ingresar autor]",
        "change": spec.get("cambio") or "Creación del documento",
        "change_date": today("%d-%m-%Y"),
        "body": body(spec, results),
    }
    with tempfile.TemporaryDirectory() as tmp:
        manual_path = Path(tmp) / "spec.json"
        manual_path.write_text(json.dumps(manual_spec, ensure_ascii=False), encoding="utf-8")
        save(lambda: build_manual.main(manual_path, args.output), args.output)

    for caso, (v, reason) in results:
        value, level, _ = score(caso["criterios"])
        print(f"{caso['id']}: {v} (score {value}/100, {level}) — {reason}")


if __name__ == "__main__":
    main()
