"""LAWTRACE — one place for Indian law students.  Run:  streamlit run app.py"""
from __future__ import annotations

import json
import random
import time
from pathlib import Path

import streamlit as st

from lawtrace import knowledge
from lawtrace.config import ROOT
from lawtrace.generation import ask
from lawtrace.generation import llm
from lawtrace.retrieval.hybrid import get_index
from lawtrace.tools import scanner, simplifier, study
from lawtrace.ui import components as ui
from lawtrace.ui import theme

st.set_page_config(page_title="LAWTRACE", page_icon="⚖️", layout="wide", initial_sidebar_state="collapsed")

PAGES = ["Ask", "Simplify", "Bare acts", "Old → New", "Cases", "Maxims", "Clause check", "Practice", "About"]
RATE_LIMIT = (20, 600)  # questions per window (seconds) when a paid model is in use

ss = st.session_state
ss.setdefault("entered", st.query_params.get("enter") == "1")
ss.setdefault("messages", [])
ss.setdefault("quiz_seed", random.randint(0, 10_000))
ss.setdefault("ask_times", [])


def enter(page: str = "Ask") -> None:
    ss.entered = True
    ss.nav = page
    st.rerun()


@st.cache_resource(show_spinner="Opening the library…")
def warm_index():
    return get_index()


# ─────────────────────────────── gate ───────────────────────────────
def gate() -> None:
    st.markdown(theme.css(gate=True), unsafe_allow_html=True)
    with st.container(key="gatenav"):
        cols = st.columns([3.2, 0.8, 1, 0.9, 1, 1.35], vertical_alignment="center")
        cols[0].markdown(ui.brand(36), unsafe_allow_html=True)
        for col, (label, page) in zip(cols[1:5], [("Ask", "Ask"), ("Bare acts", "Bare acts"), ("Cases", "Cases"), ("Practice", "Practice")]):
            with col:
                if st.button(label, key=f"go_{page.replace(' ', '_')}"):
                    enter(page)
        with cols[5]:
            if st.button("Get started", key="go_start"):
                enter("Ask")
    st.markdown(ui.gate_hero(), unsafe_allow_html=True)
    if st.button("Enter the court", key="enter"):
        enter("Ask")
    st.markdown(ui.gate_foot() + ui.disclaimer(), unsafe_allow_html=True)


# ─────────────────────────────── shell ───────────────────────────────
def shell() -> str:
    st.markdown(theme.css(gate=False) + f"<style>{theme.masthead_css()}</style>", unsafe_allow_html=True)
    if "nav" not in ss or ss.nav not in PAGES:
        ss.nav = "Ask"
    top = st.columns([1.35, 6.4, 1.2], vertical_alignment="center")
    top[0].markdown(ui.brand(28), unsafe_allow_html=True)
    with top[1]:
        page = st.radio("Go to", PAGES, horizontal=True, key="nav", label_visibility="collapsed")
    with top[2]:
        if st.button("Leave court", key="leave", help="Back to the entrance"):
            ss.entered = False
            st.rerun()
    st.markdown(ui.disclaimer(), unsafe_allow_html=True)
    return page


def head(title: str, lede: str) -> None:
    st.markdown(ui.masthead(title, lede), unsafe_allow_html=True)


# ─────────────────────────────── Ask ───────────────────────────────
SUGGESTIONS = [
    "Police refused to write my FIR. What can I do?",
    "What is IPC 420 under the new law?",
    "Can my landlord keep my whole security deposit?",
    "RTI ka jawab kitne din mein aana chahiye?",
    "Is privacy a fundamental right?",
    "मुझे गिरफ्तारी का डर है, अग्रिम जमानत कैसे मिलेगी?",
]


def rate_limited() -> bool:
    if not llm.available():
        return False
    now = time.time()
    ss.ask_times = [t for t in ss.ask_times if now - t < RATE_LIMIT[1]]
    if len(ss.ask_times) >= RATE_LIMIT[0]:
        return True
    ss.ask_times.append(now)
    return False


