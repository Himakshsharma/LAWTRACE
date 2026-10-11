"""Tokenisation and a dependency-free Okapi BM25 index."""
from __future__ import annotations

import math
import re
from collections import Counter

STOP = set("""a an the of to in on for and or is are was were be been being by with as at from that this
these those it its into than then there their they them he she his her you your i me my we our us what which who
whom whose when where why how can could should would will shall may might do does did done not no if any all
about under over up down out more most such only own same so too very just get got have has had
please tell explain law laws legal india indian act section article
ka ki ke ko se me mein hai hain ho hota hoti kya kaise kab kahan aur ya bhi par pe nahi na mera meri mere hum ham
tum aap apna apni karna kare karein karu kar raha rahi tha thi aata aati jata jaati sakta sakti chahiye liye wala wali""".split())

_TOKEN = re.compile(r"[a-z0-9]+(?:[a-z0-9]*)")


def stem(w: str) -> str:
    for suf in ("ations", "ation", "ings", "ing", "ments", "ment", "ies", "es", "ed", "s"):
        if len(w) > len(suf) + 3 and w.endswith(suf):
            return w[: -len(suf)] + ("y" if suf == "ies" else "")
    return w


def tokenize(text: str) -> list[str]:
    return [stem(t) for t in _TOKEN.findall(text.lower()) if t not in STOP and len(t) > 1]


class BM25:
    def __init__(self, docs: list[list[str]], k1: float = 1.4, b: float = 0.72):
        self.k1, self.b = k1, b
        self.docs = docs
        self.n = len(docs)
        self.avgdl = sum(map(len, docs)) / max(self.n, 1)
        self.tf = [Counter(d) for d in docs]
        df = Counter(t for d in docs for t in set(d))
        self.idf = {t: math.log(1 + (self.n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: list[str]) -> list[float]:
        out = []
        for tf, d in zip(self.tf, self.docs):
            s, dl = 0.0, len(d)
            for q in query:
                f = tf.get(q)
                if f:
                    s += self.idf[q] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            out.append(s)
        return out
