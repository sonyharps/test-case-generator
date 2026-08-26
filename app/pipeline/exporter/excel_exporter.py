"""
Excel Exporter — produces a multi-sheet .xlsx test-case report from an
orchestrator result.

Sheets:
  1. Summary        — requirement metadata, key features, risk
  2. Functional     — happy-path test cases
  3. Negative       — error-handling test cases
  4. Boundary       — edge-case / boundary test cases
  5. Coverage       — counts per category + total

Designed to mirror the PDF exporter's `generate_pdf(result, requirement, model)`
contract so the API endpoint can swap formats trivially.
"""

import io
from typing import Any, Dict, List
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.core.logging_config import get_logger

logger = get_logger(__name__)


# ---- Styling helpers ----
_HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
_HEADER_FILL = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
_TITLE_FONT = Font(bold=True, size=14, color="1E3A8A")
_LABEL_FONT = Font(bold=True, size=10)
_WRAP_ALIGN = Alignment(wrap_text=True, vertical="top")
_THIN_BORDER = Border(
    left=Side(style="thin", color="D1D5DB"),
    right=Side(style="thin", color="D1D5DB"),
    top=Side(style="thin", color="D1D5DB"),
    bottom=Side(style="thin", color="D1D5DB"),
)

# Alternating row fills per category sheet for readability
_CATEGORY_FILLS = {
    "functional": PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid"),
    "negative": PatternFill(start_color="FEF2F2", end_color="FEF2F2", fill_type="solid"),
    "boundary": PatternFill(start_color="FFFBEB", end_color="FFFBEB", fill_type="solid"),
}

_TC_COLUMNS = [
    ("TC ID", 14),
    ("Priority", 10),
    ("Module", 18),
    ("Title", 40),
    ("Preconditions", 35),
    ("Test Data", 35),
    ("Steps", 50),
    ("Expected Result", 45),
    ("Postconditions", 30),
]

# Priority-based row tints (applied to the Priority cell only)
_PRIORITY_FILLS = {
    "P0": PatternFill(start_color="DC2626", end_color="DC2626", fill_type="solid"),  # red
    "P1": PatternFill(start_color="EA580C", end_color="EA580C", fill_type="solid"),  # orange
    "P2": PatternFill(start_color="CA8A04", end_color="CA8A04", fill_type="solid"),  # amber
    "P3": PatternFill(start_color="16A34A", end_color="16A34A", fill_type="solid"),  # green
}
_PRIORITY_FONT = Font(bold=True, color="FFFFFF", size=10)


def _safe_list_join(value: Any, sep: str = "\n") -> str:
    """Coerce list/dict/str values into a newline-joined display string."""
    if value is None:
        return ""
    if isinstance(value, list):
        parts = []
        for i, item in enumerate(value, start=1):
            if isinstance(item, dict):
                # {"action": "..."} / {"result": "..."} style
                txt = " ".join(str(v) for v in item.values() if v is not None)
                parts.append(f"{i}. {txt}" if txt else "")
            else:
                txt = str(item)
                # Models sometimes pre-number steps ("1. Klik..."); don't
                # double-number those — only prefix items lacking a number.
                import re as _re
                if _re.match(r"^\s*\d+[\.\)]\s", txt):
                    parts.append(txt)
                else:
                    parts.append(f"{i}. {txt}")
        return sep.join(p for p in parts if p)
    return str(value)


