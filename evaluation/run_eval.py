"""Retrieval evaluation.   python -m evaluation.run_eval   (from the repo root)

Reports Hit@1, Hit@5, MRR on answerable questions, and refusal accuracy on off-topic ones.
Writes evaluation/results.json (shown on the About page) and evaluation/results.md.
Optional: --ragas runs RAGAS faithfulness / answer relevancy when ragas and an LLM key are configured.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from lawtrace.retrieval import trace_retrieve  # noqa: E402


def evaluate(k: int = 5) -> dict:
    items = json.loads((HERE / "eval_set.json").read_text(encoding="utf-8"))
    ans = [i for i in items if i["expected"]]
    off = [i for i in items if not i["expected"]]
    hit1 = hit5 = rr = 0.0
    misses = []
    for it in ans:
        res, _ = trace_retrieve(it["q"], k=k)
        ids = [r["id"] for r in res]
        ranks = [ids.index(e) + 1 for e in it["expected"] if e in ids]
        best = min(ranks) if ranks else None
        hit1 += best == 1
        hit5 += best is not None
        rr += 1 / best if best else 0
        if best != 1:
            misses.append({"q": it["q"], "expected": it["expected"], "got": ids[:3]})
    refused = sum(not trace_retrieve(i["q"], k=k)[1]["confident"] for i in off)
    return {
        "n": len(items), "answerable": len(ans), "off_topic": len(off),
        "hit@1": hit1 / len(ans), "hit@5": hit5 / len(ans), "mrr": rr / len(ans),
        "refusal_accuracy": refused / len(off) if off else 1.0, "misses": misses,
    }


def markdown(m: dict) -> str:
    return ("| Metric | Value |\n|---|---|\n"
            f"| Questions (answerable / off-topic) | {m['answerable']} / {m['off_topic']} |\n"
            f"| Hit@1 | {m['hit@1']:.1%} |\n| Hit@5 | {m['hit@5']:.1%} |\n| MRR | {m['mrr']:.3f} |\n"
            f"| Correct refusals (off-topic) | {m['refusal_accuracy']:.1%} |\n")


def ragas_eval():  # pragma: no cover - needs network + keys
    from datasets import Dataset
    from ragas import evaluate as r_eval
    from ragas.metrics import answer_relevancy, faithfulness

    from lawtrace.generation import ask

    items = [i for i in json.loads((HERE / "eval_set.json").read_text(encoding="utf-8")) if i["expected"]][:20]
    rows = {"question": [], "answer": [], "contexts": []}
    for it in items:
        out = ask(it["q"])
        rows["question"].append(it["q"])
        rows["answer"].append(out["answer"])
        rows["contexts"].append([r["text"] for r in out["results"]])
    print(r_eval(Dataset.from_dict(rows), metrics=[faithfulness, answer_relevancy]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ragas", action="store_true")
    a = ap.parse_args()
    m = evaluate()
    (HERE / "results.json").write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")
    (HERE / "results.md").write_text(markdown(m), encoding="utf-8")
    print(markdown(m))
    for x in m["misses"]:
        print("not first:", x)
    if a.ragas:
        ragas_eval()
