"""PDF rendering for the generated blueprint.

The styled HTML report produced by ai.report.html is the single source of
truth: the PDF is that exact document printed by a headless Chromium
browser, so the two can never drift apart in content or design. There is
no second, simplified PDF renderer.

Chrome or Edge is used through its `--print-to-pdf` switch, which needs no
extra Python package and no downloaded browser. The print rules that keep
tables, cards, and the architecture diagram intact live with the rest of
the report CSS in ai/report/html.py.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.core.errors import AppError

# Checked in order. CHROME_BINARY overrides everything for unusual installs.
_BROWSER_CANDIDATES = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)

_PDF_TIMEOUT_SECONDS = 120


def find_browser() -> str:
    """Path to a Chromium-family browser able to print the report."""
    override = os.getenv("CHROME_BINARY")
    if override and Path(override).exists():
        return override

    for name in ("chrome", "chromium", "google-chrome", "msedge"):
        found = shutil.which(name)
        if found:
            return found

    for candidate in _BROWSER_CANDIDATES:
        if Path(candidate).exists():
            return candidate

    raise AppError(
        message=(
            "No Chrome or Edge installation was found to render the PDF. "
            "Set the CHROME_BINARY environment variable to a Chromium-family "
            "browser executable."
        ),
        status_code=500,
        error_code="REPORT_GENERATION_ERROR",
    )


def generate_pdf(blueprint_html: str) -> bytes:
    """Print the already-styled HTML report to PDF, unchanged.

    `blueprint_html` is the self-contained report from
    ai.report.html.render_blueprint_html — it embeds its own CSS and SVG,
    so the browser never needs network access to render it.
    """
    if not blueprint_html:
        raise AppError(
            message="Blueprint HTML is empty.",
            status_code=500,
            error_code="REPORT_GENERATION_ERROR",
        )

    browser = find_browser()

    with tempfile.TemporaryDirectory(prefix="solutionforge-pdf-") as workdir:
        source = Path(workdir) / "blueprint.html"
        target = Path(workdir) / "blueprint.pdf"
        source.write_text(blueprint_html, encoding="utf-8")

        command = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--no-pdf-header-footer",
            "--print-to-pdf-no-header",
            # Let webfonts/layout settle before the snapshot is taken.
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=10000",
            f"--user-data-dir={Path(workdir) / 'profile'}",
            f"--print-to-pdf={target}",
            source.as_uri(),
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                timeout=_PDF_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise AppError(
                message="PDF rendering timed out.",
                status_code=500,
                error_code="REPORT_GENERATION_ERROR",
            ) from exc
        except OSError as exc:
            raise AppError(
                message="The PDF renderer could not be started.",
                status_code=500,
                error_code="REPORT_GENERATION_ERROR",
            ) from exc

        if not target.exists():
            detail = (result.stderr or b"").decode("utf-8", "replace").strip()[-400:]
            raise AppError(
                message=f"PDF rendering produced no output. {detail}".strip(),
                status_code=500,
                error_code="REPORT_GENERATION_ERROR",
            )

        pdf_bytes = target.read_bytes()

    if not pdf_bytes.startswith(b"%PDF"):
        raise AppError(
            message="PDF rendering returned a malformed document.",
            status_code=500,
            error_code="REPORT_GENERATION_ERROR",
        )

    return pdf_bytes
