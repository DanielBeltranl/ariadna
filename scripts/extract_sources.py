"""Extract every source file of an initiative to one plain-text Markdown file and print per-file data as JSON.

Usage:
  python extract_sources.py --input <file|folder> [--input ...] [--latest] [--output fuentes.md]

A folder contributes every file in it, recursively, skipping hidden and Office temp (~$) files.
--latest keeps only the most recently modified file of each folder.
Stdout: {"fuentes": [{"archivo", "modificado", "estado", "duracion_min", "participantes", "tema"}]}
estado: "extraido" (text in the output), "leer_con_read" (PDF/image: the agent reads it natively)
or "no_soportado" (binary format with no extractor). Duration and participants are null/empty
when the source carries no timestamps or speakers (any non-transcript document).
"""
import argparse
import json
import math
import re
import zipfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from spec_io import fail, utf8_console

NATIVE = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
VTT_CUE = re.compile(r"(?:(\d+):)?(\d{2}):(\d{2})\.\d{3}\s+-->\s+(?:(\d+):)?(\d{2}):(\d{2})\.\d{3}")
VTT_VOICE = re.compile(r"<v\s+([^>]+)>(.*?)(?:</v>|$)")
DOCX_SPEAKER = re.compile(r"^(.+?)\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*$")
SLIDE = re.compile(r"ppt/slides/slide(\d+)\.xml$")
TOPIC_CHARS = 200


def seconds(h, m, s):
    return int(h or 0) * 3600 + int(m) * 60 + int(s or 0)


def visible(path, root):
    return not any(part.startswith((".", "~$")) for part in path.relative_to(root).parts)


def resolve(inputs, latest):
    files = []
    for raw in inputs:
        path = Path(raw).expanduser()
        if path.is_dir():
            found = sorted(p for p in path.rglob("*") if p.is_file() and visible(p, path))
            if not found:
                fail(f"No hay archivos en {path}")
            files += [max(found, key=lambda p: p.stat().st_mtime)] if latest else found
        elif path.is_file():
            files.append(path)
        else:
            fail(f"No existe el archivo o carpeta {path}")
    return list(dict.fromkeys(files))


def parse_vtt(text):
    turns, last = [], None
    for line in text.splitlines():
        cue = VTT_CUE.search(line)
        if cue:
            last = seconds(*cue.groups()[3:])
            continue
        voice = VTT_VOICE.search(line)
        if voice:
            turns.append((voice.group(1).strip(), voice.group(2).strip()))
        elif line.strip() and line.strip() != "WEBVTT" and not line.strip().isdigit():
            turns.append((None, line.strip()))
    return turns, last


def parse_docx(path):
    root = ET.fromstring(zipfile.ZipFile(path).read("word/document.xml"))
    turns, speaker, last = [], None, None
    for p in root.iter(f"{W}p"):
        line = "".join(t.text or "" for t in p.iter(f"{W}t")).strip()
        if not line:
            continue
        header = DOCX_SPEAKER.match(line)
        if header:  # Teams transcript speaker line: "Name M:SS" or "Name H:MM:SS"
            speaker = header.group(1).strip()
            a, b, c = header.group(2), header.group(3), header.group(4)
            last = seconds(a, b, c) if c else seconds(0, a, b)
        else:
            turns.append((speaker, line))
    return turns, last


def parse_pptx(path):
    with zipfile.ZipFile(path) as z:
        slides = sorted((int(m.group(1)), n) for n in z.namelist() if (m := SLIDE.match(n)))
        turns = []
        for number, name in slides:
            root = ET.fromstring(z.read(name))
            turns.append((None, f"[Diapositiva {number}]"))
            turns += [(None, line) for p in root.iter(f"{A}p")
                      if (line := "".join(t.text or "" for t in p.iter(f"{A}t")).strip())]
    return turns, None


def parse_xlsx(path):
    import openpyxl  # already required by the generators; imported here so other formats work without it

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    turns = []
    for ws in wb.worksheets:
        turns.append((None, f"[Hoja {ws.title}]"))
        for row in ws.iter_rows(values_only=True):
            cells = ["" if v is None else str(v) for v in row]
            if any(cells):
                turns.append((None, " | ".join(cells).rstrip(" |")))
    wb.close()
    return turns, None


def parse_text(path):
    data = path.read_bytes()
    if b"\x00" in data:
        return None
    try:
        raw = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raw = data.decode("cp1252", errors="replace")
    if path.suffix.lower() == ".vtt":
        return parse_vtt(raw)
    return [(None, line.rstrip()) for line in raw.splitlines() if line.strip()], None


PARSERS = {".docx": parse_docx, ".pptx": parse_pptx, ".xlsx": parse_xlsx, ".xlsm": parse_xlsx}


def extract(path):
    """Return (estado, turns, last_second)."""
    suffix = path.suffix.lower()
    if suffix in NATIVE:
        return "leer_con_read", [], None
    try:
        parsed = PARSERS.get(suffix, parse_text)(path)
    except (zipfile.BadZipFile, KeyError, ET.ParseError, OSError, ValueError) as err:
        fail(f"No se pudo leer {path}: {err}")
    if parsed is None:
        return "no_soportado", [], None
    return "extraido", *parsed


def main():
    parser = argparse.ArgumentParser(description="Extrae las fuentes de una iniciativa a texto plano")
    parser.add_argument("--input", required=True, action="append", help="Archivo o carpeta (repetible)")
    parser.add_argument("--latest", action="store_true", help="De cada carpeta, usa solo el archivo más reciente")
    parser.add_argument("--output", help="Ruta del .md consolidado de salida")
    utf8_console()
    args = parser.parse_args()

    sources, sections = [], []
    for path in resolve(args.input, args.latest):
        estado, turns, last = extract(path)
        participants = list(dict.fromkeys(s for s, _ in turns if s))
        body = {
            "extraido": "\n".join(f"{s}: {t}" if s else t for s, t in turns),
            "leer_con_read": "[PDF o imagen: leer el archivo original con la herramienta Read]",
            "no_soportado": "[Formato binario sin extractor: pedir al usuario una versión .docx, .xlsx, .pdf o texto]",
        }[estado]
        sections.append(f"## {path}\n\n{body}\n")
        sources.append({
            "archivo": str(path),
            "modificado": datetime.fromtimestamp(path.stat().st_mtime).strftime("%d/%m/%Y %H:%M"),
            "estado": estado,
            "duracion_min": math.ceil(last / 60) if last else None,
            "participantes": participants,
            "tema": " ".join(t for _, t in turns)[:TOPIC_CHARS],
        })

    if args.output:
        try:
            Path(args.output).write_text("# Fuentes\n\n" + "\n".join(sections), encoding="utf-8")
        except OSError as err:
            fail(f"No se pudo guardar {args.output}: {err}")

    print(json.dumps({"fuentes": sources}))  # ASCII escapes keep names intact whatever the console encoding


if __name__ == "__main__":
    main()
