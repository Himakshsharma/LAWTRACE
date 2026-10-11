"""HTML building blocks. Pure functions returning strings, so they can be unit-tested and previewed."""
from __future__ import annotations

import html

from .. import knowledge

e = html.escape

COMPONENT_CSS = """
/* brand */
.lt-brand{display:flex; align-items:center; gap:.7rem; text-decoration:none;}
.lt-brand svg{flex:none}
.lt-brand b{font-family:var(--serif); font-weight:400; letter-spacing:.32em; font-size:1rem; color:var(--parchment);}

/* gate hero */
.lt-hero{text-align:center; margin:clamp(3rem,15vh,9rem) auto 1.6rem; max-width:860px; padding:0 16px;}
.lt-hero h1{font-family:var(--serif) !important; font-size:clamp(2.6rem,8vw,5.6rem) !important; line-height:1.02 !important;
  letter-spacing:.06em; margin:0 0 1.1rem !important; padding:0 !important; text-shadow:0 2px 24px rgba(0,0,0,.6);
  animation:lt-track 1.6s cubic-bezier(.2,.7,.2,1) both;}
@keyframes lt-track{from{letter-spacing:.42em; opacity:0}to{letter-spacing:.06em; opacity:1}}
.lt-hero .rule{width:120px; height:1.5px; margin:0 auto 1.3rem; background:var(--brass); transform-origin:center; animation:lt-rule 1.2s .6s ease-out both;}
@keyframes lt-rule{from{transform:scaleX(0)}to{transform:scaleX(1)}}
.lt-hero p{font-family:var(--serif); font-size:clamp(1.1rem,2.3vw,1.55rem); line-height:1.55; color:var(--parchment); margin:0 auto; max-width:30ch; text-shadow:0 1px 14px rgba(0,0,0,.7);}
.lt-gate-foot{display:flex; justify-content:space-between; align-items:flex-end; gap:1rem; margin-top:clamp(4rem,24vh,15rem); color:var(--muted); font-size:.82rem; flex-wrap:wrap;}
.lt-gate-acts{display:flex; gap:.5rem; flex-wrap:wrap;}
.lt-gate-acts span{border:1px solid var(--brass-dim); border-radius:var(--r-pill); padding:.22rem .7rem; color:var(--parchment); background:rgba(5,7,11,.5);}

/* masthead under the nav */
.lt-masthead{border:1px solid var(--brass-faint); border-radius:18px; padding:1.5rem 1.7rem; margin:.4rem 0 1.4rem;}
.lt-masthead h2{margin:0 0 .35rem !important; padding:0 !important; font-size:clamp(1.5rem,3vw,2.1rem) !important;}
.lt-masthead p{margin:0; color:var(--muted); max-width:68ch; font-size:.98rem;}

/* trace thread: the signature element */
.lt-trace{position:relative; padding:.2rem 0 .2rem 30px; margin-top:.2rem;}
.lt-trace::before{content:""; position:absolute; left:8px; top:10px; bottom:12px; width:1.5px;
  background:linear-gradient(var(--brass-hi), var(--brass) 60%, var(--brass-dim)); transform-origin:top; animation:lt-draw 1.1s ease-out both;}
@keyframes lt-draw{from{transform:scaleY(0)}to{transform:scaleY(1)}}
.lt-step{position:relative; margin:0 0 1.05rem;}
.lt-step::before{content:""; position:absolute; left:-27px; top:.32rem; width:11px; height:11px; border-radius:50%;
  background:var(--ink); border:1.5px solid var(--brass);}
.lt-step.end::before{background:var(--brass);}
.lt-step .k{font-size:.78rem; color:var(--muted); margin-bottom:.2rem;}
.lt-step .v{font-size:.92rem; color:var(--parchment);}
.lt-q{font-family:var(--serif); font-style:italic;}
.lt-lanes{display:grid; grid-template-columns:1fr 1fr; gap:.7rem;}
.lt-lane{background:var(--ink-2); border:1px solid var(--brass-faint); border-radius:10px; padding:.55rem .65rem;}
.lt-lane .t{font-size:.74rem; color:var(--muted); margin-bottom:.35rem;}
.lt-hit{display:grid; grid-template-columns:1fr auto; gap:.1rem .4rem; font-size:.8rem; margin:.18rem 0;}
.lt-hit i{grid-column:1/3; height:3px; border-radius:2px; background:var(--brass-faint); overflow:hidden; font-style:normal;}
.lt-hit i b{display:block; height:100%; background:var(--brass);}
.lt-hit span:last-of-type{color:var(--quiet); font-variant-numeric:tabular-nums;}
.lt-stamps{display:flex; flex-wrap:wrap; gap:.4rem;}
.lt-stamp{font-family:var(--serif); font-size:.82rem; border:1.5px solid var(--brass); color:var(--brass-hi);
  border-radius:6px; padding:.12rem .5rem; transform:rotate(-1.2deg); background:rgba(217,169,58,.06);}
.lt-stamp:nth-child(2n){transform:rotate(.8deg);}
.lt-empty{color:var(--muted); font-size:.92rem; border:1px dashed var(--brass-dim); border-radius:12px; padding:1rem;}

/* source / section cards */
.lt-card{display:grid; grid-template-columns:6px 1fr; gap:0 1rem; background:var(--ink-2); border:1px solid var(--brass-faint);
  border-radius:var(--r-card); padding:1rem 1.1rem 1rem 0; margin:0 0 .75rem; overflow:hidden;}
.lt-card .spine{border-radius:0 4px 4px 0;}
.lt-card .cite{font-family:var(--serif); font-size:1.02rem; color:var(--parchment);}
.lt-card .cite small{color:var(--muted); font-family:var(--sans); font-size:.78rem; margin-left:.35rem;}
.lt-card .ttl{color:var(--brass-hi); font-size:.92rem; margin:.1rem 0 .45rem;}
.lt-card .plain{font-family:var(--serif); font-size:.96rem; line-height:1.65; margin:0 0 .5rem;}
.lt-card details summary{cursor:pointer; color:var(--muted); font-size:.84rem;}
.lt-card details summary:hover{color:var(--brass-hi);}
.lt-card details p{font-size:.9rem; color:var(--parchment); opacity:.9; margin:.45rem 0 0; line-height:1.7;}
.lt-card .meta{display:flex; gap:.9rem; flex-wrap:wrap; font-size:.78rem; color:var(--quiet); margin-top:.5rem;}
.lt-tag{display:inline-block; font-size:.74rem; border:1px solid var(--brass-dim); border-radius:var(--r-pill); padding:.05rem .55rem; color:var(--muted);}

/* converter */
.lt-conv{display:grid; grid-template-columns:1fr auto 1fr; align-items:center; gap:1rem; background:var(--ink-2);
  border:1px solid var(--brass-faint); border-radius:var(--r-card); padding:1rem 1.2rem; margin-bottom:.7rem;}
.lt-conv .old{font-family:var(--serif); font-size:1.35rem; color:var(--muted); text-decoration:line-through; text-decoration-color:var(--high); text-decoration-thickness:1.5px;}
.lt-conv .new{font-family:var(--serif); font-size:1.6rem; color:var(--brass-hi); text-align:right;}
.lt-conv .arrow{width:clamp(40px,10vw,120px); height:1.5px; background:var(--brass); position:relative;}
.lt-conv .arrow::after{content:""; position:absolute; right:-1px; top:-4px; border:5px solid transparent; border-left:8px solid var(--brass); border-right:0;}
.lt-conv .topic{grid-column:1/4; color:var(--parchment); font-size:.92rem; opacity:.85;}
.lt-conv.gone .new{color:var(--high); font-size:1.1rem;}

/* cases timeline */
.lt-timeline{position:relative; padding-left:86px;}
.lt-timeline::before{content:""; position:absolute; left:64px; top:6px; bottom:6px; width:1.5px; background:var(--brass-dim);}
.lt-case{position:relative; margin-bottom:1rem;}
.lt-case .yr{position:absolute; left:-86px; top:.85rem; width:52px; text-align:right; font-family:var(--serif); color:var(--brass-hi); font-size:.95rem;}
.lt-case::before{content:""; position:absolute; left:-26px; top:1.05rem; width:9px; height:9px; border-radius:50%; background:var(--brass);}
.lt-case details{background:var(--ink-2); border:1px solid var(--brass-faint); border-radius:var(--r-card); padding:.8rem 1rem;}
.lt-case summary{cursor:pointer; list-style:none; font-family:var(--serif); font-size:1.04rem;}
.lt-case summary::-webkit-details-marker{display:none;}
.lt-case summary .area{font-family:var(--sans); font-size:.75rem; color:var(--muted); margin-left:.5rem;}
.lt-case details[open] summary{color:var(--brass-hi); margin-bottom:.5rem;}
.lt-case dl{display:grid; grid-template-columns:auto 1fr; gap:.35rem .9rem; margin:0; font-size:.92rem;}
.lt-case dt{color:var(--muted);} .lt-case dd{margin:0; line-height:1.6;}

/* maxim flashcards */
.lt-maxims{display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:.8rem;}
.lt-maxim{background:var(--ink-2); border:1px solid var(--brass-faint); border-radius:var(--r-card); padding:1.1rem 1.1rem 1rem; min-height:132px;}
.lt-maxim summary{cursor:pointer; list-style:none; font-family:var(--serif); font-style:italic; font-size:1.12rem; color:var(--parchment);}
.lt-maxim summary::-webkit-details-marker{display:none;}
.lt-maxim summary small{display:block; font-style:normal; font-family:var(--sans); font-size:.76rem; color:var(--quiet); margin-top:.5rem;}
.lt-maxim[open]{border-color:var(--brass);}
.lt-maxim[open] summary small{display:none;}
.lt-maxim .m{color:var(--brass-hi); font-family:var(--serif); margin:.55rem 0 .3rem;}
.lt-maxim .u{font-size:.86rem; color:var(--muted); line-height:1.55;}

/* clause check */
.lt-dial{width:150px; height:150px; border-radius:50%; display:grid; place-items:center; margin:.2rem auto .6rem;}
.lt-dial > div{width:118px; height:118px; border-radius:50%; background:var(--ink); display:grid; place-items:center; text-align:center;}
.lt-dial b{font-family:var(--serif); font-size:2.3rem; font-weight:400; line-height:1;}
.lt-dial span{font-size:.72rem; color:var(--muted);}
.lt-verdict{text-align:center; font-family:var(--serif); font-size:1.1rem;}
.lt-flag{border-left:3px solid var(--sev); background:var(--ink-2); border-radius:0 var(--r-card) var(--r-card) 0; padding:.85rem 1.1rem; margin-bottom:.7rem;}
.lt-flag .h{display:flex; justify-content:space-between; gap:1rem; align-items:baseline;}
.lt-flag .h b{font-weight:600; font-size:.98rem;}
.lt-flag .h span{font-size:.76rem; color:var(--sev); border:1px solid var(--sev); border-radius:var(--r-pill); padding:.02rem .55rem; white-space:nowrap;}
.lt-flag q{display:block; font-family:var(--serif); font-style:italic; color:var(--parchment); opacity:.85; margin:.5rem 0; font-size:.92rem; quotes:"“" "”";}
.lt-flag p{font-size:.9rem; margin:.2rem 0 .45rem; color:var(--parchment);}
.lt-chip{display:inline-block; font-size:.76rem; border:1px solid var(--brass-dim); color:var(--brass-hi); border-radius:var(--r-pill); padding:.05rem .6rem; margin:0 .3rem .25rem 0; cursor:help;}

/* simplifier */
.lt-original{font-family:var(--serif); line-height:1.95; background:var(--ink-2); border:1px solid var(--brass-faint); border-radius:var(--r-card); padding:1rem 1.2rem;}
abbr.lt-jargon{text-decoration:none; border-bottom:1.5px dotted var(--brass); cursor:help; color:var(--brass-hi);}
.lt-plain{font-family:var(--serif); font-size:1.02rem; line-height:1.75;}
.lt-terms{display:grid; grid-template-columns:repeat(auto-fill,minmax(210px,1fr)); gap:.55rem;}
.lt-term{border:1px solid var(--brass-faint); border-radius:10px; padding:.55rem .75rem; background:var(--ink-2);}
.lt-term b{font-family:var(--serif); font-weight:400; color:var(--brass-hi);}
.lt-term div{font-size:.84rem; color:var(--muted); margin-top:.15rem;}

/* bare acts */
.lt-acts{display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:.6rem; margin-bottom:1rem;}
.lt-act{border:1px solid var(--brass-faint); border-left:4px solid var(--c); border-radius:10px; padding:.6rem .8rem; background:var(--ink-2);}
.lt-act b{font-family:var(--serif); font-weight:400; display:block;}
.lt-act span{font-size:.76rem; color:var(--muted);}
.lt-sotd{display:grid; grid-template-columns:auto 1fr; gap:1.2rem; align-items:center; border:1px solid var(--brass-dim); border-radius:18px; padding:1.1rem 1.3rem; margin-bottom:1.2rem; background:linear-gradient(90deg, rgba(217,169,58,.08), transparent);}
.lt-sotd .num{font-family:var(--serif); font-size:2.6rem; color:var(--brass-hi); line-height:1;}
.lt-sotd .num small{display:block; font-family:var(--sans); font-size:.72rem; color:var(--muted); margin-top:.3rem;}
.lt-sotd h4{margin:0 0 .25rem !important; padding:0 !important; font-size:1.1rem !important;}
.lt-sotd p{margin:0; font-size:.93rem; color:var(--parchment); opacity:.9;}

/* practice */
.lt-score{font-family:var(--serif); font-size:2rem; color:var(--brass-hi);}
.lt-explain{font-size:.88rem; color:var(--muted); border-left:2px solid var(--brass-dim); padding-left:.7rem; margin:.2rem 0 1rem;}

/* about */
.lt-pipe{display:flex; flex-wrap:wrap; align-items:center; gap:.4rem; margin:.6rem 0 1.2rem;}
.lt-pipe span{border:1px solid var(--brass-dim); border-radius:8px; padding:.35rem .7rem; font-size:.84rem; background:var(--ink-2);}
.lt-pipe i{color:var(--brass); font-style:normal;}

/* persistent disclaimer */
.lt-disclaimer{position:fixed; left:0; right:0; bottom:0; z-index:99; text-align:center; font-size:.76rem; color:var(--muted);
  background:rgba(5,7,11,.92); border-top:1px solid var(--brass-faint); padding:.4rem 16px; backdrop-filter:blur(4px);}
.lt-disclaimer b{color:var(--brass-hi); font-weight:500;}
.lt-gate .lt-disclaimer{background:rgba(5,7,11,.6);}

@media (max-width:760px){
  .lt-lanes{grid-template-columns:1fr;}
  .lt-conv{grid-template-columns:1fr; text-align:left;}
  .lt-conv .new{text-align:left;}
  .lt-conv .arrow{transform:rotate(90deg); margin:.4rem 0 .4rem 1rem; width:40px;}
  .lt-timeline{padding-left:24px;} .lt-timeline::before{left:6px;}
  .lt-case .yr{position:static; text-align:left; width:auto; margin-bottom:.2rem;} .lt-case::before{left:-22px;}
  .lt-sotd{grid-template-columns:1fr;}
}
"""


