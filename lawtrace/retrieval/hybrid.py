"""Hybrid retrieval: BM25 + meaning search, merged with Reciprocal Rank Fusion, then reranked.

    retrieve(query, k=5, act_filter=None) -> list[dict]
    trace_retrieve(...) -> (results, trace)   # trace powers the 'Trace' view in the UI
"""
from __future__ import annotations

import re
from functools import lru_cache

import numpy as np

from .. import knowledge, lang
from ..config import get_settings
from . import lexical, semantic

RRF_K = 60
POOL = 20

_OLD_CODES = {"ipc": "IPC", "crpc": "CrPC", "cr.p.c": "CrPC", "crp.c": "CrPC", "iea": "IEA", "evidence act": "IEA"}
_NEW_CODES = {
    "bns": "BNS", "bnss": "BNSS", "bsa": "BSA", "rti": "RTI", "cpa": "CPA",
    "consumer protection act": "CPA", "contract act": "ICA", "ica": "ICA",
    "lsa": "LSA", "legal services authorities act": "LSA", "registration act": "Registration",
    "model tenancy act": "MTA", "mta": "MTA",
    "nyaya sanhita": "BNS", "nagarik suraksha sanhita": "BNSS", "sakshya adhiniyam": "BSA",
}
_NUM = r"(\d+[a-z]?(?:\(\d+\))?)"
_CODE_ALT = "|".join(sorted({re.escape(k) for k in list(_OLD_CODES) + list(_NEW_CODES)}, key=len, reverse=True))
_REF_A = re.compile(rf"\b({_CODE_ALT})\s*(?:s\.|sec\.?|section)?\s*{_NUM}", re.I)
_REF_B = re.compile(rf"\b(?:section|sec\.?|s\.)\s*{_NUM}\s*(?:of\s+)?(?:the\s+)?({_CODE_ALT})\b", re.I)
_ART = re.compile(rf"\b(?:article|art\.?)\s*{_NUM}", re.I)


def _expand_old(old_sec: str) -> list[str]:
    out = []
    for part in re.split(r"[/,]", old_sec):
        part = part.strip()
        m = re.match(r"(\d+)\s*[–-]\s*(\d+)$", part)
        if m:
            out += [str(i) for i in range(int(m.group(1)), int(m.group(2)) + 1)]
        elif part:
            out.append(part)
    return out


def _match_ids(act: str, sec: str) -> list[str]:
    sec = sec.upper().replace(" ", "")
    hits = []
    for c in knowledge.chunks():
        if c["act"] != act:
            continue
        s = c["section"].upper()
        if s == sec or s.startswith(sec + "("):
            hits.append(c["id"])
    return hits


def references(query: str) -> tuple[list[str], list[str]]:
    """Return (chunk ids explicitly referenced, human notes about old→new conversions)."""
    ids, notes = [], []
    pairs = [(m.group(1), m.group(2)) for m in _REF_A.finditer(query)]
    pairs += [(m.group(2), m.group(1)) for m in _REF_B.finditer(query)]
    for code, sec in pairs:
        key = code.lower()
        if key in _OLD_CODES:
            old = _OLD_CODES[key]
            for row in knowledge.conversions():
                if row["old"] == old and sec.upper() in [s.upper() for s in _expand_old(row["old_sec"])]:
                    if row["new_sec"] == "—":
                        notes.append(f"{old} {sec} has no equivalent in the new law ({row['topic']}).")
                        continue
                    notes.append(f"{old} {sec} is now {row['new']} {row['new_sec']} ({row['topic']}).")
                    base = row["new_sec"].split("–")[0].split("(")[0]
                    ids += _match_ids(row["new"], row["new_sec"]) or _match_ids(row["new"], base)
        elif key in _NEW_CODES:
            ids += _match_ids(_NEW_CODES[key], sec)
    for m in _ART.finditer(query):
        ids += _match_ids("Constitution", m.group(1))
    seen, uniq = set(), []
    for i in ids:
        if i not in seen:
            seen.add(i)
            uniq.append(i)
    return uniq, notes


def _doc_text(c: dict) -> str:
    return " ".join([c["title"], c["title"], c["text"], c.get("plain", ""), c.get("keywords", ""), c.get("keywords", ""), c["act_name"]])


class Index:
    def __init__(self):
        s = get_settings()
        self.chunks = knowledge.chunks()
        texts = [_doc_text(c) for c in self.chunks]
        self.bm25 = lexical.BM25([lexical.tokenize(t) for t in texts])
        self.sem = semantic.build(texts, s.use_dense, s.dense_model)
        self.cross = None
        if s.use_cross_encoder:
            try:
                from sentence_transformers import CrossEncoder

                self.cross = CrossEncoder(s.reranker_model)
            except Exception:
                self.cross = None

    @property
    def reranker_name(self) -> str:
        return "Cross-encoder" if self.cross else "Lexical title + reference rerank"


