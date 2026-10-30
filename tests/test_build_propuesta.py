import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_propuesta.py"
EXAMPLE = json.loads((ROOT / "examples" / "propuesta.json").read_text(encoding="utf-8"))


def run(spec, tmp):
    spec_path, out = Path(tmp) / "propuesta.json", Path(tmp) / "Propuesta.docx"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    proc = subprocess.run([sys.executable, str(SCRIPT), "--json", str(spec_path), "--output", str(out)],
                          capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return proc, out


def document_xml(path):
    with zipfile.ZipFile(path) as z:
        return z.read("word/document.xml").decode("utf-8")


class BuildPropuestaTest(unittest.TestCase):
    def test_generates_docx_with_all_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc, out = run(EXAMPLE, tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            xml = document_xml(out)
        for text in ("Contexto", "Objetivo general", "Objetivos específicos", "Alcance", "Fuera de alcance",
                     "Observaciones", "Valorización CoE", "Decisión tomada", "Responsable definido",
                     "UC-01", "UC-03", "Gestión Alerta Enlaces caídos", "Zabbix"):
            self.assertIn(text, xml)
        self.assertNotIn("{{", xml)

    def test_missing_score_is_reported_as_insufficient_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc, out = run(EXAMPLE, tmp)
            xml = document_xml(out)
        self.assertIn("No hay suficientes datos para establecer una calificación certera", xml)
        self.assertIn("SCORE FINAL CoE: [PENDIENTE]", proc.stdout)

    def test_prints_card_with_final_score_when_data_is_complete(self):
        spec = json.loads(json.dumps(EXAMPLE))
        spec["evaluacion_coe"]["alineamiento"] = 4
        with tempfile.TemporaryDirectory() as tmp:
            proc, _ = run(spec, tmp)
        # 600*10*80%/60 = 80 HH -> eficiencia 4; 1.2+0.8+0.45+0.3+0.4-0.3
        self.assertIn("SCORE FINAL CoE: 2.85  ==>  PRIORIDAD: Media", proc.stdout)
        self.assertIn("Casos Viables Asumidos: UC-01, UC-02", proc.stdout)

    def test_rejects_missing_required_field(self):
        spec = {k: v for k, v in EXAMPLE.items() if k != "objetivo_general"}
        with tempfile.TemporaryDirectory() as tmp:
            proc, out = run(spec, tmp)
            self.assertFalse(out.exists())
        self.assertEqual(proc.returncode, 1)
        self.assertIn("objetivo_general", proc.stderr)

    def test_rejects_invalid_score(self):
        spec = json.loads(json.dumps(EXAMPLE))
        spec["evaluacion_coe"]["impacto"] = 7
        with tempfile.TemporaryDirectory() as tmp:
            proc, _ = run(spec, tmp)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("evaluacion_coe.impacto", proc.stderr)


if __name__ == "__main__":
    unittest.main()