def brand(size: int = 34, word: bool = True) -> str:
    # Outlined monogram in the reference's spirit: an "L" and a "T" sharing one stroke, like a ruled margin.
    svg = (f'<svg width="{size}" height="{size}" viewBox="0 0 40 40" fill="none" stroke="#D9A93A" stroke-width="3" '
           'stroke-linecap="square" aria-hidden="true"><path d="M6 5v30h13"/><path d="M14 5h22M25 5v30"/>'
           '<path d="M14 13h6" stroke-width="2.4"/></svg>')
    return f'<div class="lt-brand" aria-label="LAWTRACE">{svg}{"<b>LAWTRACE</b>" if word else ""}</div>'


def gate_hero() -> str:
    return ('<div class="lt-hero"><h1>LAWTRACE</h1><div class="rule"></div>'
            '<p>Every question about Indian law, traced to the section that answers it.</p></div>')


def gate_foot() -> str:
    acts = "".join(f"<span>{e(a['short'] if a['short'] != 'Constitution' else 'Constitution')}</span>" for a in knowledge.acts().values())
    return (f'<div class="lt-gate-foot"><div>Supreme Court of India, Tilak Marg, New Delhi</div>'
            f'<div class="lt-gate-acts" aria-label="Laws inside">{acts}</div></div>')


