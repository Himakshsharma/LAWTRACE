"""Study tools: old→new law converter, quiz generator, section of the day."""
from __future__ import annotations

import datetime as dt
import random
import re

from .. import knowledge


def convert(query: str) -> list[dict]:
    """Search the IPC/CrPC/IEA → BNS/BNSS/BSA table by section number or topic, in either direction."""
    q = query.strip().lower()
    if not q:
        return knowledge.conversions()
    num = re.findall(r"\d+[a-z]?", q)
    code = re.findall(r"\b(ipc|crpc|iea|bns|bnss|bsa)\b", q)
    out = []
    for r in knowledge.conversions():
        olds = [s.strip().lower() for s in re.split(r"[/,]", r["old_sec"])]
        news = [r["new_sec"].lower(), r["new_sec"].split("(")[0].lower()]
        hay = f"{r['old']} {r['old_sec']} {r['new']} {r['new_sec']} {r['topic']}".lower()
        if num:
            hit_old = any(n in olds for n in num) and (not code or r["old"].lower() in code)
            hit_new = any(n in news for n in num) and (not code or r["new"].lower() in code)
            if hit_old or hit_new:
                out.append(r)
        elif all(w in hay for w in q.split()):
            out.append(r)
    return out


def section_of_the_day(today: dt.date | None = None) -> dict:
    today = today or dt.date.today()
    chunks = [c for c in knowledge.chunks() if c["origin"] == "curated"]
    return chunks[today.toordinal() % len(chunks)]


def quiz(n: int = 6, seed: int | None = None, topics: tuple[str, ...] = ("convert", "maxim", "case", "section")) -> list[dict]:
    rng = random.Random(seed)
    qs: list[dict] = []
    conv = [r for r in knowledge.conversions() if r["new_sec"] != "—"]
    maxims, cases = knowledge.maxims(), knowledge.cases()
    secs = [c for c in knowledge.chunks() if c["origin"] == "curated"]

    def opts(right, pool):
        wrong = rng.sample([p for p in pool if p != right], 3)
        o = wrong + [right]
        rng.shuffle(o)
        return o

    makers = []
    if "convert" in topics:
        def m_conv():
            r = rng.choice(conv)
            right = f"{r['new']} {r['new_sec']}"
            pool = list({f"{x['new']} {x['new_sec']}" for x in conv if x["new"] == r["new"]})
            return {"q": f"{r['old']} {r['old_sec']} ({r['topic'].split(' (')[0].lower()}) is now…", "options": opts(right, pool),
                    "answer": right, "explain": f"{r['old']} {r['old_sec']} → {r['new']} {r['new_sec']}: {r['topic']}.", "kind": "Old → new"}
        makers.append(m_conv)
    if "maxim" in topics:
        def m_max():
            m = rng.choice(maxims)
            return {"q": f"What does “{m['term']}” mean?", "options": opts(m["meaning"], [x["meaning"] for x in maxims]),
                    "answer": m["meaning"], "explain": m["use"], "kind": "Maxim"}
        makers.append(m_max)
    if "case" in topics:
        def m_case():
            c = rng.choice(cases)
            return {"q": f"Which case held: {c['held'].split('. ')[0].rstrip('.')}?", "options": opts(c["name"], [x["name"] for x in cases]),
                    "answer": c["name"], "explain": f"{c['name']} ({c['year']}). {c['why']}", "kind": "Case law"}
        makers.append(m_case)
    if "section" in topics:
        def m_sec():
            c = rng.choice(secs)
            right = knowledge.cite(c)
            pool = [knowledge.cite(x) for x in secs if x["act"] == c["act"]] or [knowledge.cite(x) for x in secs]
            if len(set(pool)) < 4:
                pool = [knowledge.cite(x) for x in secs]
            return {"q": f"Which provision deals with “{c['title']}”?", "options": opts(right, list(set(pool))),
                    "answer": right, "explain": c["plain"], "kind": "Bare act"}
        makers.append(m_sec)

    seen = set()
    while len(qs) < n and makers:
        item = rng.choice(makers)()
        if item["q"] in seen:
            continue
        seen.add(item["q"])
        qs.append(item)
    return qs
