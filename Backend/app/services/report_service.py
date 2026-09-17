
from io import BytesIO

from markdown import markdown

from jinja2 import Template

from reportlab.lib.pagesizes import A4

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from reportlab.lib.enums import TA_CENTER

from reportlab.lib.units import mm

from reportlab.platypus import (

    SimpleDocTemplate,

    Paragraph,

    Spacer,

    Table,

    TableStyle,

    PageBreak,

)

from reportlab.lib import colors

from app.core.errors import AppError

# ============================================================

# HTML REPORT TEMPLATE

# ============================================================

REPORT_TEMPLATE = """

<!DOCTYPE html>

<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta

        name="viewport"

        content="width=device-width, initial-scale=1.0"

    >

    <title>

        SolutionForge AI - Solution Blueprint

    </title>

    <style>

        body {

            font-family: Arial, Helvetica, sans-serif;

            line-height: 1.6;

            max-width: 1000px;

            margin: 0 auto;

            padding: 40px 24px;

            color: #222;

            background: #ffffff;

        }

        h1 {

            font-size: 32px;

            margin-bottom: 24px;

        }

        h2 {

            font-size: 24px;

            margin-top: 32px;

            border-bottom: 1px solid #ddd;

            padding-bottom: 8px;

        }

        h3 {

            font-size: 20px;

            margin-top: 24px;

        }

        h4 {

            font-size: 18px;

            margin-top: 20px;

        }

        p {

            margin: 12px 0;

        }

        ul,

        ol {

            padding-left: 28px;

        }

        li {

            margin-bottom: 6px;

        }

        code {

            font-family: monospace;

            background: #f4f4f4;

            padding: 2px 5px;

            border-radius: 4px;

        }

        pre {

            background: #f4f4f4;

            padding: 16px;

            overflow-x: auto;

            border-radius: 6px;

        }

        pre code {

            background: transparent;

            padding: 0;

        }

        blockquote {

            margin: 16px 0;

            padding-left: 16px;

            border-left: 4px solid #ccc;

            color: #555;

        }

        table {

            width: 100%;

            border-collapse: collapse;

            margin: 20px 0;

        }

        th,

        td {

            border: 1px solid #ddd;

            padding: 10px;

            text-align: left;

        }

        th {

            background: #f4f4f4;

        }

        hr {

            border: 0;

            border-top: 1px solid #ddd;

            margin: 30px 0;

        }

        @media print {

            body {

                max-width: none;

                padding: 20px;

            }

        }

    </style>

</head>

<body>

    {{ content }}

</body>

</html>

"""

# ============================================================

# HTML REPORT GENERATION

# ============================================================

def render_report(blueprint_md: str) -> str:

    """

    Convert a Markdown solution blueprint into

    a styled HTML report.

    Flow:

        Markdown

            ↓

        HTML content

            ↓

        Jinja2 template

            ↓

        Styled HTML report

    """

    if not blueprint_md:

        raise AppError(

            message="Blueprint Markdown is empty.",

            status_code=500,

            error_code="REPORT_GENERATION_ERROR",

        )

    try:

        # Convert Markdown into HTML

        html_content = markdown(

            blueprint_md,

            extensions=[

                "tables",

                "fenced_code",

                "toc",

            ],

        )

        # Apply HTML template

        template = Template(

            REPORT_TEMPLATE

        )

        rendered_html = template.render(

            content=html_content

        )

        if not rendered_html:

            raise AppError(

                message="Report rendering returned an empty result.",

                status_code=500,

                error_code="REPORT_GENERATION_ERROR",

            )

        return rendered_html

    except AppError:

        raise

    except Exception as exc:

        raise AppError(

            message="Failed to generate HTML report.",

            status_code=500,

            error_code="REPORT_GENERATION_ERROR",

        ) from exc

# ============================================================

# PDF REPORT GENERATION

# ============================================================

