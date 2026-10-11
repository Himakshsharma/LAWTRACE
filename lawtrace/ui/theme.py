"""Visual system: court-night black, brass gold, parchment text, Libre Baskerville + Instrument Sans."""
from __future__ import annotations

import base64
from functools import lru_cache

from ..config import ASSETS_DIR

# Remote photograph of the Supreme Court of India (Wikimedia Commons). If it fails to load,
# the gold line drawing underneath shows instead. Put your own photo at
# assets/supreme_court.jpg to use it and skip the remote request.
REMOTE_PHOTO = "https://commons.wikimedia.org/wiki/Special:FilePath/Supreme_Court_of_India_-_Retouched.jpg?width=1920"


@lru_cache(maxsize=1)
def court_layers() -> str:
    """CSS background-image value: local photo or remote photo, over the line-art fallback."""
    layers = []
    for name, mime in (("supreme_court.jpg", "image/jpeg"), ("supreme_court.jpeg", "image/jpeg"),
                       ("supreme_court.png", "image/png"), ("supreme_court.webp", "image/webp")):
        p = ASSETS_DIR / name
        if p.exists():
            layers.append(f"url('data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}')")
            break
    else:
        layers.append(f"url('{REMOTE_PHOTO}')")
    svg = (ASSETS_DIR / "court_lineart.svg").read_bytes()
    layers.append(f"url('data:image/svg+xml;base64,{base64.b64encode(svg).decode()}')")
    return ", ".join(layers)


TOKENS = """
:root{
  --ink:#05070B; --ink-2:#0C1018; --ink-3:#131925;
  --brass:#D9A93A; --brass-hi:#F2C85B; --brass-dim:rgba(217,169,58,.32); --brass-faint:rgba(217,169,58,.10);
  --parchment:#EEE6D3; --muted:#A39B88; --quiet:#6F6A5E;
  --high:#E2694B; --med:#E0A83C; --info:#7FA6C9; --ok:#8DBF7A;
  --serif:'Libre Baskerville', 'GFS Baskerville', Georgia, 'Times New Roman', serif;
  --sans:'Instrument Sans', 'Segoe UI', system-ui, -apple-system, sans-serif;
  --r-pill:999px; --r-card:14px;
}
"""

BASE = """
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Instrument+Sans:wght@400;500;600&display=swap');
html, body, .stApp, [data-testid="stAppViewContainer"]{font-variant-numeric:lining-nums; background:var(--ink); color:var(--parchment); font-family:var(--sans);}
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer,
[data-testid="stStatusWidget"], [data-testid="stSidebarCollapsedControl"]{display:none !important;}
.block-container, [data-testid="stMainBlockContainer"]{padding-top:1.1rem; padding-bottom:5rem; max-width:1240px;}
*{font-variant-numeric:lining-nums;}
h1,h2,h3,h4{font-family:var(--serif) !important; color:var(--parchment); font-weight:400 !important; letter-spacing:.01em;}
p, li{line-height:1.65;}
a{color:var(--brass-hi) !important; text-decoration-color:var(--brass-dim);}
::selection{background:var(--brass); color:var(--ink);}
:focus-visible{outline:2px solid var(--brass-hi) !important; outline-offset:3px;}
hr{border-color:var(--brass-faint);}

/* buttons: gold-outlined pills, as in the reference */
.stButton button, .stDownloadButton button, [data-testid="stFormSubmitButton"] button{
  background:transparent; color:var(--parchment); border:1.5px solid var(--brass); border-radius:var(--r-pill);
  font-family:var(--sans); font-weight:500; padding:.45rem 1.25rem; transition:background .2s, color .2s;}
.stButton button:hover, .stDownloadButton button:hover, [data-testid="stFormSubmitButton"] button:hover{
  background:var(--brass); color:var(--ink); border-color:var(--brass);}
.stButton button:active{transform:translateY(1px);}

/* inputs */
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div, [data-testid="stChatInput"] > div{
  background:var(--ink-2) !important; border:1px solid var(--brass-dim) !important; border-radius:12px !important;}
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea, [data-testid="stChatInput"] textarea{
  color:var(--parchment) !important; font-family:var(--sans) !important;}
[data-testid="stChatInput"] button{background:var(--brass) !important; border-radius:50% !important;}
[data-testid="stChatInput"] button svg{fill:var(--ink) !important; color:var(--ink) !important;}
label, [data-testid="stWidgetLabel"] p{color:var(--muted) !important; font-size:.86rem !important;}

/* nav: horizontal radio rendered as text links with a brass underline (Streamlit >= 1.50 markup) */
.st-key-nav [data-testid="stRadioOption"] > div > div:first-child:not([data-testid]){display:none !important;}
.st-key-nav [data-testid="stRadioOption"]{padding:.35rem 0; margin:0; border-bottom:1.5px solid transparent; cursor:pointer;}
.st-key-nav [data-testid="stRadioOption"] p{font-size:.95rem; color:var(--parchment); opacity:.78;}
.st-key-nav [data-testid="stRadioOption"]:hover p{opacity:1;}
.st-key-nav [data-testid="stRadioOption"][data-selected="true"]{border-bottom-color:var(--brass);}
.st-key-nav [data-testid="stRadioOption"][data-selected="true"] p{opacity:1; color:var(--brass-hi);}
/* older Streamlit markup */
.st-key-nav [role="radiogroup"]{gap:.15rem 1.35rem; justify-content:center; flex-wrap:wrap;}
.st-key-nav label[data-baseweb="radio"] > div:first-child{display:none;}
.st-key-nav label[data-baseweb="radio"]{padding:.35rem 0; margin:0; border-bottom:1.5px solid transparent; cursor:pointer;}
.st-key-nav label[data-baseweb="radio"] p{font-size:.95rem; color:var(--parchment); opacity:.78;}
.st-key-nav label[data-baseweb="radio"]:hover p{opacity:1;}
.st-key-nav label[data-baseweb="radio"]:has(input:checked){border-bottom-color:var(--brass);}
.st-key-nav label[data-baseweb="radio"]:has(input:checked) p{opacity:1; color:var(--brass-hi);}

/* chat */
[data-testid="stChatMessage"]{background:transparent; padding:.9rem 0; border-bottom:1px solid var(--brass-faint);}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"]{font-family:var(--serif); font-size:1.0rem;}
[data-testid="stChatMessage"] h3{font-size:1.05rem !important; color:var(--brass-hi); margin:.6rem 0 .3rem;}
[data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"]{background:var(--ink-3); border:1px solid var(--brass-dim);}
[data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"]{background:var(--ink) !important;}
blockquote{border-left:2px solid var(--brass) !important; color:var(--parchment); background:var(--brass-faint); padding:.4rem .9rem !important; border-radius:0 8px 8px 0;}

/* expanders, tabs, uploader */
[data-testid="stExpander"] details{background:var(--ink-2); border:1px solid var(--brass-faint); border-radius:var(--r-card);}
[data-testid="stExpander"] summary:hover{color:var(--brass-hi);}
[data-baseweb="tab-list"]{gap:1.2rem; border-bottom:1px solid var(--brass-faint);}
button[role="tab"]{background:transparent !important;}
button[role="tab"] p{font-size:.95rem;}
button[role="tab"][aria-selected="true"] p{color:var(--brass-hi);}
[data-baseweb="tab-highlight"]{background:var(--brass) !important;}
[data-testid="stFileUploaderDropzone"]{background:var(--ink-2); border:1px dashed var(--brass-dim); border-radius:var(--r-card);}
[data-testid="stAlert"]{background:var(--ink-2); border:1px solid var(--brass-faint); border-radius:12px;}
[data-testid="stMetricValue"]{font-family:var(--serif);}

@media (prefers-reduced-motion: reduce){*{animation:none !important; transition:none !important;}}
"""

