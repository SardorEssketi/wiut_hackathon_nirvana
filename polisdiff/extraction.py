"""Bounded PDF parsing. JavaScript, attachments and links are never executed."""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from .models import Document, Page, Passage
from .text import normalize, detect_languages, extract_dates

MAX_BYTES = 10 * 1024 * 1024
MAX_PAGES = 80
MAX_CHARS = 500_000
MAX_PASSAGES = 1000


class PDFError(ValueError):
    pass


def validate_pdf(data: bytes):
    if not data or len(data) > MAX_BYTES:
        raise PDFError("PDF must contain between 1 byte and 10 MiB.")
    if not data.startswith(b"%PDF-"):
        raise PDFError("Invalid PDF header; changing a file extension is insufficient.")


def _extract(data: bytes) -> Document:
    import pymupdf
    validate_pdf(data)
    pymupdf.TOOLS.mupdf_display_errors(False)
    pymupdf.TOOLS.mupdf_display_warnings(False)
    try:
        pdf = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise PDFError("PDF could not be parsed.") from exc
    with pdf:
        if pdf.needs_pass:
            raise PDFError("Encrypted PDFs are unsupported.")
        if not 1 <= len(pdf) <= MAX_PAGES:
            raise PDFError("Supported PDF length is 1–80 pages.")
        pages, passages, warnings = [], [], []
        total_chars = 0
        appendix = False
        for i, page in enumerate(pdf):
            # MuPDF text extraction does not execute PDF JavaScript.
            blocks = [b for b in page.get_text("blocks", sort=True) if b[6] == 0]
            text = "".join(b[4] for b in blocks)
            norm = normalize(text)
            # Require both a rules heading and legal attribution, not a passing reference.
            is_rules = bool(re.search(r"(?:^|\s)(?:правила обязательного страхования|қоидалар|qoidalar)(?:\s|$)", norm))
            attribution = bool(re.search(r"(?:приложение|илова|ilova).{0,250}(?:141|2008)|(?:141|2008).{0,250}(?:приложение|илова|ilova)", norm))
            if is_rules and attribution:
                appendix = True
            section = "regulatory_appendix" if appendix else "offer"
            readable = len(re.sub(r"\s", "", text)) >= 30 and text.count("\ufffd") < max(3, len(text) * .02)
            if not readable:
                warnings.append(f"Page {i + 1}: insufficient or damaged text; OCR is not enabled. Manual review required.")
            total_chars += len(text)
            if total_chars > MAX_CHARS:
                raise PDFError("Extracted text exceeds the resource limit.")
            pages.append(Page(number=i + 1, text=text, chars=len(text), readable=readable, section=section))
            offset = 0
            for block in blocks:
                original = block[4]
                # Fixed bounded windows, split at whitespace, retaining original offsets.
                start = 0
                while start < len(original):
                    end = min(start + 1200, len(original))
                    if end < len(original):
                        boundary = original.rfind(" ", start + 650, end)
                        if boundary > start:
                            end = boundary + 1
                    fragment = original[start:end]
                    if len(fragment.strip()) >= 12:
                        passages.append(Passage(id=f"p{i+1}-{len(passages)}", page=i+1,
                            text=fragment, normalized=normalize(fragment), start=offset+start,
                            end=offset+end, bbox=tuple(block[:4]), languages=detect_languages(fragment), section=section))
                    start = end
                offset += len(original)
            if len(passages) > MAX_PASSAGES:
                raise PDFError("Too many passages; document exceeds resource limits.")
        languages = sorted({lang for p in passages for lang in p.languages})
        refs = [p for p in passages if p.section == "offer" and
                re.search(r"\b141\b", p.normalized) and
                re.search(r"правил|qoid|қоид|qaror|қарор|постановлен", p.normalized)]
        return Document(sha256=hashlib.sha256(data).hexdigest(), pages=pages, passages=passages,
                        languages=languages, warnings=warnings,
                        detected_dates=extract_dates(pages[0].text), governing_reference=refs)


def extract_pdf(data: bytes, *, isolated: bool = True) -> Document:
    validate_pdf(data)
    if not isolated:
        return _extract(data)
    # Parsing runs in a killable process. Raw bytes are sent on stdin, never disk/logs.
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        process = subprocess.run([sys.executable, "-m", "polisdiff.extract_worker"],
            input=data, capture_output=True, timeout=25, env=env,
            cwd=Path(__file__).resolve().parents[1])
    except subprocess.TimeoutExpired as exc:
        raise PDFError("PDF extraction exceeded 25 seconds.") from exc
    if process.returncode:
        raise PDFError("PDF rejected: malformed, encrypted, empty, or over resource limits.")
    try:
        return Document.model_validate_json(process.stdout)
    except (ValueError, json.JSONDecodeError) as exc:
        raise PDFError("Extraction worker returned an invalid result.") from exc


def render_page(data: bytes, page_number: int) -> bytes:
    """Raster evidence preview; excludes active PDF content."""
    validate_pdf(data)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        proc = subprocess.run([sys.executable, "-m", "polisdiff.extract_worker", "--render", str(page_number)],
            input=data, capture_output=True, timeout=15, env=env, cwd=Path(__file__).resolve().parents[1])
    except subprocess.TimeoutExpired as exc:
        raise PDFError("Page rendering timed out.") from exc
    if proc.returncode:
        raise PDFError("Page could not be rendered safely.")
    return proc.stdout
