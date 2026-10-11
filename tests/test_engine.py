import json
from pathlib import Path

import pytest

from lawtrace import knowledge
from lawtrace.generation import NOT_FOUND, ask
from lawtrace.generation.answer import verify_citations
from lawtrace.ingestion.chunker import chunk_text
from lawtrace.retrieval import references, retrieve, trace_retrieve
from lawtrace.tools import scanner, simplifier, study

SAMPLE_QUERIES = [
    ("What is the punishment for murder?", "BNS-103"),
    ("How do I file an FIR online?", "BNSS-173"),
    ("How many days does the PIO have to reply to RTI?", "RTI-7"),
    ("Are WhatsApp chats admissible as evidence?", "BSA-63"),
    ("Is a non-compete clause valid?", "ICA-27"),
]


@pytest.mark.parametrize("q,expected", SAMPLE_QUERIES)
def test_retrieve_top5(q, expected):
    ids = [r["id"] for r in retrieve(q, k=5)]
    assert expected in ids


def test_result_shape_and_metadata():
    r = retrieve("anticipatory bail", k=3)[0]
    for key in ("act", "act_name", "year", "section", "title", "source_url", "citation", "score"):
        assert key in r
    assert r["id"] == "BNSS-482"


def test_act_filter():
    res = retrieve("appeal", k=5, act_filter="RTI")
    assert res and all(r["act"] == "RTI" for r in res)


def test_old_law_reference_conversion():
    ids, notes = references("what is IPC 498A now")
    assert ids == ["BNS-85"]
    assert "BNS 85" in notes[0]
    ids, _ = references("section 438 of crpc")
    assert ids == ["BNSS-482"]
    ids, notes = references("IPC 377")
    assert ids == [] and "no equivalent" in notes[0]


def test_article_reference():
    assert references("Article 21A")[0] == ["Constitution-21A"]


def test_hindi_query():
    res, trace = trace_retrieve("अग्रिम जमानत कैसे मिलती है?")
    assert trace["lang"] == "hi"
    assert res[0]["id"] == "BNSS-482"


def test_off_topic_refuses():
    out = ask("What is the best pizza place in Delhi?")
    assert out["answer"] == NOT_FOUND
    assert out["trace"]["confident"] is False


def test_offline_answer_cites_sections():
    out = ask("IPC 302 punishment", exam=True)
    assert "[BNS, Section 103]" in out["answer"]
    assert "IPC 302" in out["answer"]


def test_citation_verifier_catches_invented_sections():
    ctx = retrieve("murder punishment", k=3)
    assert verify_citations("Murder is punished [BNS, Section 103].", ctx) == []
    assert verify_citations("See [BNS, Section 999].", ctx) == ["BNS, 999"]


def test_every_conversion_target_exists():
    for r in knowledge.conversions():
        if r["new_sec"] == "—":
            continue
        base = r["new_sec"].split("–")[0].split("(")[0]
        assert any(c["act"] == r["new"] and c["section"].split("(")[0] == base for c in knowledge.chunks()), r


def test_data_files_well_formed():
    ids = [c["id"] for c in knowledge.chunks()]
    assert len(ids) == len(set(ids))
    assert all(c["plain"] and c["text"] for c in knowledge.chunks() if c["origin"] == "curated")
    assert len(knowledge.cases()) >= 20 and len(knowledge.maxims()) >= 25


def test_scanner_flags_unfair_sample():
    r = scanner.scan(scanner.SAMPLE)
    rules = {f.rule for f in r["flags"]}
    assert "Whole deposit can be forfeited" in rules
    assert "Owner can enter without notice" in rules
    assert r["deposit_months"] == 6.0
    assert r["score"] < 50


def test_scanner_balanced_agreement_scores_high():
    text = ("The tenancy is for 11 months. The monthly rent is Rs. 15,000. The security deposit is Rs. 30,000, "
            "refundable on vacating after deducting unpaid dues. The owner may enter after 24 hours' written notice. "
            "Either party may terminate with one month's written notice.")
    r = scanner.scan(text)
    assert r["score"] >= 80, [f.rule for f in r["flags"]]


def test_simplifier_offline():
    r = simplifier.simplify("Notwithstanding anything herein, the lessee shall forthwith pay rent within 30 days; "
                            "provided that no penalty exceeding Rs. 5,000 is levied.", use_model=False)
    terms = {t[0] for t in r["terms"]}
    assert {"notwithstanding", "lessee", "forthwith"} <= terms
    assert "must" in r["plain"] and "But" in r["plain"]
    assert r["deadlines"] and r["amounts"]
    assert "lt-jargon" in r["highlighted"]


def test_converter_both_directions():
    assert study.convert("302")[0]["new_sec"] == "103"
    assert study.convert("bnss 482")[0]["old_sec"] == "438"


def test_quiz_is_well_formed_and_seeded():
    a = study.quiz(8, seed=7)
    b = study.quiz(8, seed=7)
    assert a == b and len(a) == 8
    for q in a:
        assert q["answer"] in q["options"] and len(set(q["options"])) == 4


def test_chunker_splits_by_section():
    page = ("CHAPTER I\nPRELIMINARY\n1. Short title and commencement.—(1) This Act may be called the Test Act.\n"
            "2. Definitions.—In this Act, unless the context otherwise requires, words have meanings.\n"
            "CHAPTER II\n3. Punishment for testing.—Whoever tests shall be punished with fine.\n")
    cs = chunk_text([page], "Test Act", 2024, short="TA")
    assert [c["section"] for c in cs] == ["1", "2", "3"]
    assert cs[2]["chapter"] == "II" and cs[0]["title"].startswith("Short title")
    assert cs[0]["id"] == "TA-1" and cs[0]["page_no"] == 1


def test_eval_results_meet_bar():
    from evaluation.run_eval import evaluate

    m = evaluate()
    assert m["hit@5"] >= 0.9 and m["mrr"] >= 0.8 and m["refusal_accuracy"] == 1.0
