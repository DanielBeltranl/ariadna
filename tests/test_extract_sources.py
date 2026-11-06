import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
import zipfile
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "extract_sources.py"

VTT = """WEBVTT

00:00:03.000 --> 00:00:06.000
<v Nelssy Paredes>Hoy revisamos el sistema SAG manualmente.</v>

00:27:40.000 --> 00:27:45.000
<v Nelson Silva>Queda pendiente el acceso.</v>
"""

DOCX_PARAGRAPHS = ["Nelssy Paredes   0:03", "Hoy revisamos el sistema SAG.", "Daniel Beltran   12:30", "Ok, lo automatizamos."]


def make_docx(path, paragraphs):
    body = "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs)
    xml = ('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
           f"<w:body>{body}</w:body></w:document>")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/document.xml", xml)


def make_pptx(path, slides):
    a = "http://schemas.openxmlformats.org/drawingml/2006/main"
    with zipfile.ZipFile(path, "w") as z:
        for i, text in enumerate(slides, 1):
            z.writestr(f"ppt/slides/slide{i}.xml",
                       f'<p:sld xmlns:p="p" xmlns:a="{a}"><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:sld>')


def run(*args):
    proc = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True,
                          encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return proc, (json.loads(proc.stdout)["fuentes"] if proc.returncode == 0 else None)


def by_name(sources):
    return {Path(s["archivo"]).name: s for s in sources}


class TranscriptTest(unittest.TestCase):
    def test_vtt_metadata_and_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out = Path(tmp) / "reu.vtt", Path(tmp) / "fuentes.md"
            src.write_text(VTT, encoding="utf-8")
            proc, sources = run("--input", src, "--output", out)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            text = out.read_text(encoding="utf-8")
        meta = sources[0]
        self.assertEqual(meta["estado"], "extraido")
        self.assertEqual(meta["participantes"], ["Nelssy Paredes", "Nelson Silva"])
        self.assertEqual(meta["duracion_min"], 28)
        self.assertIn("sistema SAG", meta["tema"])
        self.assertIn("Nelssy Paredes: Hoy revisamos el sistema SAG manualmente.", text)
        self.assertNotIn("-->", text)

    def test_docx_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "reu.docx"
            make_docx(src, DOCX_PARAGRAPHS)
            proc, sources = run("--input", src)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(sources[0]["participantes"], ["Nelssy Paredes", "Daniel Beltran"])
        self.assertEqual(sources[0]["duracion_min"], 13)

    def test_plain_text_without_speakers_omits_optional_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "reu.txt"
            src.write_text("Notas sueltas de la reunión.", encoding="utf-8")
            proc, sources = run("--input", src)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIsNone(sources[0]["duracion_min"])
        self.assertEqual(sources[0]["participantes"], [])


class SourcesTest(unittest.TestCase):
    def test_folder_reads_every_file_recursively_and_skips_hidden_and_temp(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "sub").mkdir()
            (base / "notas.md").write_text("# Arquitectura\nOracle 19c", encoding="utf-8")
            (base / "sub" / "reu.vtt").write_text(VTT, encoding="utf-8")
            (base / "diagrama.pdf").write_bytes(b"%PDF-1.4")
            (base / "viejo.xls").write_bytes(b"\xd0\xcf\x11\xe0\x00\x00")
            (base / ".oculto.txt").write_text("no", encoding="utf-8")
            (base / "~$borrador.docx").write_bytes(b"x")
            out = base / "salida" / "fuentes.md"
            out.parent.mkdir()
            proc, sources = run("--input", base / "notas.md", "--input", base / "sub", "--input", base / "diagrama.pdf",
                                "--input", base / "viejo.xls", "--input", base / ".oculto.txt", "--output", out)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            text = out.read_text(encoding="utf-8")
            out.unlink()
            out.parent.rmdir()
            proc, folder = run("--input", base)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        names = by_name(folder)
        self.assertEqual(set(names), {"notas.md", "reu.vtt", "diagrama.pdf", "viejo.xls"})
        self.assertEqual(names["diagrama.pdf"]["estado"], "leer_con_read")
        self.assertEqual(names["viejo.xls"]["estado"], "no_soportado")
        self.assertIn("Oracle 19c", text)
        self.assertIn("Nelson Silva: Queda pendiente el acceso.", text)
        self.assertIn("diagrama.pdf", text)
        self.assertEqual(len(sources), 5)  # a hidden file given explicitly is still read

    def test_xlsx_and_pptx_are_extracted(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            wb = openpyxl.Workbook()
            wb.active.title = "Volumen"
            wb.active.append(["Mes", "Casos"])
            wb.active.append(["Enero", 120])
            wb.save(base / "datos.xlsx")
            make_pptx(base / "deck.pptx", ["Flujo actual", "Sistema SAP"])
            out = base / "fuentes.md"
            proc, sources = run("--input", base / "datos.xlsx", "--input", base / "deck.pptx", "--output", out)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            text = out.read_text(encoding="utf-8")
        self.assertEqual({s["estado"] for s in sources}, {"extraido"})
        self.assertIn("Volumen", text)
        self.assertIn("Enero | 120", text)
        self.assertLess(text.index("Flujo actual"), text.index("Sistema SAP"))

    def test_latest_picks_most_recent_file_in_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, new = Path(tmp) / "vieja.txt", Path(tmp) / "nueva.vtt"
            old.write_text("texto viejo", encoding="utf-8")
            new.write_text(VTT, encoding="utf-8")
            past = time.time() - 3600
            os.utime(old, (past, past))
            proc, sources = run("--input", tmp, "--latest")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual([Path(s["archivo"]).name for s in sources], ["nueva.vtt"])

    def test_missing_input_fails_clearly(self):
        proc, _ = run("--input", ROOT / "no-existe.txt")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("no-existe.txt", proc.stderr)

    def test_empty_folder_fails_clearly(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc, _ = run("--input", tmp)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("No hay archivos", proc.stderr)


if __name__ == "__main__":
    unittest.main()