def page_ask() -> None:
    prompt = st.chat_input("Ask about any right, offence, procedure or section — in English or हिन्दी")
    q = prompt or ss.pop("pending", None)
    left, right = st.columns([1.7, 1], gap="large")

    with right:
        st.markdown("#### Settings")
        acts = ["All"] + list(knowledge.acts().keys())
        act = st.selectbox("Search within", acts, format_func=lambda k: "All laws" if k == "All" else knowledge.acts()[k]["name"])
        exam = st.toggle("Exam-ready answer", help="Adds provisions, old-law equivalents and cases to cite")
        lang_choice = st.selectbox("Answer in", ["Same as my question", "English", "Hindi"])
        st.caption(f"Answer engine: {llm.provider_label()}")

    if q:
        if rate_limited():
            st.warning("You've asked 20 questions in 10 minutes. Wait a few minutes, then ask again.")
        else:
            lang_code = {"English": "en", "Hindi": "hi"}.get(lang_choice)
            with st.spinner("Tracing the law…"):
                try:
                    res = ask(q, act_filter=None if act == "All" else act, exam=exam, answer_lang=lang_code)
                except Exception as err:  # never crash the chat
                    res = {"answer": f"Something went wrong while answering: {err}", "results": [], "trace": None,
                           "mode": "error", "unverified": [], "error": str(err)}
            ss.messages.append({"role": "user", "content": q})
            ss.messages.append({"role": "assistant", **res})

    with left:
        head("Ask the law", "Ask in your own words. Every answer cites the sections it comes from, "
                            "and the trace on the right shows how it found them.")
        if not ss.messages:
            st.markdown("##### Try one of these")
            cols = st.columns(2)
            for i, s in enumerate(SUGGESTIONS):
                if cols[i % 2].button(s, key=f"sug{i}", use_container_width=True):
                    ss.pending = s
                    st.rerun()
        for i, m in enumerate(ss.messages):
            with st.chat_message(m["role"], avatar="🧑‍🎓" if m["role"] == "user" else "⚖️"):
                if m["role"] == "user":
                    st.markdown(m["content"])
                    continue
                st.markdown(m["answer"])
                if m.get("unverified"):
                    st.warning("These citations were not in the retrieved sections, so treat them with caution: "
                               + ", ".join(m["unverified"]))
                if m.get("note"):
                    st.info(m["note"])
                if m.get("error") and m.get("mode") != "error":
                    st.caption(f"The language model was unavailable, so this is a grounded extract. ({m['error'][:120]})")
                if m.get("results") and m.get("trace", {}).get("confident"):
                    with st.expander(f"Sources · {min(3, len(m['results']))} sections"):
                        st.markdown("".join(ui.source_card(r) for r in m["results"][:3]), unsafe_allow_html=True)
        if ss.messages and st.button("Clear conversation", key="clear"):
            ss.messages = []
            st.rerun()

    with right:
        st.markdown("#### Trace")
        last = next((m.get("trace") for m in reversed(ss.messages) if m["role"] == "assistant"), None)
        st.markdown(ui.trace_html(last), unsafe_allow_html=True)


# ─────────────────────────────── Simplify ───────────────────────────────
SIMPLIFY_SAMPLES = {
    "A bail provision": ("When a person accused of a bailable offence is arrested or detained without warrant and is prepared "
                         "to give bail, such person shall be released on bail; provided that where such person is indigent and "
                         "cannot furnish surety, the officer or Court may, in lieu thereof, discharge him on his executing a bond "
                         "without sureties for his appearance."),
    "A rent clause": ("Notwithstanding anything contained hereinbefore, the Lessee shall forthwith indemnify and hold harmless "
                      "the Lessor against all losses, and the security deposit shall be forfeited in the event the Lessee "
                      "vacates the demised premises before the expiry of the lock-in period of 11 months; provided that the "
                      "Lessee shall not be liable for any force majeure event."),
    "A contract term": ("The parties hereto agree that this Agreement shall be governed by the laws of India and the courts at "
                        "Mumbai shall have exclusive jurisdiction; inter alia, the Employee shall not, for a period of two years "
                        "after termination, engage in any business similar to that of the Company, and any breach thereof shall "
                        "entitle the Company to liquidated damages of Rs. 5,00,000."),
}


