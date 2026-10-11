"""Question → grounded answer with citations and a retrieval trace."""
from __future__ import annotations

import re

from .. import knowledge
from ..lang import LANG_NAMES
from ..retrieval import trace_retrieve
from . import llm, prompts

NOT_FOUND = ("I couldn't find this in the available laws. For advice on your situation, consult a lawyer "
             "or get free legal aid from NALSA / your District Legal Services Authority (helpline **15100**).")

_CITE = re.compile(r"\[([^\[\],]+),\s*(Section|Article)\s+([^\]]+)\]")


def _ctx_label(c: dict) -> str:
    return f"[{c['act']}, {'Article' if c.get('unit') == 'Article' else 'Section'} {c['section']}]"


def related_cases(c: dict) -> list[dict]:
    out = []
    old = [r for r in knowledge.conversions() if r["new"] == c["act"] and r["new_sec"].split("(")[0] == c["section"].split("(")[0]]
    old_refs = {f"Section {s}" for r in old for s in re.split(r"[/,]", r["old_sec"])}
    for case in knowledge.cases():
        blob = case["held"] + " " + case["why"] + " " + case["facts"]
        if c["act"] == "Constitution" and c["section"] in case["articles"]:
            out.append(case)
        elif f"{c['act']} Section {c['section'].split('(')[0]}" in blob or f"{c['act']} Sections" in blob and c["section"] in blob:
            out.append(case)
        elif any(r in blob for r in old_refs):
            out.append(case)
    return out[:3]


def old_equivalent(c: dict) -> str | None:
    for r in knowledge.conversions():
        if r["new"] == c["act"] and r["new_sec"] != "—" and r["new_sec"].split("(")[0] == c["section"].split("(")[0]:
            return f"{r['old']} {r['old_sec']}"
    return None


def _pick(results: list[dict]) -> list[dict]:
    if not results:
        return []
    top = results[0]["score"]
    keep = [r for r in results if r["score"] >= 0.8 * top or r["referenced"]]
    return keep[:3]


def _first_sentences(text: str, n: int = 2) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(parts[:n])


def offline_answer(results: list[dict], trace: dict, exam: bool) -> str:
    if not trace["confident"]:
        return NOT_FOUND
    picks = _pick(results)
    lines = ["### Plain-language answer"]
    for n in trace["conversions"]:
        lines.append(f"> {n}")
    for r in picks:
        lines.append(f"- {r['plain']} **[{r['act']}, {'Article' if r['unit'] == 'Article' else 'Section'} {r['section']}]**")
    if exam:
        lines.append("\n### Exam-ready notes")
        for r in picks:
            lines.append(f"\n**{r['citation']} — {r['title']}**\n")
            lines.append(f"- *Provision:* {_first_sentences(r['text'], 3)}")
            oe = old_equivalent(r)
            if oe:
                lines.append(f"- *Old law equivalent:* {oe}")
            cs = related_cases(r)
            if cs:
                lines.append("- *Cases to cite:* " + "; ".join(f"{c['name']} ({c['year']})" for c in cs))
    lines.append("\n### Relevant sections")
    for r in picks:
        lines.append(f"- **{r['citation']}** — {r['title']}")
    return "\n".join(lines)


def verify_citations(answer: str, context: list[dict]) -> list[str]:
    """Return citations in the answer that are NOT among the retrieved context sections."""
    allowed = {(c["act"].lower(), c["section"].lower().replace(" ", "")) for c in context}
    bad = []
    for act, _, sec in _CITE.findall(answer):
        key = (act.strip().lower(), sec.strip().lower().replace(" ", ""))
        if key not in allowed and not any(key[0] == a and key[1].split("(")[0] == s.split("(")[0] for a, s in allowed):
            bad.append(f"{act.strip()}, {sec.strip()}")
    return bad


def ask(question: str, act_filter: str | None = None, exam: bool = False, answer_lang: str | None = None) -> dict:
    results, trace = trace_retrieve(question, k=5, act_filter=act_filter)
    lang_code = answer_lang or trace["lang"]
    language = LANG_NAMES.get(lang_code, "English")
    trace["cited"] = [r["citation"] for r in _pick(results)] if trace["confident"] else []
    out = {"results": results, "trace": trace, "mode": llm.provider_label(), "unverified": [], "error": None}

    if llm.available() and trace["confident"]:
        context = "\n\n".join(f"{_ctx_label(c)} {c['act_name']} ({c['year']}) — {c['title']}\n{c['text']}" for c in results)
        conv = ("CONVERSIONS\n" + "\n".join(trace["conversions"]) + "\n\n") if trace["conversions"] else ""
        prompt = prompts.ANSWER.format(context=context, conversions=conv, question=question,
                                       style=prompts.STYLE_EXAM if exam else prompts.STYLE_PLAIN)
        try:
            text = llm.generate(prompts.SYSTEM.format(language=language), prompt)
            out["answer"] = text
            out["unverified"] = verify_citations(text, results)
            return out
        except llm.LLMError as e:
            out["error"] = str(e)
            out["mode"] = "Offline (model unavailable)"
    out["answer"] = offline_answer(results, trace, exam)
    if lang_code != "en" and not llm.available():
        out["note"] = f"Answers in {language} need a language model. Add a GEMINI_API_KEY to get replies in {language}."
    return out
