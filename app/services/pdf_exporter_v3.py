# app/services/pdf_exporter_v3.py

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS


def export_orchestrator_pdf_v3(
    data: dict,
    *,
    requirement: str,
    model_used: str,
    output_path: str = "orchestrator_report.pdf",
) -> str:
    """
    Render orchestrator result -> nice PDF (blue / orange / purple theme)
    using HTML+CSS (WeasyPrint).

    data: hasil dari app.services.orchestrator.orchestrate()
    requirement: requirement asli dari user
    model_used: nama model (llama3.1:8b, dsb)
    output_path: nama file pdf output
    """

    # --- siapkan context ---
    ctx = dict(data)  # copy biar aman
    ctx["requirement"] = requirement
    ctx["model_used"] = model_used

    # --- path template ---
    base_dir = Path(__file__).resolve().parent.parent  # app/
    template_dir = base_dir / "templates"

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    template = env.get_template("orchestrator_report.html")
    html_string = template.render(**ctx)

    html = HTML(string=html_string, base_url=str(template_dir))
    css = CSS(filename=str(template_dir / "report_style.css"))

    html.write_pdf(target=output_path, stylesheets=[css])

    return output_path