def generate_pdf(blueprint_md: str) -> bytes:

    """

    Convert the Markdown solution blueprint into a PDF.

    The PDF is generated in memory and returned as bytes.

    Flow:

        Markdown

            ↓

        Markdown → HTML

            ↓

        Extract readable content

            ↓

        ReportLab

            ↓

        PDF bytes

    """

    if not blueprint_md:

        raise AppError(

            message="Blueprint Markdown is empty.",

            status_code=500,

            error_code="REPORT_GENERATION_ERROR",

        )

    try:

        # ----------------------------------------------------

        # Convert Markdown to HTML

        # ----------------------------------------------------

        html_content = markdown(

            blueprint_md,

            extensions=[

                "tables",

                "fenced_code",

            ],

        )

        # ----------------------------------------------------

        # Create PDF in memory

        # ----------------------------------------------------

        pdf_buffer = BytesIO()

        document = SimpleDocTemplate(

            pdf_buffer,

            pagesize=A4,

            rightMargin=18 * mm,

            leftMargin=18 * mm,

            topMargin=18 * mm,

            bottomMargin=18 * mm,

            title="SolutionForge AI - Solution Blueprint",

            author="SolutionForge AI",

        )

        # ----------------------------------------------------

        # PDF styles

        # ----------------------------------------------------

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(

            "CustomTitle",

            parent=styles["Title"],

            fontSize=24,

            leading=30,

            alignment=TA_CENTER,

            spaceAfter=20,

        )

        heading1_style = ParagraphStyle(

            "CustomHeading1",

            parent=styles["Heading1"],

            fontSize=18,

            leading=22,

            spaceBefore=16,

            spaceAfter=10,

        )

        heading2_style = ParagraphStyle(

            "CustomHeading2",

            parent=styles["Heading2"],

            fontSize=15,

            leading=19,

            spaceBefore=12,

            spaceAfter=8,

        )

        heading3_style = ParagraphStyle(

            "CustomHeading3",

            parent=styles["Heading3"],

            fontSize=13,

            leading=17,

            spaceBefore=10,

            spaceAfter=6,

        )

        body_style = ParagraphStyle(

            "CustomBody",

            parent=styles["BodyText"],

            fontSize=10,

            leading=15,

            spaceAfter=7,

        )

        bullet_style = ParagraphStyle(

            "CustomBullet",

            parent=body_style,

            leftIndent=15,

            firstLineIndent=-8,

            spaceAfter=4,

        )

        code_style = ParagraphStyle(

            "CustomCode",

            parent=body_style,

            fontName="Courier",

            fontSize=8,

            leading=11,

            leftIndent=10,

            rightIndent=10,

            spaceBefore=6,

            spaceAfter=6,

        )

        # ----------------------------------------------------

        # Build PDF content

        # ----------------------------------------------------

        story = []

        # Split Markdown into lines

        lines = blueprint_md.splitlines()

        first_heading = True

        for line in lines:

            stripped = line.strip()

            # Ignore empty lines

            if not stripped:

                story.append(

                    Spacer(1, 4)

                )

                continue

            # ------------------------------------------------

            # H1

            # ------------------------------------------------

            if stripped.startswith("# "):

                text = stripped[2:].strip()

                if first_heading:

                    story.append(

                        Paragraph(

                            _escape_pdf_text(text),

                            title_style,

                        )

                    )

                    first_heading = False

                else:

                    story.append(

                        Paragraph(

                            _escape_pdf_text(text),

                            heading1_style,

                        )

                    )

                continue

            # ------------------------------------------------

            # H2

            # ------------------------------------------------

            if stripped.startswith("## "):

                text = stripped[3:].strip()

                story.append(

                    Paragraph(

                        _escape_pdf_text(text),

                        heading1_style,

                    )

                )

                continue

            # ------------------------------------------------

            # H3

            # ------------------------------------------------

            if stripped.startswith("### "):

                text = stripped[4:].strip()

                story.append(

                    Paragraph(

                        _escape_pdf_text(text),

                        heading2_style,

                    )

                )

                continue

            # ------------------------------------------------

            # H4

            # ------------------------------------------------

            if stripped.startswith("#### "):

                text = stripped[5:].strip()

                story.append(

                    Paragraph(

                        _escape_pdf_text(text),

                        heading3_style,

                    )

                )

                continue

            # ------------------------------------------------

            # Bullet points

            # ------------------------------------------------

            if stripped.startswith("- "):

                text = stripped[2:].strip()

                story.append(

                    Paragraph(

                        "• "

                        + _escape_pdf_text(text),

                        bullet_style,

                    )

                )

                continue

            # ------------------------------------------------

            # Numbered list

            # ------------------------------------------------

            if _is_numbered_list(stripped):

                text = _remove_number_prefix(

                    stripped

                )

                story.append(

                    Paragraph(

                        _escape_pdf_text(text),

                        bullet_style,

                    )

                )

                continue

            # ------------------------------------------------

            # Horizontal rule

            # ------------------------------------------------

            if stripped in {

                "---",

                "***",

                "___",

            }:

                story.append(

                    Spacer(1, 8)

                )

                continue

            # ------------------------------------------------

            # Code block

            # ------------------------------------------------

            if stripped.startswith("```"):

                continue

            # ------------------------------------------------

            # Markdown table

            # ------------------------------------------------

            if "|" in stripped:

                # Table handling is intentionally kept

                # simple for the MVP.

                table_data = _parse_table_row(

                    stripped

                )

                if table_data:

                    table = Table(

                        [table_data],

                        repeatRows=0,

                    )

                    table.setStyle(

                        TableStyle(

                            [

                                (

                                    "GRID",

                                    (0, 0),

                                    (-1, -1),

                                    0.5,

                                    colors.grey,

                                ),

                                (

                                    "VALIGN",

                                    (0, 0),

                                    (-1, -1),

                                    "TOP",

                                ),

                                (

                                    "FONTNAME",

                                    (0, 0),

                                    (-1, -1),

                                    "Helvetica",

                                ),

                                (

                                    "FONTSIZE",

                                    (0, 0),

                                    (-1, -1),

                                    8,

                                ),

                                (

                                    "LEFTPADDING",

                                    (0, 0),

                                    (-1, -1),

                                    6,

                                ),

                                (

                                    "RIGHTPADDING",

                                    (0, 0),

                                    (-1, -1),

                                    6,

                                ),

                                (

                                    "TOPPADDING",

                                    (0, 0),

                                    (-1, -1),

                                    5,

                                ),

                                (

                                    "BOTTOMPADDING",

                                    (0, 0),

                                    (-1, -1),

                                    5,

                                ),

                            ]

                        )

                    )

                    story.append(table)

                    story.append(

                        Spacer(1, 8)

                    )

                    continue

            # ------------------------------------------------

            # Normal paragraph

            # ------------------------------------------------

            text = _format_inline_markdown(

                stripped

            )

            story.append(

                Paragraph(

                    text,

                    body_style,

                )

            )

        # ----------------------------------------------------

        # Generate PDF

        # ----------------------------------------------------

        document.build(

            story

        )

        pdf_bytes = pdf_buffer.getvalue()

        pdf_buffer.close()

        if not pdf_bytes:

            raise AppError(

                message="PDF generation returned an empty result.",

                status_code=500,

                error_code="REPORT_GENERATION_ERROR",

            )

        return pdf_bytes

    except AppError:

        raise

    except Exception as exc:

        raise AppError(

            message="Failed to generate PDF report.",

            status_code=500,

            error_code="REPORT_GENERATION_ERROR",

        ) from exc