def masthead(title: str, lede: str) -> str:
    return f'<div class="lt-masthead"><h2>{e(title)}</h2><p>{e(lede)}</p></div>'


def disclaimer() -> str:
    return ('<div class="lt-disclaimer"><b>Information, not legal advice.</b> Provisions are summarised for study; '
            'check the official text on India Code before relying on them. Free legal aid: NALSA helpline 15100.</div>')


def _hits(items: list[dict]) -> str:
    if not items:
        return '<div class="lt-hit"><span>No match</span></div>'
    top = max(i["score"] for i in items) or 1
    return "".join(f'<div class="lt-hit"><span>{e(i["cite"])}</span><span>{i["score"]:.2f}</span>'
                   f'<i><b style="width:{max(6, 100 * i["score"] / top):.0f}%"></b></i></div>' for i in items[:4])


def trace_html(t: dict | None) -> str:
    if not t:
        return ('<div class="lt-empty">Ask a question and LAWTRACE draws its path here: how your words were read, '
                'what each search found, and which sections the answer rests on.</div>')
    steps = [f'<div class="lt-step"><div class="k">Your question</div><div class="v lt-q">“{e(t["query"])}”</div></div>']
    if t.get("lang") and t["lang"] != "en":
        steps.append(f'<div class="lt-step"><div class="k">Language bridge</div><div class="v">Read in {"Hindi" if t["lang"] == "hi" else "Punjabi"}; searched with: {e(t["expanded"][-140:])}</div></div>')
    if t.get("conversions"):
        steps.append('<div class="lt-step"><div class="k">Old law converted</div><div class="v">' + "<br>".join(e(n) for n in t["conversions"]) + "</div></div>")
    elif t.get("references"):
        steps.append(f'<div class="lt-step"><div class="k">Direct reference spotted</div><div class="v">{e(", ".join(t["references"]))}</div></div>')
    if t.get("act_filter") and t["act_filter"] != "All":
        steps.append(f'<div class="lt-step"><div class="k">Searching only</div><div class="v">{e(t["act_filter"])}</div></div>')
    steps.append('<div class="lt-step"><div class="k">Two searches, side by side</div><div class="lt-lanes">'
                 f'<div class="lt-lane"><div class="t">Exact words (BM25)</div>{_hits(t["bm25"])}</div>'
                 f'<div class="lt-lane"><div class="t">Meaning ({e(t.get("semantic_name", "semantic").split(" (")[0])})</div>{_hits(t["semantic"])}</div></div></div>')
    steps.append(f'<div class="lt-step"><div class="k">Merged by rank fusion, then reranked</div><div class="v">{_hits(t["final"])}</div></div>')
    if t["confident"]:
        stamps = "".join(f'<span class="lt-stamp">{e(c)}</span>' for c in (t.get("cited") or [f["cite"] for f in t["final"][:3]]))
        steps.append(f'<div class="lt-step end"><div class="k">Sections the answer rests on</div><div class="lt-stamps">{stamps}</div></div>')
    else:
        steps.append('<div class="lt-step end"><div class="k">Result</div><div class="v">No section matched strongly enough, so LAWTRACE did not guess.</div></div>')
    return '<div class="lt-trace">' + "".join(steps) + "</div>"


