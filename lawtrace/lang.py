"""Language detection and a small Hindi / Hinglish legal vocabulary bridge.

Retrieval runs in English. When an LLM is configured, the answer is written back
in the user's language; offline, the Hindi words are mapped so retrieval still works.
"""
from __future__ import annotations

import re

DEVANAGARI = re.compile(r"[ऀ-ॿ]")
GURMUKHI = re.compile(r"[਀-੿]")

# Hindi (Devanagari) and Hinglish words → English legal search terms
VOCAB = {
    "चोरी": "theft", "chori": "theft",
    "हत्या": "murder", "क़त्ल": "murder", "katl": "murder", "qatl": "murder",
    "जमानत": "bail", "ज़मानत": "bail", "jamanat": "bail", "zamanat": "bail",
    "अग्रिम जमानत": "anticipatory bail",
    "गिरफ्तारी": "arrest", "गिरफ़्तारी": "arrest", "giraftari": "arrest", "giraftar": "arrest",
    "प्राथमिकी": "FIR", "एफआईआर": "FIR", "शिकायत": "complaint", "shikayat": "complaint",
    "पुलिस": "police", "थाना": "police station", "thana": "police station",
    "दहेज": "dowry", "dahej": "dowry",
    "धोखाधड़ी": "cheating fraud", "धोखा": "cheating", "dhokha": "cheating", "dhokhadhadi": "cheating fraud",
    "मानहानि": "defamation", "manhani": "defamation",
    "धमकी": "criminal intimidation threat", "dhamki": "criminal intimidation threat",
    "उपभोक्ता": "consumer", "upbhokta": "consumer", "रिफंड": "refund",
    "सूचना का अधिकार": "right to information RTI", "सूचना": "information",
    "किराया": "rent", "kiraya": "rent", "किरायेदार": "tenant", "kirayedar": "tenant",
    "मकान मालिक": "landlord", "makan malik": "landlord",
    "जमा राशि": "security deposit", "सिक्योरिटी": "security deposit",
    "तलाक": "divorce", "talaq": "divorce", "भरण पोषण": "maintenance", "गुजारा भत्ता": "maintenance",
    "पत्नी": "wife", "pati": "husband", "पति": "husband", "patni": "wife",
    "मुफ्त वकील": "free legal aid", "वकील": "lawyer advocate", "vakil": "lawyer advocate",
    "अदालत": "court", "adalat": "court", "न्यायालय": "court",
    "सबूत": "evidence", "saboot": "evidence", "सबूत इलेक्ट्रॉनिक": "electronic evidence",
    "बयान": "statement", "बलात्कार": "rape", "पीछा": "stalking",
    "मारपीट": "hurt assault", "maarpeet": "hurt assault", "marpit": "hurt assault",
    "अधिकार": "rights", "adhikar": "rights", "समानता": "equality", "जीवन": "life liberty",
    "शिक्षा": "education", "निजता": "privacy",
    "jawab": "reply", "जवाब": "reply", "kitne din": "how many days time limit", "कितने दिन": "how many days time limit",
    "pareshan": "harassment cruelty", "परेशान": "harassment cruelty", "jhooti": "false", "jhutha": "false",
    "naukri": "employment job", "नौकरी": "employment job", "zameen": "land property", "ज़मीन": "land property",
    "अपील": "appeal", "जुर्माना": "fine penalty", "सजा": "punishment", "saza": "punishment", "saja": "punishment",
}


def detect(text: str) -> str:
    """Return 'hi', 'pa' or 'en' (langdetect used when installed, for Latin-script text)."""
    if DEVANAGARI.search(text):
        return "hi"
    if GURMUKHI.search(text):
        return "pa"
    return "en"


LANG_NAMES = {"en": "English", "hi": "Hindi", "pa": "Punjabi"}


def bridge(text: str) -> str:
    """Append English legal terms for any Hindi/Hinglish words found."""
    low = text.lower()
    extra = []
    for k in sorted(VOCAB, key=len, reverse=True):
        hit = re.search(rf"\b{re.escape(k)}\b", low) if k.isascii() else k in text
        if hit:
            extra.append(VOCAB[k])
    return (text + " " + " ".join(extra)).strip() if extra else text