# ============================================================

# HELPER FUNCTIONS

# ============================================================

def _escape_pdf_text(text: str) -> str:

    """

    Escape special characters for ReportLab Paragraph.

    """

    if not text:

        return ""

    text = str(text)

    text = (

        text.replace("&", "&amp;")

        .replace("<", "&lt;")

        .replace(">", "&gt;")

    )

    return text

def _format_inline_markdown(text: str) -> str:

    """

    Convert basic Markdown formatting into

    ReportLab-compatible inline formatting.

    """

    text = _escape_pdf_text(text)

    # Bold

    while "**" in text:

        parts = text.split("**", 2)

        if len(parts) < 3:

            break

        text = (

            parts[0]

            + "<b>"

            + parts[1]

            + "</b>"

            + parts[2]

        )

    # Inline code

    while "`" in text:

        parts = text.split("`", 2)

        if len(parts) < 3:

            break

        text = (

            parts[0]

            + "<font name='Courier'>"

            + parts[1]

            + "</font>"

            + parts[2]

        )

    return text

def _is_numbered_list(text: str) -> bool:

    """

    Check whether a line is a numbered Markdown list.

    Examples:

        1. First item

        2. Second item

    """

    if len(text) < 3:

        return False

    index = 0

    while index < len(text) and text[index].isdigit():

        index += 1

    return (

        index > 0

        and index < len(text)

        and text[index] == "."

        and index + 1 < len(text)

        and text[index + 1] == " "

    )

def _remove_number_prefix(text: str) -> str:

    """

    Remove the number from a numbered Markdown list.

    """

    index = 0

    while index < len(text) and text[index].isdigit():

        index += 1

    if (

        index < len(text)

        and text[index] == "."

    ):

        return text[index + 1:].strip()

    return text

def _parse_table_row(text: str) -> list[str]:

    """

    Parse one Markdown table row.

    Example:

        | Name | Technology | Purpose |

    Returns:

        ["Name", "Technology", "Purpose"]

    """

    if "|" not in text:

        return []

    parts = text.split("|")

    # Remove empty first/last elements

    if parts and not parts[0].strip():

        parts = parts[1:]

    if parts and not parts[-1].strip():

        parts = parts[:-1]

    cleaned = []

    for part in parts:

        value = part.strip()

        # Skip Markdown separator rows

        if value and all(

            character in "-: "

            for character in value

        ):

            return []

        cleaned.append(

            _escape_pdf_text(value)

        )

    return cleaned