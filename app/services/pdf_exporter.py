from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import tempfile
import os

def export_tc_pdf(testcases: list, filename: str = "testcases.pdf"):
    styles = getSampleStyleSheet()
    style = styles["Normal"]

    # Make landscape PDF
    pdf_path = os.path.join(tempfile.gettempdir(), filename)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(A4),
        leftMargin=20,
        rightMargin=20,
        topMargin=20,
        bottomMargin=20
    )

    # Wider landscape columns
    column_widths = [70, 140, 150, 150, 150]

    # Header row
    table_data = [
        [
            Paragraph("TC ID", style),
            Paragraph("Judul", style),
            Paragraph("Prasyarat", style),
            Paragraph("Langkah", style),
            Paragraph("Hasil yang Diharapkan", style)
        ]
    ]

    # Rows
    for tc in testcases:
        table_data.append([
            Paragraph(tc["tc_id"], style),
            Paragraph(tc["title"], style),
            Paragraph("<br/>".join(tc["preconditions"]), style),
            Paragraph("<br/>".join(tc["steps"]), style),
            Paragraph("<br/>".join(tc["expected_result"]), style),
        ])

    # Create table
    table = Table(table_data, colWidths=column_widths, repeatRows=1)

    # Styling
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    ]))

    doc.build([table])
    return pdf_path
