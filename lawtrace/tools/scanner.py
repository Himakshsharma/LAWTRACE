"""Clause check: flags risky clauses in rent agreements and simple contracts.

Rules are transparent regexes, so a student can read exactly why a clause was flagged.
Each flag links to the provision that explains the concern.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass, field

HIGH, MED, LOW = "High", "Medium", "Info"


@dataclass
class Flag:
    rule: str
    severity: str
    clause: str
    why: str
    refs: list[str] = field(default_factory=list)


_RULES = [
    ("Whole deposit can be forfeited", HIGH,
     r"(forfeit\w*|shall not be refund\w*|non[- ]refundable)[^.]{0,120}(deposit|advance)|(deposit|advance)[^.]{0,120}(forfeit\w*|non[- ]refundable|shall not be refund\w*)",
     "A deposit is security against actual dues or damage. A clause letting the owner keep all of it regardless of loss is one-sided; courts award only reasonable compensation for breach.",
     ["ICA-74", "MTA-11"]),
    ("Owner can enter without notice", HIGH,
     r"(enter|inspect|visit)[^.]{0,80}(at any time|without (?:any )?(?:prior )?notice|without intimation)",
     "Entry without notice affects your privacy. The Model Tenancy Act (where adopted) requires 24 hours' written notice, in daytime.",
     ["MTA-17", "Constitution-21"]),
    ("Eviction or termination without notice", HIGH,
     r"(evict|vacate|terminat\w*)[^.]{0,80}(without (?:any )?notice|immediately|forthwith|at (?:his|her|their|the owner'?s?|the landlord'?s?|sole) discretion)",
     "You should get reasonable written notice before having to leave. Most State rent laws and the Model Tenancy Act require a proper process.",
     ["MTA-9"]),
    ("Large or open-ended rent increase", MED,
     r"(rent|licen[cs]e fee)[^.]{0,80}(increase|enhance|escalat)\w*[^.]{0,60}(\b(1[1-9]|[2-9]\d)\s?%|at (?:the )?(?:sole )?discretion|as (?:decided|determined) by)",
     "An increase above about 10% a year, or one left to the owner's discretion, can make the rent unpredictable. Fix the percentage and the date in writing.",
     ["MTA-9"]),
    ("One-sided indemnity", MED,
     r"(tenant|licensee|lessee|employee|buyer)[^.]{0,60}(indemnif\w*|hold harmless)[^.]{0,80}(all|any|every)",
     "You promise to cover all of the other side's losses, even ones you did not cause. Limit it to losses caused by your own breach or negligence.",
     ["ICA-73"]),
    ("Penalty or heavy late fee", MED,
     r"(penalty|late (?:payment )?(?:fee|charge)|interest)[^.]{0,60}(\b([3-9]\d|\d{3,})\s?%|per day|daily|doubl)",
     "Courts award only reasonable compensation even if the contract names a bigger penalty. Very high daily or percentage charges may not be enforceable.",
     ["ICA-74"]),
    ("Non-compete after the contract ends", HIGH,
     r"(shall not|not to|cannot)[^.]{0,60}(work|join|engage|employ\w*|carry on|start)[^.]{0,80}(compet\w*|similar business|rival)[^.]{0,80}(after|following|post|for a period)",
     "Agreements that stop you working in a lawful trade or profession are void to that extent in India.",
     ["ICA-27"]),
    ("You give up the right to go to court or the consumer commission", HIGH,
     r"(waive\w*|shall not (?:approach|file|claim)|no (?:claim|complaint))[^.]{0,80}(court|consumer|forum|commission|legal (?:action|proceeding)|police)",
     "You cannot sign away your access to courts or consumer commissions. Such terms are generally unenforceable and a warning sign.",
     ["ICA-23", "CPA-2(47)"]),
    ("All repairs pushed onto tenant", MED,
     r"(all|any|every)\s+(?:major |structural )?(repairs?|maintenance)[^.]{0,80}(tenant|licensee|lessee)",
     "Structural repairs are usually the owner's job; only day-to-day, minor repairs are the tenant's. Split them clearly.",
     ["MTA-17"]),
    ("Lock-in period", LOW,
     r"lock[- ]?in",
     "You may have to pay rent for the whole lock-in even if you leave early. Check its length and whether it binds the owner too.",
     []),
    ("Disputes only in a distant city", LOW,
     r"(exclusive jurisdiction|courts? (?:at|of|in) [A-Z][a-z]+ (?:alone|only|shall have))",
     "Consumer complaints can still be filed where you live or work, whatever the contract says.",
     ["CPA-34"]),
]

_NUM = r"(?:rs\.?|inr|₹)\s?([\d,]+\d)"


def _amount(s: str) -> int | None:
    try:
        return int(s.replace(",", ""))
    except ValueError:
        return None


def _clause(text: str, start: int, end: int) -> str:
    a = max(text.rfind(".", 0, start), text.rfind("\n", 0, start)) + 1
    b_candidates = [i for i in (text.find(".", end), text.find("\n", end)) if i != -1]
    b = min(b_candidates) + 1 if b_candidates else len(text)
    return re.sub(r"\s+", " ", text[a:b]).strip()[:320]


def read_upload(name: str, data: bytes) -> str:
    if name.lower().endswith(".pdf"):
        from ..ingestion.parser import pdf_text

        return pdf_text(io.BytesIO(data))
    return data.decode("utf-8", errors="ignore")


def normalise(text: str) -> str:
    """Remove full stops inside abbreviations so clause boundaries are real sentence ends."""
    text = re.sub(r"\b(Rs|No|Mr|Ms|Mrs|Dr|Smt|Shri|Sh|viz|i\.e|e\.g|etc)\.", lambda m: m.group(1).replace(".", ""), text, flags=re.I)
    return text.replace("\r", "")


def scan(text: str) -> dict:
    text = normalise(text)
    flags: list[Flag] = []
    seen = set()
    for name, sev, pat, why, refs in _RULES:
        for m in re.finditer(pat, text, flags=re.I):
            clause = _clause(text, m.start(), m.end())
            if (name, clause) in seen:
                continue
            seen.add((name, clause))
            flags.append(Flag(name, sev, clause, why, refs))
            break

    # deposit-to-rent ratio
    rent = dep = None
    m = re.search(r"(?:monthly )?(?:rent|licen[cs]e fee)[^.\d₹]{0,40}" + _NUM, text, re.I)
    if m:
        rent = _amount(m.group(1))
    m2 = re.search(r"(?:security )?deposit[^.\d₹]{0,40}" + _NUM, text, re.I)
    if m2:
        dep = _amount(m2.group(1))
    months = round(dep / rent, 1) if rent and dep else None
    if months and months > 2:
        flags.insert(0, Flag("Security deposit above two months' rent", MED if months <= 4 else HIGH,
                             _clause(text, m2.start(), m2.end()),
                             f"The deposit is about {months:g} months' rent. The Model Tenancy Act (where a State has adopted it) caps residential deposits at 2 months.",
                             ["MTA-11"]))

    duration = re.search(r"(?:period|term|duration)[^.]{0,40}?(\d+)\s*(months?|years?)", text, re.I)
    term_months = None
    if duration:
        n = int(duration.group(1))
        term_months = n * 12 if duration.group(2).lower().startswith("year") else n
        if term_months > 12 and not re.search(r"\bregist(?:ered|ration)\b", text, re.I):
            flags.append(Flag("Long lease with no mention of registration", MED, _clause(text, duration.start(), duration.end()),
                              "A lease for more than one year must be registered; otherwise it has very limited value as evidence.",
                              ["Registration-17", "Registration-49"]))

    order = {HIGH: 0, MED: 1, LOW: 2}
    flags.sort(key=lambda f: order[f.severity])
    score = max(0, 100 - sum({HIGH: 22, MED: 10, LOW: 3}[f.severity] for f in flags))
    verdict = ("Looks balanced" if score >= 80 else "Needs a few changes" if score >= 50 else "Get legal advice before signing")
    return {"flags": flags, "score": score, "verdict": verdict, "rent": rent, "deposit": dep,
            "deposit_months": months, "term_months": term_months, "words": len(text.split())}


SAMPLE = """RENT AGREEMENT
This agreement is made at Shimla between Mr. R. Sharma (Owner) and Ms. A. Verma (Tenant).
1. The tenancy shall be for a period of 24 months commencing 1 November 2026.
2. The monthly rent shall be Rs. 18,000 payable on or before the 5th of every month.
3. The Tenant has paid a security deposit of Rs. 1,08,000 which shall be forfeited in full if the Tenant leaves before the lock-in period of 12 months.
4. The rent shall be increased by 15% every year, or as decided by the Owner.
5. The Owner may enter and inspect the premises at any time without notice.
6. All repairs and maintenance of the premises shall be borne by the Tenant.
7. A late fee of Rs. 500 per day shall be charged on delayed rent.
8. The Tenant shall indemnify the Owner against all claims, losses and expenses of every kind.
9. The Owner may terminate this agreement and evict the Tenant without notice at his sole discretion.
10. The Tenant waives any right to approach any court or consumer forum regarding this agreement.
"""
