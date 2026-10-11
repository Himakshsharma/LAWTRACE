"""Loads the bundled knowledge base (and any PDFs you ingested yourself)."""
from __future__ import annotations

import json
from functools import lru_cache

from .config import DATA_DIR, PROCESSED_DIR


def _load(name: str):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def acts() -> dict[str, dict]:
    return {a["short"]: a for a in _load("acts.json")}


@lru_cache(maxsize=1)
def chunks() -> list[dict]:
    """Every retrievable unit. Bundled sections + optional ingested chunks.jsonl."""
    out = []
    for i, s in enumerate(_load("sections.json")):
        a = acts()[s["act"]]
        out.append({
            "id": f"{s['act']}-{s['sec']}",
            "act": s["act"],
            "act_name": a["name"],
            "year": a["year"],
            "unit": a["unit"],
            "section": s["sec"],
            "title": s["title"],
            "text": s["text"],
            "plain": s["plain"],
            "keywords": s.get("kw", ""),
            "source_url": a["url"],
            "origin": "curated",
        })
    extra = PROCESSED_DIR / "chunks.jsonl"
    if extra.exists():
        seen = {c["id"] for c in out}
        for line in extra.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            c = json.loads(line)
            if c["id"] in seen:
                continue
            c.setdefault("plain", "")
            c.setdefault("keywords", "")
            c.setdefault("act", c.get("act_name", "Act"))
            c.setdefault("unit", "Section")
            c["origin"] = "ingested"
            out.append(c)
    return out


@lru_cache(maxsize=1)
def by_id() -> dict[str, dict]:
    return {c["id"]: c for c in chunks()}


@lru_cache(maxsize=1)
def conversions() -> list[dict]:
    return _load("conversions.json")


@lru_cache(maxsize=1)
def cases() -> list[dict]:
    return sorted(_load("cases.json"), key=lambda c: c["year"])


@lru_cache(maxsize=1)
def maxims() -> list[dict]:
    return _load("maxims.json")


@lru_cache(maxsize=1)
def glossary() -> dict[str, list[str]]:
    return _load("glossary.json")


def cite(c: dict) -> str:
    """Human citation like 'BNSS s.173' or 'Constitution Art. 21'."""
    unit = "Art." if c.get("unit") == "Article" else "s."
    return f"{c['act']} {unit} {c['section']}"
