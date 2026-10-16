from io import BytesIO
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def generate_financial_summary_pdf(summary: dict) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize=A4, title="HisabDo Financial Summary"
    )
    styles = getSampleStyleSheet()
    content = [
        Paragraph("HisabDo Financial Summary", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Generated on: {date.today()}", styles["Normal"]),
        Spacer(1, 12),
    ]

    if str(summary.get("source", "")).startswith("MOCK_BACKEND_CLIENT"):
        content.extend([
            Paragraph(
                "<b>DEMO DATA ONLY</b> This is sample data, not actual user data.",
                styles["Normal"],
            ),
            Spacer(1, 12),
        ])

    currency = summary.get("currency", "PKR")
    rows = [
        ["Item", "Amount"],
        ["Current balance", f"{summary['balance']} {currency}"],
        ["Expenses this month", f"{summary['total_expenses_this_month']} {currency}"],
        ["Revenue this month", f"{summary['total_revenue_this_month']} {currency}"],
        ["Outstanding receivables", f"{summary['outstanding_receivables']} {currency}"],
    ]
    table = Table(rows, colWidths=[270, 180])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    content.append(table)
    document.build(content)
    return buffer.getvalue()
