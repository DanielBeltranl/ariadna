import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "pendientes.py"


def run(folder):
    proc = subprocess.run([sys.executable, str(SCRIPT), "--dir", str(folder)], capture_output=True, text=True,
                          encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return proc


class PendientesTest(unittest.TestCase):
    def collect(self, files):
        with tempfile.TemporaryDirectory() as tmp:
            for name, content in files.items():
                Path(tmp, name).write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
            proc = run(tmp)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)["pendientes"]

    def test_lists_pending_items_of_the_examples(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("propuesta.json", "automatizabilidad.json", "casos.json"):
                shutil.copy(ROOT / "examples" / name, tmp)
            proc = run(tmp)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        items = {(p["archivo"], p["campo"]) for p in json.loads(proc.stdout)["pendientes"]}
        self.assertEqual(items, {
            ("propuesta.json", "observaciones[1]"),
            ("propuesta.json", "evaluacion_coe.alineamiento"),
            ("automatizabilidad.json", "UC-01.excepciones"),
            ("automatizabilidad.json", "UC-01.optimizacion"),
            ("automatizabilidad.json", "UC-02.reglas"),
            ("automatizabilidad.json", "UC-02.optimizacion"),
        })

    def test_every_item_carries_a_question(self):
        items = self.collect({"propuesta.json": {"iniciativa": "X", "evaluacion_coe": {"volumen_mensual": None}}})
        fields = {p["campo"]: p["pregunta"] for p in items}
        self.assertIn("torre", fields)
        self.assertIn("solicitante", fields)
        self.assertIn("evaluacion_coe.volumen_mensual", fields)
        self.assertTrue(all(q.strip() for q in fields.values()))

    def test_pending_text_in_any_json_is_listed(self):
        items = self.collect({"historias.json": {"historias": [{"criterios": ["Usuario: [PENDIENTE]"]}]}})
        self.assertEqual(items[0]["campo"], "historias[0].criterios[0]")
        self.assertIn("Usuario: [PENDIENTE]", items[0]["pregunta"])

    def test_answered_criterion_without_question_is_not_listed(self):
        spec = {"casos": [{"id": "UC-01", "criterios": {"reglas": {"estado": "cumple", "evidencia": "ok"}}}]}
        self.assertEqual(self.collect({"automatizabilidad.json": spec}), [])

    def test_folder_without_ariadna_json_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "acta.docx").write_bytes(b"x")
            proc = run(tmp)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("No hay JSON de Ariadna", proc.stderr)


if __name__ == "__main__":
    unittest.main()