def source_card(c: dict, open_text: bool = False) -> str:
    a = knowledge.acts().get(c["act"], {})
    colour = a.get("colour", "#D9A93A")
    plain = f'<p class="plain">{e(c["plain"])}</p>' if c.get("plain") else ""
    meta = [f'{e(a.get("name", c.get("act_name", "")))}, {a.get("year", c.get("year", ""))}']
    if c.get("referenced"):
        meta.append("cited in your question")
    link = f'<a href="{e(c["source_url"])}" target="_blank" rel="noopener">Official text on India Code</a>' if c.get("source_url") else ""
    label = "Statutory summary" if c.get("origin") == "curated" else "Text from the act"
    return (f'<div class="lt-card"><div class="spine" style="background:{colour}"></div><div>'
            f'<div class="cite">{e(knowledge.cite(c))}<small>{e(" · ".join(meta[:1]))}</small></div>'
            f'<div class="ttl">{e(c["title"])}</div>{plain}'
            f'<details{" open" if open_text else ""}><summary>{label}</summary><p>{e(c["text"])}</p></details>'
            f'<div class="meta">{link}{"<span>Mentioned in your question</span>" if c.get("referenced") else ""}</div></div></div>')


def conversion_card(r: dict) -> str:
    gone = r["new_sec"] == "—"
    new = "Not in the new law" if gone else f'{r["new"]} {r["new_sec"]}'
    return (f'<div class="lt-conv{" gone" if gone else ""}"><div class="old">{e(r["old"])} {e(r["old_sec"])}</div>'
            f'<div class="arrow" aria-hidden="true"></div><div class="new">{e(new)}</div><div class="topic">{e(r["topic"])}</div></div>')


