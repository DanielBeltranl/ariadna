"""Extract a Teams transcript (.txt, .vtt or .docx) to plain text and print confirmation data as JSON.

Usage:
  python extract_transcript.py --input <file|folder> [--output transcripcion.txt]

With a folder, the most recently modified transcript in it is used.
Stdout: {"archivo", "modificado", "duracion_min", "participantes", "tema"}; duration and
participants are null/empty when the format carries no timestamps or speakers.
"""
import argparse
import json
import math
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from spec_io import fail

EXTENSIONS = {".txt", ".vtt", ".docx"}
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
VTT_CUE = re.compile(r"(?:(\d+):)?(\d{2}):(\d{2})\.\d{3}\s+-->\s+(?:(\d+):)?(\d{2}):(\d{2})\.\d{3}")
VTT_VOICE = re.compile(r"<v\s+([^>]+)>(.*?)(?:</v>|$)")
DOCX_SPEAKER = re.compile(r"^(.+?)\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*$")
TOPIC_CHARS = 200


def seconds(h, m, s):
    return int(h or 0) * 3600 + int(m) * 60 + int(s or 0)


def resolve(path):
    path = Path(path).expanduser()
    if path.is_dir():
        candidates = [p for p in path.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS]
        if not candidates:
            fail(f"No hay transcripciones (.txt, .vtt, .docx) en {path}")
        return max(candidates, key=lambda p: p.stat().st_mtime)
    if not path.is_file():
        fail(f"No existe el archivo {path}")
    if path.suffix.lower() not in EXTENSIONS:
        fail(f"Formato no soportado {path.suffix}: se espera .txt, .vtt o .docx")
    return path


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
    try:
        with zipfile.ZipFile(path) as z:
            root = ET.fromstring(z.read("word/document.xml"))
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as err:
        fail(f"No se pudo leer el .docx {path}: {err}")
    turns, speaker, last = [], None, None
    for p in root.iter(f"{W}p"):
        line = "".join(t.text or "" for t in p.iter(f"{W}t")).strip()
        if not line:
            continue
        header = DOCX_SPEAKER.match(line)
        if header:
            speaker = header.group(1).strip()
            # "M:SS" or "H:MM:SS"
            a, b, c = header.group(2), header.group(3), header.group(4)
            last = seconds(a, b, c) if c else seconds(0, a, b)
        else:
            turns.append((speaker, line))
    return turns, last


def main():
    parser = argparse.ArgumentParser(description="Extrae una transcripción de Teams a texto plano")
    parser.add_argument("--input", required=True, help="Archivo de transcripción o carpeta donde buscar la más reciente")
    parser.add_argument("--output", help="Ruta del .txt de salida")
    args = parser.parse_args()
    sys.stdout.reconfigure(errors="replace")

    path = resolve(args.input)
    suffix = path.suffix.lower()
    if suffix == ".docx":
        turns, last = parse_docx(path)
    else:
        try:
            raw = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            raw = path.read_text(encoding="cp1252")
        turns, last = parse_vtt(raw) if suffix == ".vtt" else ([(None, line.strip()) for line in raw.splitlines() if line.strip()], None)

    participants = list(dict.fromkeys(s for s, _ in turns if s))
    lines = [f"{s}: {t}" if s else t for s, t in turns]
    spoken = " ".join(t for _, t in turns)

    if args.output:
        try:
            Path(args.output).write_text("\n".join(lines) + "\n", encoding="utf-8")
        except OSError as err:
            fail(f"No se pudo guardar {args.output}: {err}")

    print(json.dumps({
        "archivo": str(path),
        "modificado": datetime.fromtimestamp(path.stat().st_mtime).strftime("%d/%m/%Y %H:%M"),
        "duracion_min": math.ceil(last / 60) if last else None,
        "participantes": participants,
        "tema": spoken[:TOPIC_CHARS],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
