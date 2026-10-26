"""Human-readable PDF note (ReportLab, pure Python, works offline)."""
from __future__ import annotations
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from . import chain as chainmod

TEAL = colors.HexColor("#0F6B63")


def build_pdf(incident: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=15 * mm, bottomMargin=15 * mm,
                            title=f"FieldScribe {incident['incident_id']}")
    ss = getSampleStyleSheet()
    small = ParagraphStyle("small", parent=ss["BodyText"], fontSize=8, leading=10)
    cell = ParagraphStyle("cell", parent=ss["BodyText"], fontSize=9, leading=11)
    h = ParagraphStyle("h", parent=ss["Title"], textColor=TEAL, fontSize=18)
    story = [Paragraph("FieldScribe - Prehospital Care Record", h)]
    meta = [["Incident", incident["incident_id"], "Date", incident["incident_date"]],
            ["Responder", incident["responder"], "Patient", incident["patient_label"]]]
    t = Table(meta, colWidths=[25 * mm, 65 * mm, 20 * mm, 70 * mm])
    t.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 9), ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                           ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                           ("BOX", (0, 0), (-1, -1), 0.5, TEAL), ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey)]))
    story += [t, Spacer(1, 6 * mm)]

    rows = [["#", "Time", "Type", "Item", "Dose", "Route", "Conf.", "Review flags"]]
    flagged = []
    for link in incident["chain"]:
        p = link["payload"]
        dose = f"{p['dose_value']:g} {p.get('dose_unit') or ''}".strip() if p.get("dose_value") is not None else "-"
        det = "; ".join(f"{k}={v}" for k, v in (p.get("details") or {}).items())
        item = p["name"] + (f" ({det})" if det else "")
        rows.append([str(link["index"] + 1), p.get("time") or "-", p["kind"].capitalize(),
                     Paragraph(item, cell), dose, p.get("route") or "-", f"{p.get('confidence', 0):.2f}",
                     Paragraph(", ".join(p.get("flags", [])) or ("confirmed" if p.get("confirmed") else "-"), cell)])
        if p.get("flags"):
            flagged.append(len(rows) - 1)
    if len(rows) == 1:
        rows.append(["", "", "", "No entries recorded", "", "", "", ""])
    t = Table(rows, repeatRows=1, colWidths=[8 * mm, 14 * mm, 22 * mm, 47 * mm, 22 * mm, 14 * mm, 14 * mm, 39 * mm])
    style = [("BACKGROUND", (0, 0), (-1, 0), TEAL), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
             ("FONTSIZE", (0, 0), (-1, -1), 9), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("GRID", (0, 0), (-1, -1), 0.25, colors.grey)]
    for r in flagged:
        style.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#FFF3CD")))
    t.setStyle(TableStyle(style))
    story += [t, Spacer(1, 6 * mm)]

    ok, bad = chainmod.verify(incident["chain"])
    head = incident["chain"][-1]["hash"] if incident["chain"] else chainmod.GENESIS
    verdict = "VERIFIED - chain intact" if ok else f"TAMPERING DETECTED at entry {bad + 1}"
    story += [Paragraph(f"<b>Audit chain:</b> {verdict}", ss["BodyText"]),
              Paragraph(f"Chain head (SHA-256): <font name='Courier'>{head}</font>", small),
              Paragraph("Rows shaded yellow carry review flags. Dose-range checks are illustrative and are not clinical "
                        "guidance. Generated on-device by FieldScribe; no real patient identifiers are stored.", small)]
    doc.build(story)
    return buf.getvalue()