def case_timeline(cases: list[dict]) -> str:
    items = []
    for c in cases:
        arts = ", ".join(f"Art. {a}" for a in c["articles"]) or "—"
        items.append(f'<div class="lt-case"><div class="yr">{c["year"]}</div><details><summary>{e(c["name"])}'
                     f'<span class="area">{e(c["area"])}</span></summary><dl><dt>Facts</dt><dd>{e(c["facts"])}</dd>'
                     f'<dt>Held</dt><dd>{e(c["held"])}</dd><dt>Why it matters</dt><dd>{e(c["why"])}</dd>'
                     f'<dt>Provisions</dt><dd>{e(arts)}</dd></dl></details></div>')
    return '<div class="lt-timeline">' + "".join(items) + "</div>"


def maxim_cards(ms: list[dict]) -> str:
    return '<div class="lt-maxims">' + "".join(
        f'<details class="lt-maxim"><summary>{e(m["term"])}<small>Tap to reveal</small></summary>'
        f'<div class="m">{e(m["meaning"])}</div><div class="u">{e(m["use"])}</div></details>' for m in ms) + "</div>"


def score_dial(score: int, verdict: str) -> str:
    col = "var(--ok)" if score >= 80 else "var(--med)" if score >= 50 else "var(--high)"
    return (f'<div class="lt-dial" style="background:conic-gradient({col} {score * 3.6}deg, var(--ink-3) 0)">'
            f'<div><div><b>{score}</b><br><span>fairness score</span></div></div></div>'
            f'<div class="lt-verdict" style="color:{col}">{e(verdict)}</div>')


