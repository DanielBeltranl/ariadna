import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_automatizabilidad.py"
EXAMPLE = json.loads((ROOT / "examples" / "automatizabilidad.json").read_text(encoding="utf-8"))
ALL_MET = {k: {"estado": "cumple", "evidencia": "ok [fuente: a.docx]"} for k in EXAMPLE["casos"][0]["criterios"]}


def case(**overrides):
    criterios = json.loads(json.dumps(ALL_MET))
    for key, estado in overrides.items():
        criterios[key] = {"estado": estado, "evidencia": ""}
        if estado == "sin_evidencia":
            criterios[key]["pregunta"] = f"¿Pregunta sobre {key}?"
    return {"iniciativa": "X | Y | Z", "casos": [{"id": "UC-01", "titulo": "T", "criterios": criterios}]}


def run(spec, tmp):
    spec_path, out = Path(tmp) / "automatizabilidad.json", Path(tmp) / "Analisis.docx"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    proc = subprocess.run([sys.executable, str(SCRIPT), "--json", str(spec_path), "--output", str(out)],
                          capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return proc, out


def document_xml(path):
    with zipfile.ZipFile(path) as z:
        return z.read("word/document.xml").decode("utf-8")


class BuildAutomatizabilidadTest(unittest.TestCase):
    def verdict(self, spec):
        with tempfile.TemporaryDirectory() as tmp:
            proc, _ = run(spec, tmp)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout

    def test_generates_docx_with_sections_and_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc, out = run(EXAMPLE, tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            xml = document_xml(out)
        for text in ("Criterios de evaluación", "Resumen", "UC-01", "UC-02", "Reglas claras y explícitas",
                     "ping falla 3 veces", "Preguntas pendientes", "enlaces satelitales"):
            self.assertIn(text, xml)
        self.assertNotIn("{{", xml)

    def test_all_met_is_automatable(self):
        self.assertIn("UC-01: Automatizable", self.verdict(case()))

    def test_each_eliminatory_not_met_blocks(self):
        for key in ("reglas", "entradas", "estabilidad", "excepciones"):
            with self.subTest(key=key):
                self.assertIn("UC-01: No automatizable aún", self.verdict(case(**{key: "no_cumple"})))

    def test_eliminatory_without_evidence_is_to_confirm(self):
        self.assertIn("UC-01: Por confirmar", self.verdict(case(reglas="sin_evidencia")))

    def test_risk_not_met_requires_human_review(self):
        self.assertIn("UC-01: Automatizable con revisión humana", self.verdict(case(riesgo="no_cumple")))

    def test_systems_not_met_is_only_an_observation(self):
        out = self.verdict(case(sistemas="no_cumple"))
        self.assertIn("UC-01: Automatizable", out)
        self.assertNotIn("No automatizable", out)
        with tempfile.TemporaryDirectory() as tmp:
            _, docx = run(case(sistemas="no_cumple"), tmp)
            self.assertIn("vía de integración", document_xml(docx))

    def test_example_verdicts(self):
        out = self.verdict(EXAMPLE)
        self.assertIn("UC-01: Automatizable", out)
        self.assertIn("UC-02: No automatizable aún", out)

    def test_score_all_met_is_100_high(self):
        self.assertIn("UC-01: Automatizable (score 100/100, Alto)", self.verdict(case()))

    def test_score_weights_eliminatory_double_and_partial_half(self):
        # reglas no_cumple (-2), volumen parcial (-0.5): 10.5/13 = 80.8 -> 81
        out = self.verdict(case(reglas="no_cumple", volumen="parcial"))
        self.assertIn("UC-01: No automatizable aún (score 81/100, Alto)", out)

    def test_score_counts_missing_evidence_as_zero_and_reports_it(self):
        # optimizacion, medible, riesgo sin evidencia: 10/13 = 76.9 -> 77
        spec = case(optimizacion="sin_evidencia", medible="sin_evidencia", riesgo="sin_evidencia")
        self.assertIn("(score 77/100, Medio)", self.verdict(spec))
        with tempfile.TemporaryDirectory() as tmp:
            _, docx = run(spec, tmp)
            xml = document_xml(docx)
        self.assertIn("3 criterios sin evidencia", xml)
        self.assertIn("Score", xml)

    def test_example_scores(self):
        out = self.verdict(EXAMPLE)
        # UC-01: 13 - 1 (excepciones parcial) - 1 (optimizacion) = 11/13 -> 85
        self.assertIn("UC-01: Automatizable (score 85/100, Alto)", out)
        # UC-02: entradas 1 + estabilidad 2 + volumen .5 + medible .5 = 4/13 -> 31
        self.assertIn("UC-02: No automatizable aún (score 31/100, Bajo)", out)

    def test_uses_version_and_change_when_given(self):
        spec = json.loads(json.dumps(EXAMPLE))
        spec["version"], spec["cambio"] = "1.1", "Actualización de pendientes"
        with tempfile.TemporaryDirectory() as tmp:
            proc, out = run(spec, tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            xml = document_xml(out)
        self.assertIn("1.1", xml)
        self.assertIn("Actualización de pendientes", xml)

    def test_defaults_to_first_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, out = run(EXAMPLE, tmp)
            xml = document_xml(out)
        self.assertIn("Creación del documento", xml)

    def test_rejects_missing_criterion(self):
        spec = case()
        del spec["casos"][0]["criterios"]["riesgo"]
        with tempfile.TemporaryDirectory() as tmp:
            proc, out = run(spec, tmp)
            self.assertFalse(out.exists())
        self.assertEqual(proc.returncode, 1)
        self.assertIn("riesgo", proc.stderr)

    def test_rejects_missing_evidence_without_question(self):
        spec = case(volumen="sin_evidencia")
        del spec["casos"][0]["criterios"]["volumen"]["pregunta"]
        with tempfile.TemporaryDirectory() as tmp:
            proc, out = run(spec, tmp)
            self.assertFalse(out.exists())
        self.assertEqual(proc.returncode, 1)
        self.assertIn("volumen", proc.stderr)
        self.assertIn("pregunta", proc.stderr)

    def test_rejects_invalid_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc, _ = run(case(reglas="quizas"), tmp)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("quizas", proc.stderr)


if __name__ == "__main__":
    unittest.main()
