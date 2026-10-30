"""Build a SONDA-format user manual (.docx) from a JSON spec.

Usage: python build_manual.py spec.json "out/Manual de Usuario X V1.docx"

The template (sonda-manual-template.docx, next to this script) keeps the SONDA
cover, header/footer, change control, approval table and TOC. Only the body and
the {{PLACEHOLDERS}} are replaced. See references/spec-format.md for the schema.
"""
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

TEMPLATE = Path(__file__).with_name("sonda-manual-template.docx")
TEXT_WIDTH = 8828  # DXA, Letter page minus SONDA margins
EMU_PER_CM = 360000

BULLET_NUM_ID = "22"
DECIMAL_TEMPLATE_NUM_ID = "27"
CELL_PPR = '<w:pPr><w:spacing w:before="40" w:after="40" w:line="259" w:lineRule="auto"/><w:jc w:val="{}"/></w:pPr>'
MONO_RPR = '<w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
REQUIRED = ["title", "subtitle", "version", "version_date", "author", "change", "change_date", "body"]


def runs(text, rpr=""):
    """Plain text with **bold** spans -> <w:r> elements."""
    out = []
    for i, part in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if not part:
            continue
        props = rpr
        if i % 2:
            props = (rpr[:-len("</w:rPr>")] if rpr else "<w:rPr>") + "<w:b/><w:bCs/></w:rPr>"
        out.append(f'<w:r>{props}<w:t xml:space="preserve">{escape(part)}</w:t></w:r>')
    return "".join(out)


def para(text="", ppr="", rpr=""):
    return f"<w:p>{f'<w:pPr>{ppr}</w:pPr>' if ppr else ''}{runs(text, rpr)}</w:p>"


def labeled(label, text):
    if not text.lower().startswith(label.lower()):
        text = f"**{label}:** {text}"
    return para(text)


class Builder:
    def __init__(self, numbering_xml, base_dir):
        self.numbering = numbering_xml
        self.base_dir = base_dir
        self.media = []  # (zip name, bytes, rel id)
        self.next_num_id = max(int(n) for n in re.findall(r'<w:num w:numId="(\d+)"', numbering_xml)) + 1
        m = re.search(rf'<w:num w:numId="{DECIMAL_TEMPLATE_NUM_ID}"[^>]*>.*?<w:abstractNumId w:val="(\d+)"/>', numbering_xml, re.S)
        self.decimal_abstract = m.group(1)
        self.new_nums = []
        self.doc_pr_id = 1000

    def heading(self, level, text):
        if level == 1:
            return para(text, '<w:pStyle w:val="Ttulo1"/>')
        return para(text, f'<w:pStyle w:val="Ttulo{level}"/><w:numPr><w:ilvl w:val="{level - 1}"/><w:numId w:val="1"/></w:numPr>')

    def items(self, items, num_id):
        ppr = f'<w:pStyle w:val="Prrafodelista"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="{num_id}"/></w:numPr>'
        return "".join(para(t, ppr) for t in items)

    def steps(self, items):
        num_id = str(self.next_num_id)
        self.next_num_id += 1
        self.new_nums.append(
            f'<w:num w:numId="{num_id}"><w:abstractNumId w:val="{self.decimal_abstract}"/>'
            f'<w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/></w:lvlOverride></w:num>'
        )
        return self.items(items, num_id)

    def table(self, spec):
        header, rows = spec["header"], spec["rows"]
        n = len(header)
        weights = spec.get("widths") or [1] * n
        widths = [round(TEXT_WIDTH * w / sum(weights)) for w in weights]
        align = spec.get("align") or ["left"] * n

        def row(cells, is_header):
            tr_pr = (
                '<w:trPr><w:cnfStyle w:val="100000000000" w:firstRow="1" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" '
                'w:oddVBand="0" w:evenVBand="0" w:oddHBand="0" w:evenHBand="0" w:firstRowFirstColumn="0" w:firstRowLastColumn="0" '
                'w:lastRowFirstColumn="0" w:lastRowLastColumn="0"/><w:tblHeader/></w:trPr>'
                if is_header else "<w:trPr><w:cantSplit/></w:trPr>"
            )
            tcs = "".join(
                f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/><w:vAlign w:val="center"/></w:tcPr>'
                f'<w:p>{CELL_PPR.format("center" if is_header else a)}{runs(str(c))}</w:p></w:tc>'
                for c, w, a in zip(cells, widths, align)
            )
            return f"<w:tr>{tr_pr}{tcs}</w:tr>"

        grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
        body = row(header, True) + "".join(row(r, False) for r in rows)
        return (
            f'<w:tbl><w:tblPr><w:tblStyle w:val="TablaSONDA"/><w:tblW w:w="{TEXT_WIDTH}" w:type="dxa"/>'
            f'<w:tblLayout w:type="fixed"/><w:tblLook w:val="0420" w:firstRow="1" w:lastRow="0" w:firstColumn="0" '
            f'w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr><w:tblGrid>{grid}</w:tblGrid>{body}</w:tbl>'
            + para()  # Word needs a paragraph between consecutive tables / before headings
        )

    def code(self, lines):
        ppr = '<w:spacing w:after="0"/><w:ind w:left="284"/><w:jc w:val="left"/>'
        body = "".join(para(line, ppr, MONO_RPR) for line in lines)
        return body + para("", '<w:spacing w:after="0"/>')

    def glossary(self, terms):
        out = []
        for term, definition in sorted(terms, key=lambda t: t[0].lower()):
            out.append(para(f"**{term}**", '<w:keepNext/><w:spacing w:after="0"/>'))
            out.append(para(definition))
        return "".join(out)

    def image(self, spec):
        path = (self.base_dir / spec["path"]).resolve()
        ext = path.suffix.lower().lstrip(".")
        ext = "jpeg" if ext == "jpg" else ext
        if ext not in ("png", "jpeg"):
            raise SystemExit(f"Unsupported image type: {path}")
        data = path.read_bytes()
        w_px, h_px = image_size(data, ext)
        cx = int(spec.get("width_cm", 15) * EMU_PER_CM)
        cy = int(cx * h_px / w_px)
        rid = f"rIdManual{len(self.media) + 1}"
        name = f"media/manual_{len(self.media) + 1}.{ext}"
        self.media.append((name, data, rid))
        self.doc_pr_id += 1
        pid = self.doc_pr_id
        drawing = (
            f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
            f'<wp:docPr id="{pid}" name="Imagen {pid}"/><a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            f'<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr>'
            f'<pic:cNvPr id="{pid}" name="Imagen {pid}"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill>'
            f'<a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr>'
            f'<a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'</pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>'
        )
        out = f'<w:p><w:pPr><w:keepNext/><w:jc w:val="center"/></w:pPr>{drawing}</w:p>'
        if spec.get("caption"):
            out += para(spec["caption"], '<w:jc w:val="center"/>', '<w:rPr><w:i/><w:iCs/><w:color w:val="605E5C"/><w:sz w:val="20"/></w:rPr>')
        return out

    def block(self, b):
        (kind, value), = b.items()
        handlers = {
            "h1": lambda v: self.heading(1, v),
            "h2": lambda v: self.heading(2, v),
            "h3": lambda v: self.heading(3, v),
            "p": para,
            "bullets": lambda v: self.items(v, BULLET_NUM_ID),
            "steps": self.steps,
            "table": self.table,
            "example": lambda v: labeled("Ejemplo", v),
            "note": lambda v: labeled("Importante", v),
            "label": lambda v: para(f"**{v}**", "<w:keepNext/>"),
            "code": self.code,
            "glossary": self.glossary,
            "image": self.image,
            "page_break": lambda v: '<w:p><w:r><w:br w:type="page"/></w:r></w:p>',
        }
        if kind not in handlers:
            raise SystemExit(f"Unknown block type: {kind!r}")
        return handlers[kind](value)