def page_simplify() -> None:
    head("Simplify a clause", "Paste dense legal text. LAWTRACE explains the jargon, splits long sentences at every "
                              "condition, and pulls out deadlines and amounts.")
    cols = st.columns(len(SIMPLIFY_SAMPLES) + 1)
    cols[0].caption("Try a sample:")
    for col, (name, text) in zip(cols[1:], SIMPLIFY_SAMPLES.items()):
        if col.button(name, key=f"ss_{name}", use_container_width=True):
            ss.simplify_text = text
    text = st.text_area("Legal text", key="simplify_text", height=150, placeholder="Paste a section, clause or paragraph…")
    use_model = st.toggle("Also write a full plain-language rewrite with AI", value=llm.available(), disabled=not llm.available(),
                          help=None if llm.available() else "Add a GEMINI_API_KEY to enable this")
    if not text.strip():
        st.markdown('<div class="lt-empty">Paste text above or pick a sample. Underlined words get a plain meaning when you hover over them.</div>', unsafe_allow_html=True)
        return
    r = simplifier.simplify(text, use_model=use_model)
    a, b = st.columns(2, gap="large")
    with a:
        st.markdown("#### Original, with jargon marked")
        st.markdown(f'<div class="lt-original">{r["highlighted"]}</div>', unsafe_allow_html=True)
    with b:
        st.markdown("#### In plain words")
        st.markdown(f'<div class="lt-plain">\n\n{r["plain"]}\n\n</div>', unsafe_allow_html=True)
        facts = []
        if r["deadlines"]:
            facts.append("**Time limits:** " + "; ".join(r["deadlines"]))
        if r["amounts"]:
            facts.append("**Amounts:** " + "; ".join(r["amounts"]))
        if facts:
            st.markdown("  \n".join(facts))
    if r["model_rewrite"]:
        st.markdown("#### AI rewrite")
        st.markdown(r["model_rewrite"])
    elif r["error"]:
        st.caption(r["error"])
    if r["terms"]:
        st.markdown(f"#### {len(r['terms'])} terms explained")
        st.markdown(ui.term_cards(r["terms"]), unsafe_allow_html=True)