@lru_cache(maxsize=1)
def get_index() -> Index:
    return Index()


def _rank(scores: np.ndarray, allowed: np.ndarray) -> list[int]:
    order = np.argsort(-scores)
    return [int(i) for i in order if allowed[i] and scores[i] > 0][:POOL]


def trace_retrieve(query: str, k: int = 5, act_filter: str | None = None):
    idx = get_index()
    user_lang = lang.detect(query)
    expanded = lang.bridge(query)
    ref_ids, notes = references(expanded)
    # bring the converted section's vocabulary into the query too
    boost_text = " ".join(knowledge.by_id()[i]["title"] for i in ref_ids if i in knowledge.by_id())
    q_text = f"{expanded} {boost_text}".strip()

    allowed = np.array([act_filter in (None, "", "All") or c["act"] == act_filter for c in idx.chunks])
    bm = np.array(idx.bm25.scores(lexical.tokenize(q_text)))
    se = idx.sem.scores(q_text)
    bm_rank, se_rank = _rank(bm, allowed), _rank(se, allowed)

    fused: dict[int, float] = {}
    for r, i in enumerate(bm_rank):
        fused[i] = fused.get(i, 0) + 1 / (RRF_K + r + 1)
    for r, i in enumerate(se_rank):
        fused[i] = fused.get(i, 0) + 1 / (RRF_K + r + 1)
    id_pos = {c["id"]: n for n, c in enumerate(idx.chunks)}
    for rid in ref_ids:
        if rid in id_pos and allowed[id_pos[rid]]:
            fused[id_pos[rid]] = fused.get(id_pos[rid], 0) + 1.0  # explicit citation wins

    cand = sorted(fused, key=fused.get, reverse=True)[:POOL]
    q_tokens = set(lexical.tokenize(q_text))
    rescored = []
    for i in cand:
        c = idx.chunks[i]
        if idx.cross is not None:
            extra = float(idx.cross.predict([(q_text, c["title"] + ". " + c["text"])])[0]) * 0.02
        else:
            t = set(lexical.tokenize(c["title"] + " " + c.get("keywords", "")))
            title = set(lexical.tokenize(c["title"]))
            coverage = len(q_tokens & title) / len(title) if title else 0
            extra = 0.012 * (len(q_tokens & t) / (len(t) ** 0.5 + 1)) + 0.01 * coverage
        rescored.append((fused[i] + extra, i))
    rescored.sort(reverse=True)

    top_bm = float(bm[bm_rank[0]]) if bm_rank else 0.0
    top_se = float(se[se_rank[0]]) if se_rank else 0.0
    q_terms = lexical.tokenize(q_text)
    coverage = sum(t in idx.bm25.idf for t in q_terms) / len(q_terms) if q_terms else 0.0
    confident = bool(ref_ids) or (coverage >= 0.5 and (top_bm >= 4.0 or top_se >= 0.16))

    bm_pos = {i: r + 1 for r, i in enumerate(bm_rank)}
    se_pos = {i: r + 1 for r, i in enumerate(se_rank)}
    results = []
    for score, i in rescored[:k]:
        c = dict(idx.chunks[i])
        c.update(score=round(score, 4), bm25_rank=bm_pos.get(i), semantic_rank=se_pos.get(i),
                 referenced=c["id"] in ref_ids, citation=knowledge.cite(c))
        results.append(c)

    def lane(ranked, scores):
        return [{"id": idx.chunks[i]["id"], "cite": knowledge.cite(idx.chunks[i]), "score": round(float(scores[i]), 3)} for i in ranked[:5]]

    trace = {
        "query": query, "lang": user_lang, "expanded": q_text if q_text != query else "",
        "conversions": notes, "references": [knowledge.cite(knowledge.by_id()[i]) for i in ref_ids],
        "bm25": lane(bm_rank, bm), "semantic": lane(se_rank, se),
        "semantic_name": idx.sem.name, "reranker": idx.reranker_name,
        "final": [{"id": r["id"], "cite": r["citation"], "score": r["score"]} for r in results],
        "confident": confident, "coverage": round(coverage, 2), "act_filter": act_filter or "All",
    }
    return results, trace


def retrieve(query: str, k: int = 5, act_filter: str | None = None) -> list[dict]:
    return trace_retrieve(query, k, act_filter)[0]
