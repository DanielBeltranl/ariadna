"""Build the user stories workbook (.xlsx) from historias.json, one sheet per module.

Usage: python build_historias.py --json historias.json --output "Historias de Usuario X.xlsx"
Schema by example: examples/historias.json · Format reference: "Historias de usuario ejemplo.xlsx"
"""
from openpyxl import Workbook

from spec_io import check_items, fail, load_spec, parse_args, save
from xlsx_sheets import group_by_module, numbered, sheet_title, write_table

HEADERS = ["N°", "Nombre", "Descripción", "Criterios de Aceptación"]
WIDTHS = [8, 28, 50, 70]
FIELDS = ["nombre", "rol", "accion", "beneficio", "criterios"]


def main():
    args = parse_args("Genera el Excel de historias de usuario")
    spec = load_spec(args.json, {"historias": list})
    check_items(spec["historias"], "historias", FIELDS)
    if not spec["historias"]:
        fail("historias está vacío: no hay historias de usuario para generar")

    wb = Workbook()
    wb.remove(wb.active)
    used = set()
    for module, stories in group_by_module(spec["historias"]).items():
        ws = wb.create_sheet(sheet_title(module, used))
        rows = [[f"{n}.0", s["nombre"], f"Como {s['rol']}, quiero {s['accion']} para {s['beneficio']}.", numbered(s["criterios"])]
                for n, s in enumerate(stories, 1)]
        write_table(ws, HEADERS, rows, WIDTHS, header_fill="A4C2F4", header_font_color="1F1F1F")
    save(lambda: wb.save(args.output), args.output)
    print(f"Written {args.output}")


if __name__ == "__main__":
    main()