# ─────────────────────────────── Bare acts ───────────────────────────────
def page_bare_acts() -> None:
    head("Bare acts library", "Browse every provision in LAWTRACE, each with a plain-language note and a link to the official text.")
    st.markdown(ui.section_of_day(study.section_of_the_day()), unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    act = c1.selectbox("Law", list(knowledge.acts().keys()), format_func=lambda k: knowledge.acts()[k]["name"])
    term = c2.text_input("Search within this law", placeholder="e.g. bail, deposit, writ, appeal")
    a = knowledge.acts()[act]
    st.caption(a["about"])
    rows = [c for c in knowledge.chunks() if c["act"] == act]
    if term.strip():
        t = term.lower()
        rows = [c for c in rows if t in (c["title"] + c["text"] + c.get("plain", "") + c.get("keywords", "")).lower()]
    if not rows:
        st.markdown('<div class="lt-empty">No provision in this law matches that word. Try a broader term, or ask the question on the Ask page.</div>', unsafe_allow_html=True)
    st.markdown("".join(ui.source_card(c) for c in rows), unsafe_allow_html=True)
    with st.expander("All laws in LAWTRACE"):
        st.markdown(ui.act_cards(), unsafe_allow_html=True)


# ─────────────────────────────── Old → New ───────────────────────────────
def page_convert() -> None:
    head("Old law to new law", "Type an IPC, CrPC or Evidence Act section, or a topic, to find its place in the BNS, BNSS or BSA. "
                               "Works backwards too.")
    picks = ["IPC 302", "IPC 420", "IPC 498A", "IPC 124A", "CrPC 154", "CrPC 438", "IEA 65B"]
    cols = st.columns(len(picks))
    for col, p in zip(cols, picks):
        if col.button(p, key=f"cv_{p}", use_container_width=True):
            ss.conv_q = p
    q = st.text_input("Section or topic", key="conv_q", placeholder="e.g. 302, 438 CrPC, BNS 318, anticipatory bail")
    if q.strip():
        rows = study.convert(q)
        if rows:
            st.markdown("".join(ui.conversion_card(r) for r in rows), unsafe_allow_html=True)
            for r in rows[:1]:
                new = knowledge.by_id().get(f"{r['new']}-{r['new_sec']}") or next(
                    (c for c in knowledge.chunks() if c["act"] == r["new"] and c["section"].split("(")[0] == r["new_sec"].split("(")[0]), None)
                if new:
                    st.markdown(ui.source_card(new), unsafe_allow_html=True)
        else:
            st.markdown('<div class="lt-empty">That section is not in the table yet. Try the topic name instead, such as “cheating” or “bail”.</div>', unsafe_allow_html=True)
    st.markdown("#### Full conversion table")
    tabs = st.tabs(["IPC → BNS", "CrPC → BNSS", "Evidence Act → BSA"])
    for tab, old in zip(tabs, ["IPC", "CrPC", "IEA"]):
        with tab:
            data = [{"Old": f"{r['old']} {r['old_sec']}", "New": "—" if r["new_sec"] == "—" else f"{r['new']} {r['new_sec']}", "Topic": r["topic"]}
                    for r in knowledge.conversions() if r["old"] == old]
            st.dataframe(data, use_container_width=True, hide_index=True)


# ─────────────────────────────── Cases ───────────────────────────────
def page_cases() -> None:
    head("Landmark cases", "The judgments every Indian law student cites, in order. Open a case for facts, holding and why it matters.")
    cs = knowledge.cases()
    areas = sorted({c["area"] for c in cs})
    c1, c2 = st.columns([2, 1])
    term = c1.text_input("Search cases", placeholder="e.g. privacy, arrest, basic structure, Article 21")
    pick = c2.multiselect("Area", areas)
    if pick:
        cs = [c for c in cs if c["area"] in pick]
    if term.strip():
        t = term.lower().replace("article ", "")
        cs = [c for c in cs if t in json.dumps(c).lower()]
    if not cs:
        st.markdown('<div class="lt-empty">No case matches. Clear the filters or search a broader word.</div>', unsafe_allow_html=True)
        return
    st.caption(f"{len(cs)} cases")
    st.markdown(ui.case_timeline(cs), unsafe_allow_html=True)


# ─────────────────────────────── Maxims ───────────────────────────────
def page_maxims() -> None:
    head("Maxims and glossary", "Latin maxims as flashcards: read the term, recall the meaning, then tap to check. "
                                "Below them, everyday legal words in plain language.")
    term = st.text_input("Search maxims and terms", placeholder="e.g. audi, liability, bail")
    ms = knowledge.maxims()
    if term.strip():
        ms = [m for m in ms if term.lower() in json.dumps(m).lower()]
    elif st.button("Shuffle cards", key="shuffle"):
        ms = random.sample(ms, len(ms))
    st.markdown(ui.maxim_cards(ms) if ms else '<div class="lt-empty">No maxim matches that word.</div>', unsafe_allow_html=True)
    st.markdown("#### Glossary")
    g = knowledge.glossary()
    items = [(k, v[0], v[1]) for k, v in sorted(g.items()) if not term.strip() or term.lower() in (k + v[1]).lower()]
    st.markdown(ui.term_cards(items), unsafe_allow_html=True)


# ─────────────────────────────── Clause check ───────────────────────────────
def page_scanner() -> None:
    head("Clause check", "Upload a rent agreement or contract. LAWTRACE marks risky clauses, says why, and links the law behind each concern.")
    t1, t2 = st.tabs(["Upload a file", "Paste text"])
    text = ""
    with t1:
        up = st.file_uploader("PDF or text file", type=["pdf", "txt", "md"])
        if up is not None:
            text = scanner.read_upload(up.name, up.getvalue())
            if not text.strip():
                st.error("No text could be read from this file. If it is a scanned image, paste the text instead.")
    with t2:
        if st.button("Load a sample rent agreement", key="sample_rent"):
            ss.scan_text = scanner.SAMPLE
        pasted = st.text_area("Agreement text", key="scan_text", height=220)
        text = text or pasted
    if not text.strip():
        st.markdown('<div class="lt-empty">Add a file or paste text to check it. Nothing you upload is stored.</div>', unsafe_allow_html=True)
        return
    r = scanner.scan(text)
    a, b = st.columns([1, 2.3], gap="large")
    with a:
        st.markdown(ui.score_dial(r["score"], r["verdict"]), unsafe_allow_html=True)
        st.metric("Clauses flagged", len(r["flags"]))
        if r["rent"]:
            st.metric("Monthly rent found", f"₹{r['rent']:,}")
        if r["deposit_months"]:
            st.metric("Deposit", f"{r['deposit_months']} months' rent")
    with b:
        if not r["flags"]:
            st.success("No risky patterns found. Still read every clause before you sign.")
        st.markdown("".join(ui.flag_card(f) for f in r["flags"]), unsafe_allow_html=True)
        if llm.available() and r["flags"] and st.button("Suggest fairer wording with AI", key="negotiate"):
            from lawtrace.generation import prompts
            flags = "\n".join(f"- {f.rule}: {f.clause}" for f in r["flags"])
            with st.spinner("Drafting suggestions…"):
                try:
                    st.markdown(llm.generate("You help tenants negotiate fair agreements in India.",
                                             prompts.SCAN.format(flags=flags, doc=text[:6000], language="English")))
                except llm.LLMError as err:
                    st.error(str(err))
    report = [f"# LAWTRACE clause check\n\nFairness score: {r['score']}/100 — {r['verdict']}\n"]
    for f in r["flags"]:
        report.append(f"## {f.rule} ({f.severity})\n> {f.clause}\n\n{f.why}\n")
    report.append("\n_Information, not legal advice._")
    st.download_button("Download this report", "\n".join(report), file_name="lawtrace-clause-check.md")


# ─────────────────────────────── Practice ───────────────────────────────
def page_practice() -> None:
    head("Practice", "Quick self-tests on new criminal laws, landmark cases, maxims and bare-act provisions. A new set every time.")
    c1, c2, c3 = st.columns([1, 2, 1], vertical_alignment="bottom")
    n = c1.select_slider("Questions", [5, 8, 10, 15], value=8)
    kinds = {"Old → new": "convert", "Case law": "case", "Maxims": "maxim", "Bare acts": "section"}
    chosen = c2.multiselect("Topics", list(kinds), default=list(kinds))
    if c3.button("New set", key="newset", use_container_width=True):
        ss.quiz_seed = random.randint(0, 10_000)
        ss.pop("quiz_done", None)
    if not chosen:
        st.markdown('<div class="lt-empty">Pick at least one topic.</div>', unsafe_allow_html=True)
        return
    qs = study.quiz(n, seed=ss.quiz_seed, topics=tuple(kinds[c] for c in chosen))
    with st.form(f"quiz_{ss.quiz_seed}_{n}_{'-'.join(chosen)}"):
        picks = []
        for i, q in enumerate(qs, 1):
            st.markdown(f"**{i}. {q['q']}**  \n<span class='lt-tag'>{q['kind']}</span>", unsafe_allow_html=True)
            picks.append(st.radio(f"q{i}", q["options"], index=None, key=f"r_{ss.quiz_seed}_{i}", label_visibility="collapsed"))
        done = st.form_submit_button("Check my answers")
    if done:
        right = sum(p == q["answer"] for p, q in zip(picks, qs))
        st.markdown(f'<div class="lt-score">{right} / {len(qs)}</div>', unsafe_allow_html=True)
        for i, (p, q) in enumerate(zip(picks, qs), 1):
            ok = p == q["answer"]
            mark = "✓" if ok else "✗"
            st.markdown(f"{mark} **{i}.** {'Correct' if ok else 'Answer: ' + q['answer']}")
            st.markdown(f"<div class='lt-explain'>{q['explain']}</div>", unsafe_allow_html=True)


# ─────────────────────────────── About ───────────────────────────────
def page_about() -> None:
    head("How LAWTRACE works", "A retrieval-augmented assistant: it searches the law first, then answers only from what it found.")
    idx = warm_index()
    st.markdown('<div class="lt-pipe"><span>Bare acts (PDF)</span><i>→</i><span>Section-aware chunks</span><i>→</i>'
                '<span>BM25 index</span><span>Meaning index</span><i>→</i><span>Rank fusion</span><i>→</i>'
                '<span>Rerank</span><i>→</i><span>Answer with citations</span><i>→</i><span>Citation check</span></div>',
                unsafe_allow_html=True)
    c = st.columns(4)
    c[0].metric("Laws", len(knowledge.acts()))
    c[1].metric("Provisions indexed", len(knowledge.chunks()))
    c[2].metric("Landmark cases", len(knowledge.cases()))
    c[3].metric("Old → new mappings", len(knowledge.conversions()))
    st.markdown(f"""
- **Meaning search:** {idx.sem.name}
- **Reranker:** {idx.reranker_name}
- **Answer engine:** {llm.provider_label()}
- **Safety rails:** answers only from retrieved sections, refuses when nothing matches, and checks every citation in a model's answer against the retrieved set.
""")
    res = ROOT / "evaluation" / "results.json"
    if res.exists():
        m = json.loads(res.read_text())
        st.markdown("#### Retrieval evaluation")
        st.caption(f"{m['n']} hand-written questions with known correct sections, including Hindi and old-law references.")
        e = st.columns(4)
        e[0].metric("Hit@1", f"{m['hit@1']:.0%}")
        e[1].metric("Hit@5", f"{m['hit@5']:.0%}")
        e[2].metric("MRR", f"{m['mrr']:.2f}")
        e[3].metric("Correct refusals", f"{m['refusal_accuracy']:.0%}")
    st.markdown("""
#### Adding the full text of more acts
1. Download bare-act PDFs from [India Code](https://www.indiacode.nic.in/) into `data/raw/`, named like `Bharatiya Nyaya Sanhita__2023.pdf`.
2. Run `python -m lawtrace.ingestion.chunker --input data/raw --output data/processed/chunks.jsonl`.
3. Restart the app. The new sections are searchable and cited like the built-in ones.

The built-in provisions are study summaries written for LAWTRACE, not the official wording. Laws change; always confirm with the official text.
""")


ROUTES = {"Ask": page_ask, "Simplify": page_simplify, "Bare acts": page_bare_acts, "Old → New": page_convert,
          "Cases": page_cases, "Maxims": page_maxims, "Clause check": page_scanner, "Practice": page_practice, "About": page_about}

if not ss.entered:
    gate()
else:
    warm_index()
    ROUTES[shell()]()