def flag_card(f) -> str:
    sev = {"High": "var(--high)", "Medium": "var(--med)", "Info": "var(--info)"}[f.severity]
    chips = ""
    for ref in f.refs:
        c = knowledge.by_id().get(ref)
        if c:
            chips += f'<span class="lt-chip" title="{e(c["plain"])}">{e(knowledge.cite(c))}</span>'
    return (f'<div class="lt-flag" style="--sev:{sev}"><div class="h"><b>{e(f.rule)}</b><span>{e(f.severity)}</span></div>'
            f'<q>{e(f.clause)}</q><p>{e(f.why)}</p>{chips}</div>')


def term_cards(terms: list[tuple[str, str, str]]) -> str:
    return '<div class="lt-terms">' + "".join(
        f'<div class="lt-term"><b>{e(t)}</b><div>{e(m)}</div></div>' for t, _, m in terms) + "</div>"


def act_cards() -> str:
    counts = {}
    for c in knowledge.chunks():
        counts[c["act"]] = counts.get(c["act"], 0) + 1
    return '<div class="lt-acts">' + "".join(
        f'<div class="lt-act" style="--c:{a["colour"]}"><b>{e(a["name"])}</b><span>{a["year"]} · {counts.get(k, 0)} '
        f'{"articles" if a["unit"] == "Article" else "sections"}</span></div>' for k, a in knowledge.acts().items()) + "</div>"


def section_of_day(c: dict) -> str:
    unit = "Article" if c.get("unit") == "Article" else "Section"
    return (f'<div class="lt-sotd"><div class="num">{e(c["section"])}<small>{e(c["act"])} · {unit} of the day</small></div>'
            f'<div><h4>{e(c["title"])}</h4><p>{e(c["plain"])}</p></div></div>')