def _write_tc_sheet(ws, category: str, test_cases: List[Dict[str, Any]]):
    """Write one test-case category sheet."""
    # Header row
    for col_idx, (label, _width) in enumerate(_TC_COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=label)
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = Alignment(vertical="center", horizontal="left")
        cell.border = _THIN_BORDER

    # Column widths
    for col_idx, (_label, width) in enumerate(_TC_COLUMNS, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    # Freeze header
    ws.freeze_panes = "A2"

    # Body rows
    row_fill = _CATEGORY_FILLS.get(category)
    for r, tc in enumerate(test_cases, start=2):
        priority = (tc.get("priority") or "P2").upper()
        values = [
            tc.get("tc_id", ""),
            priority,
            tc.get("module", ""),
            tc.get("title", ""),
            _safe_list_join(tc.get("preconditions")),
            _safe_list_join(tc.get("test_data")),
            _safe_list_join(tc.get("steps")),
            _safe_list_join(tc.get("expected_result")),
            _safe_list_join(tc.get("postconditions")),
        ]
        for c, val in enumerate(values, start=1):
            cell = ws.cell(row=r, column=c, value=val)
            cell.alignment = _WRAP_ALIGN
            cell.border = _THIN_BORDER
            if row_fill is not None:
                cell.fill = row_fill
            # Color the Priority cell (column 2) with priority-based fill
            if c == 2:
                pfill = _PRIORITY_FILLS.get(priority)
                if pfill is not None:
                    cell.fill = pfill
                    cell.font = _PRIORITY_FONT
                    cell.alignment = Alignment(horizontal="center", vertical="center")

    # Auto row height is unreliable; set a reasonable default for content rows.
    for r in range(2, len(test_cases) + 2):
        ws.row_dimensions[r].height = 60


def _write_summary_sheet(ws, result: Dict[str, Any], requirement: str, model: str):
    """Write the Summary sheet (metadata + key features + risk)."""
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 70

    ws["A1"] = "Test Case Generation Report"
    ws["A1"].font = _TITLE_FONT
    ws.merge_cells("A1:B1")

    summary = result.get("summary") or {}
    if isinstance(summary, str):
        summary = {}

    risk = result.get("risk") or {}
    metadata = result.get("metadata") or {}

    rows = [
        ("Generated At", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")),
        ("Model", model),
        ("Pipeline", metadata.get("pipeline", "—")),
        ("Requirement", requirement[:500] if requirement else "—"),
        ("", ""),
        ("ID", summary.get("id", "—")),
        ("Nama", summary.get("nama") or summary.get("judul") or "—"),
        ("Deskripsi", summary.get("deskripsi") or summary.get("description") or "—"),
        ("Prioritas", summary.get("prioritas", "—")),
        ("Kategori", summary.get("kategori", "—")),
        ("", ""),
        ("Risk Level", risk.get("level", "—")),
    ]

    for r, (label, value) in enumerate(rows, start=3):
        ws.cell(row=r, column=1, value=label).font = _LABEL_FONT
        cell = ws.cell(row=r, column=2, value=value)
        cell.alignment = _WRAP_ALIGN

    # Key features list
    fitur = summary.get("fitur_kunci") or summary.get("fiturKunci") or []
    if fitur:
        start = len(rows) + 4
        ws.cell(row=start, column=1, value="Fitur Kunci").font = _LABEL_FONT
        for i, f in enumerate(fitur, start=start + 1):
            ws.cell(row=i, column=1, value=f"• {f}")

    # Risk notes
    notes = risk.get("notes") or []
    if notes:
        notes_start = len(rows) + 4 + len(fitur) + 2
        ws.cell(row=notes_start, column=1, value="Risk Notes").font = _LABEL_FONT
        for i, note in enumerate(notes, start=notes_start + 1):
            ws.cell(row=i, column=1, value=f"• {note}").alignment = _WRAP_ALIGN
            ws.merge_cells(start_row=i, start_column=1, end_row=i, end_column=2)


def _write_coverage_sheet(ws, result: Dict[str, Any]):
    """Write the Coverage sheet with per-category counts."""
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 14

    ws["A1"] = "Coverage Summary"
    ws["A1"].font = _TITLE_FONT

    functional = result.get("functional") or []
    negative = result.get("negative") or []
    boundary = result.get("boundary") or []
    total = len(functional) + len(negative) + len(boundary)

    rows = [
        ("Category", "Count"),
        ("Functional", len(functional)),
        ("Negative", len(negative)),
        ("Boundary", len(boundary)),
        ("TOTAL", total),
    ]

    for r, (label, count) in enumerate(rows, start=3):
        a = ws.cell(row=r, column=1, value=label)
        b = ws.cell(row=r, column=2, value=count)
        if r == 3:  # header
            a.font = _HEADER_FONT; a.fill = _HEADER_FILL
            b.font = _HEADER_FONT; b.fill = _HEADER_FILL
        elif label == "TOTAL":
            a.font = Font(bold=True); b.font = Font(bold=True)


class ExcelExporter:
    """Exports orchestrator results to a styled .xlsx workbook."""

    def generate_excel(
        self,
        result: Dict[str, Any],
        requirement: str,
        model: str,
    ) -> bytes:
        """Build the .xlsx file and return it as in-memory bytes.

        Args:
            result: Orchestrator result dict (summary/functional/negative/
                    boundary/risk/metadata).
            requirement: The originating requirement text.
            model: Model identifier used for generation.

        Returns:
            .xlsx file content as bytes.
        """
        wb = Workbook()

        # Sheet 1: Summary
        ws_summary = wb.active
        ws_summary.title = "Summary"
        _write_summary_sheet(ws_summary, result, requirement, model)

        # Sheets 2-4: test-case categories
        for idx, category in enumerate(["functional", "negative", "boundary"], start=0):
            ws = wb.create_sheet(title=category.capitalize())
            _write_tc_sheet(ws, category, result.get(category) or [])

        # Sheet 5: Coverage
        ws_cov = wb.create_sheet(title="Coverage")
        _write_coverage_sheet(ws_cov, result)

        # Serialize to bytes
        buf = io.BytesIO()
        wb.save(buf)
        data = buf.getvalue()

        logger.info(
            "excel_export_success",
            size_bytes=len(data),
            functional=len(result.get("functional") or []),
            negative=len(result.get("negative") or []),
            boundary=len(result.get("boundary") or []),
        )
        return data


# Singleton instance
excel_exporter = ExcelExporter()
