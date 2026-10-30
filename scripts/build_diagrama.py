"""Build one general sequence diagram as an editable draw.io file from diagrama.json.

Usage: python build_diagrama.py --json diagrama.json --output "Diagrama X.drawio"
Schema by example: examples/diagrama.json
Layout is a fixed grid: one lifeline per participant, messages top to bottom in order.
"""
import xml.etree.ElementTree as ET

from spec_io import check_items, fail, load_spec, parse_args, save

COL_WIDTH, BOX_WIDTH, HEADER_HEIGHT = 200, 160, 40
TOP, FIRST_MSG, MSG_GAP, LOOP_WIDTH = 40, 110, 50, 40
LIFELINE_STYLE = ("shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=0;"
                  "collapsible=0;recursiveResize=0;outlineConnect=0;size=40;fillColor=#DAE8FC;strokeColor=#205DF5;")
MESSAGE_STYLE = "html=1;verticalAlign=bottom;endArrow=block;endFill=1;"
REPLY_STYLE = "html=1;verticalAlign=bottom;endArrow=open;dashed=1;"


def point(parent, x, y, role):
    ET.SubElement(parent, "mxPoint", x=str(x), y=str(y), **{"as": role})


def build(spec):
    participants, messages = spec["participantes"], spec["mensajes"]
    center = {name: TOP + i * COL_WIDTH + BOX_WIDTH / 2 for i, name in enumerate(participants)}
    height = FIRST_MSG + len(messages) * MSG_GAP

    mxfile = ET.Element("mxfile", host="ariadna")
    diagram = ET.SubElement(mxfile, "diagram", name=spec["titulo"], id="secuencia-general")
    model = ET.SubElement(diagram, "mxGraphModel", grid="1", gridSize="10", page="1", pageWidth="1169", pageHeight="827")
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    for i, name in enumerate(participants):
        cell = ET.SubElement(root, "mxCell", id=f"p{i}", value=name, style=LIFELINE_STYLE, vertex="1", parent="1")
        ET.SubElement(cell, "mxGeometry", x=str(TOP + i * COL_WIDTH), y=str(TOP), width=str(BOX_WIDTH),
                      height=str(height), **{"as": "geometry"})

    for j, msg in enumerate(messages):
        y = TOP + FIRST_MSG + j * MSG_GAP
        style = REPLY_STYLE if msg.get("respuesta") else MESSAGE_STYLE
        cell = ET.SubElement(root, "mxCell", id=f"m{j}", value=msg["texto"], style=style, edge="1", parent="1")
        geo = ET.SubElement(cell, "mxGeometry", relative="1", **{"as": "geometry"})
        x1, x2 = center[msg["de"]], center[msg["a"]]
        if x1 == x2:  # self-message: small loop to the right of the lifeline
            point(geo, x1, y, "sourcePoint")
            point(geo, x1, y + MSG_GAP / 2, "targetPoint")
            waypoints = ET.SubElement(geo, "Array", **{"as": "points"})
            ET.SubElement(waypoints, "mxPoint", x=str(x1 + LOOP_WIDTH), y=str(y))
            ET.SubElement(waypoints, "mxPoint", x=str(x1 + LOOP_WIDTH), y=str(y + MSG_GAP / 2))
        else:
            point(geo, x1, y, "sourcePoint")
            point(geo, x2, y, "targetPoint")
    return ET.ElementTree(mxfile)


def main():
    args = parse_args("Genera el diagrama de secuencia general en formato draw.io")
    spec = load_spec(args.json, {"titulo": str, "participantes": list, "mensajes": list})
    participants = spec["participantes"]
    if not participants or not all(isinstance(p, str) and p.strip() for p in participants):
        fail("participantes debe ser una lista de nombres no vacía")
    if len(set(participants)) != len(participants):
        fail("participantes tiene nombres repetidos")
    check_items(spec["mensajes"], "mensajes", ["de", "a", "texto"])
    for i, msg in enumerate(spec["mensajes"]):
        for role in ("de", "a"):
            if msg[role] not in participants:
                fail(f"mensajes[{i}].{role} = {msg[role]!r} no está en participantes")

    tree = build(spec)
    ET.indent(tree)
    save(lambda: tree.write(args.output, encoding="utf-8", xml_declaration=False), args.output)
    print(f"Written {args.output}")


if __name__ == "__main__":
    main()