def image_size(data, ext):
    if ext == "png":
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    i = 2
    while i < len(data):
        marker, length = data[i + 1], int.from_bytes(data[i + 2:i + 4], "big")
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            return int.from_bytes(data[i + 7:i + 9], "big"), int.from_bytes(data[i + 5:i + 7], "big")
        i += 2 + length
    raise SystemExit("Could not read JPEG size")


def main(spec_path, out_path):
    spec_path, out_path = Path(spec_path), Path(out_path)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED if k not in spec]
    if missing:
        raise SystemExit(f"Spec is missing keys: {missing}")

    src = zipfile.ZipFile(TEMPLATE)
    files = {i.filename: src.read(i.filename) for i in src.infolist()}
    builder = Builder(files["word/numbering.xml"].decode("utf-8"), spec_path.parent)
    body = "".join(builder.block(b) for b in spec["body"])

    values = {k.upper(): escape(str(spec[k])) for k in REQUIRED if k != "body"}

    def fill(xml):
        for key, val in values.items():
            xml = xml.replace("{{" + key + "}}", val)
        left = re.findall(r"\{\{[A-Z_]+\}\}", xml)
        if left:
            raise SystemExit(f"Unfilled placeholders: {left}")
        return xml

    doc = files["word/document.xml"].decode("utf-8").replace("<w:p><w:r><w:t>{{BODY}}</w:t></w:r></w:p>", body)
    files["word/document.xml"] = fill(doc).encode("utf-8")
    for name in ("word/header1.xml", "word/header2.xml", "docProps/core.xml"):
        files[name] = fill(files[name].decode("utf-8")).encode("utf-8")

    if builder.new_nums:
        num = builder.numbering
        anchor = "<w:numIdMacAtCleanup" if "<w:numIdMacAtCleanup" in num else "</w:numbering>"
        num = num.replace(anchor, "".join(builder.new_nums) + anchor, 1)
        files["word/numbering.xml"] = num.encode("utf-8")

    if builder.media:
        rels = files["word/_rels/document.xml.rels"].decode("utf-8")
        new = "".join(
            f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{name}"/>'
            for name, _, rid in builder.media
        )
        files["word/_rels/document.xml.rels"] = rels.replace("</Relationships>", new + "</Relationships>").encode("utf-8")
        ct = files["[Content_Types].xml"].decode("utf-8")
        for ext in {n.rsplit(".", 1)[1] for n, _, _ in builder.media}:
            if f'Extension="{ext}"' not in ct:
                ct = ct.replace("<Default ", f'<Default Extension="{ext}" ContentType="image/{ext}"/><Default ', 1)
        files["[Content_Types].xml"] = ct.encode("utf-8")
        for name, data, _ in builder.media:
            files["word/" + name] = data

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    shutil.move(tmp, out_path)
    print(f"Written {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