GATE = """
.stApp{background-image:linear-gradient(180deg, rgba(5,7,11,.42) 0%, rgba(5,7,11,.62) 45%, rgba(5,7,11,.92) 100%), {layers};
  background-size:cover; background-position:center 40%; background-attachment:fixed;}
[data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"], .main{background:transparent !important;}
.block-container, [data-testid="stMainBlockContainer"]{max-width:1240px; padding-top:1.4rem;}
@media (max-width:640px){
  .st-key-gatenav [data-testid="stHorizontalBlock"]{flex-wrap:nowrap !important; align-items:center;}
  .st-key-gatenav [data-testid="stColumn"]:not(:first-child):not(:last-child){display:none !important;}
  .st-key-gatenav [data-testid="stColumn"]{width:auto !important; flex:1 1 auto !important; min-width:0 !important;}
  .st-key-gatenav [data-testid="stColumn"]:last-child{flex:0 0 auto !important;}
}
.st-key-gatenav .stButton button{border:none; padding:.3rem .2rem; font-size:.95rem; opacity:.85; background:transparent;}
.st-key-gatenav .stButton button:hover{background:transparent; color:var(--brass-hi); opacity:1;}
.st-key-go_start .stButton button, .st-key-go_start button{border:1.5px solid var(--brass) !important; padding:.5rem 1.5rem !important; opacity:1 !important;}
.st-key-go_start button:hover{background:var(--brass) !important; color:var(--ink) !important;}
.st-key-enter, .st-key-enter .stButton{display:flex !important; justify-content:center !important; width:100% !important;}
.st-key-enter button{font-family:var(--serif) !important; font-size:1.05rem !important; padding:.75rem 2.6rem !important;
  border:1.5px solid var(--brass) !important; background:rgba(5,7,11,.45) !important; backdrop-filter:blur(3px);}
.st-key-enter button:hover{background:var(--brass) !important; color:var(--ink) !important;}
"""


def css(gate: bool) -> str:
    from .components import COMPONENT_CSS

    out = TOKENS + BASE + COMPONENT_CSS
    if gate:
        out += GATE.replace("{layers}", court_layers())
    return f"<style>{out}</style>"


def masthead_css() -> str:
    return (".lt-masthead{background-image:linear-gradient(90deg, rgba(5,7,11,.97) 35%, rgba(5,7,11,.78) 100%), "
            + court_layers() + "; background-size:cover; background-position:center 35%;}")
