"""Turn dense legal text into plain language.

Offline it does three honest, mechanical things: swaps known jargon for plain words,
splits long sentences at provisos and conditions, and lists every term it explained.
With a model configured, it also writes a full plain rewrite.
"""
from __future__ import annotations

import html
import re

from .. import knowledge
from ..generation import llm, prompts

_SPLITTERS = [
    (r";\s*provided (?:further )?that\s*", ". But "),
    (r",?\s*provided (?:further )?that\s*", ". But "),
    (r";\s*and\s+", ". Also, "),
    (r";\s*or\s+", ". Or, "),
    (r";\s*", ". "),
]


def _terms_in(text: str) -> list[tuple[str, str, str]]:
    g = knowledge.glossary()
    found, low = [], text.lower()
    for term in sorted(g, key=len, reverse=True):
        if re.search(rf"\b{re.escape(term)}\b", low) and not any(term in f[0] for f in found):
            found.append((term, g[term][0], g[term][1]))
    return found


def highlight(text: str) -> str:
    """HTML with each jargon term wrapped in a hover-able <abbr>."""
    terms = _terms_in(text)
    out = html.escape(text)
    for term, _, meaning in terms:
        out = re.sub(rf"\b({re.escape(html.escape(term))})\b",
                     lambda m: f'<abbr class="lt-jargon" title="{html.escape(meaning)}">{m.group(1)}</abbr>',
                     out, flags=re.I)
    return out


def plain_rewrite(text: str) -> str:
    out = text
    for pat, rep in _SPLITTERS:
        out = re.sub(pat, rep, out, flags=re.I)
    for term, plain, _ in _terms_in(text):
        if term in ("shall", "may", "deemed"):
            continue
        out = re.sub(rf"\b{re.escape(term)}\b", plain, out, flags=re.I)
    out = re.sub(r"\bshall not\b", "must not", out, flags=re.I)
    out = re.sub(r"\bshall\b", "must", out, flags=re.I)
    out = re.sub(r"\bshall be deemed\b|\bdeemed\b", "treated as", out, flags=re.I)
    out = re.sub(r"\s+\.", ".", re.sub(r"\.\s*\.", ".", out))
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", out) if len(s.strip()) > 2]
    return "\n".join(f"- {s[0].upper() + s[1:]}" for s in sentences)


_DEADLINE = re.compile(r"\b(?:within|not later than|before|after|exceeding|up to|upto)\s+[^.,;]{0,40}?\b(?:days?|months?|years?|hours?)\b", re.I)
_MONEY = re.compile(r"(?:₹|rs\.?|inr|rupees)\s?[\d,]+(?:\.\d+)?(?:\s?(?:lakh|crore))?|\b[\d,]+\s?(?:lakh|crore)?\s?rupees\b", re.I)


def simplify(text: str, language: str = "English", use_model: bool = True) -> dict:
    terms = _terms_in(text)
    result = {
        "highlighted": highlight(text),
        "terms": terms,
        "plain": plain_rewrite(text),
        "deadlines": sorted(set(m.group(0).strip() for m in _DEADLINE.finditer(text))),
        "amounts": sorted(set(m.group(0).strip() for m in _MONEY.finditer(text))),
        "model_rewrite": None, "error": None,
        "words_before": len(text.split()),
    }
    if use_model and llm.available():
        try:
            result["model_rewrite"] = llm.generate("You simplify Indian legal text faithfully.",
                                                   prompts.SIMPLIFY.format(text=text[:6000], language=language))
        except llm.LLMError as e:
            result["error"] = str(e)
    return result
