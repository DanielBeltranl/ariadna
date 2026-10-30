"""Build the use cases workbook (.xlsx) from casos.json, one sheet per module.

Usage: python build_casos_uso.py --json casos.json --output "Casos de Uso X.xlsx"
Schema by example: examples/casos.json · Format reference: "Casos de uso ejemplo.xlsx"
"""
from openpyxl import Workbook

from spec_io import check_items, fail, load_spec, parse_args, save
from xlsx_sheets import group_by_module, numbered, sheet_title, write_table

HEADERS = ["ID", "Caso de Uso", "Actor", "Precondiciones", "Flujo de Pasos", "Resultado Esperado"]
WIDTHS = [10, 30, 22, 32, 55, 35]
FIELDS = ["id", "titulo", "actor", "precondiciones", "pasos", "resultado"]


def main():
    args = parse_args("Genera el Excel de casos de uso")
    spec = load_spec(args.json, {"casos": list})
    check_items(spec["casos"], "casos", FIELDS)
    if not spec["casos"]:
        fail("casos está vacío: no hay casos de uso viables para generar")

    wb = Workbook()
    wb.remove(wb.active)
    used = set()
    for module, cases in group_by_module(spec["casos"]).items():
        ws = wb.create_sheet(sheet_title(module, used))
        rows = [[c["id"], c["titulo"], c["actor"], c["precondiciones"], numbered(c["pasos"]), c["resultado"]] for c in cases]
        write_table(ws, HEADERS, rows, WIDTHS, header_fill="535FC1", header_font_color="FFFFFF",
                    stripe_fills=["FFFFFF", "F6F8F9"])
    save(lambda: wb.save(args.output), args.output)
    print(f"Written {args.output}")


if __name__ == "__main__":
    main()
