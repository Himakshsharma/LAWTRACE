"""Extract clean text from bare-act PDFs (India Code). PyMuPDF if installed, else pypdf."""
from __future__ import annotations

import logging
import re
from collections import Counter

log = logging.getLogger(__name__)


def _pages(src) -> list[str]:
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=src.read(), filetype="pdf") if hasattr(src, "read") else fitz.open(src)
        return [p.get_text("text") for p in doc]
    except ImportError:
        from pypdf import PdfReader

        return [p.extract_text() or "" for p in PdfReader(src).pages]


def clean_pages(pages: list[str]) -> list[str]:
    """Drop page numbers and lines repeated at the top/bottom of most pages (running headers/footers)."""
    edge = Counter()
    for p in pages:
        lines = [l.strip() for l in p.splitlines() if l.strip()]
        for l in lines[:2] + lines[-2:]:
            edge[re.sub(r"\d+", "#", l)] += 1
    repeated = {l for l, n in edge.items() if len(pages) > 3 and n >= 0.6 * len(pages)}
    out = []
    for p in pages:
        keep = []
        for l in p.splitlines():
            s = l.strip()
            if not s or re.fullmatch(r"(page\s*)?\d+(\s*of\s*\d+)?", s, re.I) or re.sub(r"\d+", "#", s) in repeated:
                continue
            keep.append(s)
        out.append("\n".join(keep))
    return out


def pdf_pages(src) -> list[str]:
    try:
        return clean_pages(_pages(src))
    except Exception as e:  # corrupt / encrypted PDF
        log.error("Could not read PDF %s: %s", getattr(src, "name", src), e)
        return []


def pdf_text(src) -> str:
    return "\n".join(pdf_pages(src))
