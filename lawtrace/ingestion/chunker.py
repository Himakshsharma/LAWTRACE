"""Section-aware chunking of bare acts.

    python -m lawtrace.ingestion.chunker --input data/raw --output data/processed/chunks.jsonl

Name each PDF like  "Bharatiya Nyaya Sanhita__2023.pdf"  (act name, two underscores, year),
or pass --act / --year for a single file. The app picks up chunks.jsonl automatically.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path

from .parser import pdf_pages

log = logging.getLogger("chunker")

SECTION = re.compile(r"^(?:Section\s+)?(\d{1,3}[A-Z]{0,2})\.\s+([A-Z][^\n]{2,160}?)(?:\.\s*[—–-]+|[—–]|\.\s*$|\.\s+\(1\))", re.M)
CHAPTER = re.compile(r"^CHAPTER\s+([IVXLC]+)\b[^\n]*$", re.M)
SUBCLAUSE = re.compile(r"(?=\(\d+\)\s)")
MAX_TOKENS = 800


def _tokens(s: str) -> int:
    return len(s.split())


def chunk_text(pages: list[str], act_name: str, year: int | str, source_url: str = "", short: str | None = None) -> list[dict]:
    joined, page_of = "", []
    for n, p in enumerate(pages, 1):
        page_of.append((len(joined), n))
        joined += p + "\n"

    def page_at(pos: int) -> int:
        pg = 1
        for start, n in page_of:
            if start <= pos:
                pg = n
        return pg

    chapters = [(m.start(), m.group(1)) for m in CHAPTER.finditer(joined)]
    heads = list(SECTION.finditer(joined))
    short = short or "".join(w[0] for w in act_name.split() if w[0].isupper()) or act_name
    out = []
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(joined)
        body = re.sub(r"\s+", " ", joined[m.start():end]).strip()
        sec, title = m.group(1), m.group(2).strip().rstrip(".")
        chapter = next((c for pos, c in reversed(chapters) if pos <= m.start()), None)
        parts = [body]
        if _tokens(body) > MAX_TOKENS:
            parts, cur = [], ""
            for piece in SUBCLAUSE.split(body):
                if cur and _tokens(cur) + _tokens(piece) > MAX_TOKENS:
                    parts.append(cur)
                    cur = ""
                cur += piece
            parts.append(cur)
        for j, part in enumerate(parts):
            out.append({
                "id": f"{short}-{sec}" + (f"-p{j + 1}" if len(parts) > 1 else ""),
                "act": short, "act_name": act_name, "year": int(year) if str(year).isdigit() else year,
                "section": sec, "title": title, "chapter": chapter, "text": part,
                "source_url": source_url, "page_no": page_at(m.start()), "unit": "Section",
            })
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default="data/raw")
    ap.add_argument("--output", default="data/processed/chunks.jsonl")
    ap.add_argument("--act")
    ap.add_argument("--year")
    ap.add_argument("--short")
    ap.add_argument("--url", default="")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    src = Path(a.input)
    files = [src] if src.is_file() else sorted(src.glob("*.pdf"))
    allc = []
    for f in files:
        name, _, year = f.stem.partition("__")
        pages = pdf_pages(str(f))
        if not pages:
            log.warning("Skipped %s (unreadable)", f.name)
            continue
        cs = chunk_text(pages, a.act or name, a.year or year or "", a.url, a.short)
        log.info("%s → %d chunks", f.name, len(cs))
        allc += cs
    out = Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in allc), encoding="utf-8")
    log.info("Wrote %d chunks to %s", len(allc), out)


if __name__ == "__main__":
    main()
