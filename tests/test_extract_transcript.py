import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "extract_transcript.py"

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


def run(*args):
    proc = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True,
                          encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return proc, (json.loads(proc.stdout) if proc.returncode == 0 else None)


class ExtractTranscriptTest(unittest.TestCase):
    def test_vtt_metadata_and_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out = Path(tmp) / "reu.vtt", Path(tmp) / "transcripcion.txt"
            src.write_text(VTT, encoding="utf-8")
            proc, meta = run("--input", src, "--output", out)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            text = out.read_text(encoding="utf-8")
        self.assertEqual(meta["participantes"], ["Nelssy Paredes", "Nelson Silva"])
        self.assertEqual(meta["duracion_min"], 28)
        self.assertIn("sistema SAG", meta["tema"])
        self.assertIn("Nelssy Paredes: Hoy revisamos el sistema SAG manualmente.", text)
        self.assertNotIn("-->", text)

    def test_docx_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "reu.docx"
            make_docx(src, DOCX_PARAGRAPHS)
            proc, meta = run("--input", src)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(meta["participantes"], ["Nelssy Paredes", "Daniel Beltran"])
        self.assertEqual(meta["duracion_min"], 13)

    def test_folder_picks_most_recent_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, new = Path(tmp) / "vieja.txt", Path(tmp) / "nueva.vtt"
            old.write_text("texto viejo", encoding="utf-8")
            new.write_text(VTT, encoding="utf-8")
            (Path(tmp) / "foto.png").write_bytes(b"x")
            past = time.time() - 3600
            os.utime(old, (past, past))
            proc, meta = run("--input", tmp)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(Path(meta["archivo"]).name, "nueva.vtt")

    def test_plain_text_without_speakers_omits_optional_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "reu.txt"
            src.write_text("Notas sueltas de la reunión.", encoding="utf-8")
            proc, meta = run("--input", src)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIsNone(meta["duracion_min"])
        self.assertEqual(meta["participantes"], [])

    def test_missing_input_fails_clearly(self):
        proc, _ = run("--input", ROOT / "no-existe.txt")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("no-existe.txt", proc.stderr)

    def test_folder_without_transcripts_fails_clearly(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc, _ = run("--input", tmp)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("No hay transcripciones", proc.stderr)


if __name__ == "__main__":
    unittest.main()
