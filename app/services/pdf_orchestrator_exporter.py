from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    ListFlowable,
    ListItem,
)
from reportlab.lib import colors


# =========================
# SAFE TEXT SANITIZER
# =========================
def safe_text(text):
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    # Escape HTML-ish chars because Paragraph pakai mini-HTML
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br />")
    )


# =========================
# BULLET LIST HELPER
# =========================
def bullet_list(items, style):
    """Return ListFlowable for bullet list (kalau items nggak kosong)."""
    if not items:
        return None
    list_items = [
        ListItem(Paragraph(safe_text(it), style), leftIndent=15, value="bullet")
        for it in items
    ]
    return ListFlowable(
        list_items,
        bulletType="bullet",
        start="•",
        leftIndent=10,
        bulletFontName="Helvetica",
        bulletFontSize=8,
        bulletOffsetY=0,
    )


# =========================
# RENDER TEST CASE BLOCK
# =========================
def render_test_case(story, tc, normal_style, small_style):
    tc_id = safe_text(tc.get("tc_id", "TC-XXX"))
    title = safe_text(tc.get("title", "Untitled Test Case"))

    # Header per test case
    story.append(
        Paragraph(f"<b>{tc_id}</b> — {title}", normal_style)
    )
    story.append(Spacer(1, 4))

    # Preconditions
    pre = tc.get("preconditions", [])
    if pre:
        story.append(Paragraph("<b>Preconditions:</b>", small_style))
        bl = bullet_list(pre, small_style)
        if bl:
            story.append(bl)
            story.append(Spacer(1, 4))

    # Steps
    steps = tc.get("steps", [])
    if steps:
        story.append(Paragraph("<b>Steps:</b>", small_style))
        bl = bullet_list(steps, small_style)
        if bl:
            story.append(bl)
            story.append(Spacer(1, 4))

    # Expected Result
    exp = tc.get("expected_result", [])
    if exp:
        story.append(Paragraph("<b>Expected Result:</b>", small_style))
        bl = bullet_list(exp, small_style)
        if bl:
            story.append(bl)
            story.append(Spacer(1, 4))

    # Divider setiap TC
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            '<font size="8" color="grey">────────────────────────────────────────────────────</font>',
            small_style,
        )
    )
    story.append(Spacer(1, 8))


# ==========================================================
# MAIN EXPORT FUNCTION — dipanggil dari FastAPI
# ==========================================================
def export_orchestrator_pdf(
    data: dict,
    *,
    requirement: str,
    model_used: str,
    output_path: str = "orchestrator_report.pdf",
):
    """
    data: hasil penuh dari orchestrator.py
    requirement: text requirement dari API
    model_used: nama model (misal 'llama3.1:8b')
    """

    # Inject requirement & model ke data (kalau mau dipakai ke depan)
    data["requirement"] = requirement
    data["model_used"] = model_used

    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        leftMargin=30,
        rightMargin=30,
        topMargin=25,
        bottomMargin=25,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=22,
        spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=16,
        spaceAfter=10,
    )
    normal_style = ParagraphStyle(
        "Normal",
        parent=styles["BodyText"],
        fontSize=11,
        leading=14,
        spaceAfter=6,
    )
    small_style = ParagraphStyle(
        "Small",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
        spaceAfter=2,
    )

    story = []

    # ======================================================
    # 1. COVER PAGE
    # ======================================================
    story.append(Paragraph("AI Test Case Orchestrator Report", title_style))
    story.append(Paragraph(f"Requirement: <b>{safe_text(requirement)}</b>", normal_style))
    story.append(Paragraph(f"Model Used: {safe_text(model_used)}", normal_style))

    meta_time = safe_text(data.get("metadata", {}).get("time", "N/A"))
    story.append(Paragraph(f"Generated At: {meta_time}", normal_style))

    cov = data.get("coverage_matrix", {})
    functional_count = cov.get("functional_count", 0)
    negative_count = cov.get("negative_count", 0)
    boundary_count = cov.get("boundary_count", 0)
    total_count = functional_count + negative_count + boundary_count

    story.append(Spacer(1, 20))
    cov_table = Table(
        [
            ["Functional", "Negative", "Boundary", "Total"],
            [functional_count, negative_count, boundary_count, total_count],
        ],
        colWidths=[120, 120, 120, 120],
    )
    cov_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(cov_table)

    story.append(Spacer(1, 40))
    story.append(PageBreak())

    # ======================================================
    # 2. SUMMARY
    # ======================================================
    story.append(Paragraph("1. Summary", heading_style))
    summary_text = safe_text(data.get("summary", ""))
    story.append(Paragraph(summary_text, normal_style))
    story.append(Spacer(1, 20))

    # ======================================================
    # 3. RISK ASSESSMENT
    # ======================================================
    story.append(Paragraph("2. Risk Assessment", heading_style))

    risk = data.get("risk", {}) or {}
    risk_level = str(risk.get("level", "unknown")).lower()
    risk_notes_list = risk.get("notes", []) or []
    risk_notes = "<br />".join(safe_text(n) for n in risk_notes_list) or "-"

    # Warna berdasarkan level
    level_color = colors.lightgrey
    if risk_level == "high":
        level_color = colors.red
    elif risk_level == "medium":
        level_color = colors.orange
    elif risk_level == "low":
        level_color = colors.green

    risk_table = Table(
        [
            ["Level", "Notes"],
            [risk_level.upper(), risk_notes],
        ],
        colWidths=[120, 560],
    )
    risk_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("BACKGROUND", (0, 1), (0, 1), level_color),
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(risk_table)

    story.append(Spacer(1, 30))
    story.append(PageBreak())

    # ======================================================
    # 4. FUNCTIONAL TEST CASES
    # ======================================================
    story.append(Paragraph("3. Functional Test Cases", heading_style))
    functional = data.get("functional", []) or []
    if not functional:
        story.append(Paragraph("No functional test cases generated.", normal_style))
    else:
        for idx, tc in enumerate(functional, start=1):
            render_test_case(story, tc, normal_style, small_style)

    story.append(PageBreak())

    # ======================================================
    # 5. NEGATIVE TEST CASES
    # ======================================================
    story.append(Paragraph("4. Negative Test Cases", heading_style))
    negative = data.get("negative", []) or []
    if not negative:
        story.append(Paragraph("No negative test cases generated.", normal_style))
    else:
        for idx, tc in enumerate(negative, start=1):
            render_test_case(story, tc, normal_style, small_style)

    story.append(PageBreak())

    # ======================================================
    # 6. BOUNDARY TEST CASES
    # ======================================================
    story.append(Paragraph("5. Boundary Test Cases", heading_style))
    boundary = data.get("boundary", []) or []
    if not boundary:
        story.append(Paragraph("No boundary test cases generated.", normal_style))
    else:
        for idx, tc in enumerate(boundary, start=1):
            render_test_case(story, tc, normal_style, small_style)

    # ======================================================
    # BUILD PDF
    # ======================================================
    doc.build(story)
    return output_path
