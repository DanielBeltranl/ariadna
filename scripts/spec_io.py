"""Shared CLI plumbing for the generator scripts: --json/--output, validation and clear errors."""
import argparse
import json
import sys
from datetime import date


def fail(message):
    sys.stderr.write(f"ERROR: {message}\n")
    sys.exit(1)


def utf8_console():
    # The Windows code page (cp1252) garbles accents in Git Bash and cannot print every character.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def parse_args(description):
    utf8_console()
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--json", required=True, help="Input JSON file")
    parser.add_argument("--output", required=True, help="Output file path")
    return parser.parse_args()


def load_spec(path, required):
    """Load the JSON spec and check that every key in `required` ({key: type}) is present and typed."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            spec = json.load(f)
    except (OSError, json.JSONDecodeError) as err:
        fail(f"No se pudo leer el JSON {path}: {err}")
    if not isinstance(spec, dict):
        fail("El JSON debe ser un objeto")
    for key, kind in required.items():
        if not isinstance(spec.get(key), kind):
            fail(f"Campo obligatorio ausente o con tipo inválido: {key} (se espera {kind.__name__})")
    return spec


def check_items(items, field, required):
    """Every item of a list field must be an object holding the required keys."""
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            fail(f"{field}[{i}] debe ser un objeto")
        missing = [k for k in required if k not in item]
        if missing:
            fail(f"{field}[{i}] no tiene los campos: {', '.join(missing)}")


def save(save_fn, output):
    """Run the save callback; Windows refuses to overwrite a file open in Excel/Word."""
    try:
        save_fn()
    except OSError as err:
        fail(f"No se pudo guardar {output} (¿está abierto en Excel o Word?): {err}")


def today(fmt="%d/%m/%Y"):
    return date.today().strftime(fmt)
