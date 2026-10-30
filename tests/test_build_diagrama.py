import json
import os
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = json.loads((ROOT / "examples" / "diagrama.json").read_text(encoding="utf-8"))


def run(spec, tmp):
    spec_path, out = Path(tmp) / "diagrama.json", Path(tmp) / "diagrama.drawio"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_diagrama.py"), "--json", str(spec_path), "--output", str(out)],
                          capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return proc, out


class BuildDiagramaTest(unittest.TestCase):
    def test_generates_uncompressed_drawio_with_lifelines_and_ordered_messages(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc, out = run(EXAMPLE, tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            root = ET.parse(out).getroot()
        self.assertEqual(root.tag, "mxfile")
        self.assertEqual(root.find("diagram").get("name"), EXAMPLE["titulo"])
        cells = root.iter("mxCell")
        lifelines, edges = [], []
        for c in cells:
            style = c.get("style") or ""
            if "umlLifeline" in style:
                lifelines.append(c)
            elif c.get("edge") == "1":
                edges.append(c)
        self.assertEqual([c.get("value") for c in lifelines], EXAMPLE["participantes"])
        self.assertEqual([c.get("value") for c in edges], [m["texto"] for m in EXAMPLE["mensajes"]])
        ys = [float(e.find("mxGeometry/mxPoint[@as='sourcePoint']").get("y")) for e in edges]
        self.assertEqual(ys, sorted(ys))
        for edge, msg in zip(edges, EXAMPLE["mensajes"]):
            self.assertEqual("dashed=1" in edge.get("style"), msg.get("respuesta", False))

    def test_self_message_is_drawn_as_loop(self):
        spec = {"titulo": "T", "participantes": ["A"], "mensajes": [{"de": "A", "a": "A", "texto": "valida"}]}
        with tempfile.TemporaryDirectory() as tmp:
            proc, out = run(spec, tmp)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            edge = next(c for c in ET.parse(out).getroot().iter("mxCell") if c.get("edge") == "1")
        self.assertIsNotNone(edge.find("mxGeometry/Array"))

    def test_rejects_unknown_participant(self):
        spec = dict(EXAMPLE, mensajes=[{"de": "Operador N1", "a": "Fantasma", "texto": "hola"}])
        with tempfile.TemporaryDirectory() as tmp:
            proc, out = run(spec, tmp)
            self.assertFalse(out.exists())
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Fantasma", proc.stderr)


if __name__ == "__main__":
    unittest.main()
