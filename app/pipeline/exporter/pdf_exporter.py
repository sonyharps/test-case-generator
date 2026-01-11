from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Dict, Any
import io

class PDFExporter:
    """
    Export orchestrator results to PDF using existing HTML templates
    """

    def __init__(self):
        template_dir = Path(__file__).parent.parent.parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))

    def generate_pdf(self, result: Dict[str, Any], requirement: str, model: str) -> bytes:
        """
        Generate PDF from orchestrator result

        Args:
            result: OrchestratorResult dict with functional, negative, boundary, summary, risk, coverage_matrix
            requirement: Original requirement text
            model: Model name used

        Returns:
            PDF bytes
        """
        # Load template
        template = self.env.get_template("orchestrator_report.html")

        # Prepare context with safe defaults for None values
        context = {
            "requirement": requirement or "No requirement specified",
            "model_used": model or "Unknown",
            "functional": result.get("functional") or [],
            "negative": result.get("negative") or [],
            "boundary": result.get("boundary") or [],
            "summary": result.get("summary") or {},
            "risk": result.get("risk") or {"level": "N/A", "notes": []},
            "coverage_matrix": self._normalize_coverage(result.get("coverage_matrix")),
            "metadata": result.get("metadata") or {}
        }

        # Render HTML
        html_content = template.render(**context)

        # Generate PDF
        pdf_bytes = HTML(string=html_content).write_pdf()

        return pdf_bytes

    def _normalize_coverage(self, coverage: Dict[str, Any]) -> Dict[str, int]:
        """Normalize coverage matrix to expected format"""
        # Handle None or empty coverage
        if not coverage or not isinstance(coverage, dict):
            return {
                "functional_count": 0,
                "negative_count": 0,
                "boundary_count": 0,
                "total": 0
            }

        return {
            "functional_count": coverage.get("functional", coverage.get("functional_count", 0)),
            "negative_count": coverage.get("negative", coverage.get("negative_count", 0)),
            "boundary_count": coverage.get("boundary", coverage.get("boundary_count", 0)),
            "total": coverage.get("total", 0)
        }
