"""Runs every page of app.py end to end.

Uses Streamlit's own AppTest when Streamlit is installed; otherwise a call-recording stub,
so the page logic is still exercised in minimal environments.
"""
import importlib.util
import runpy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
APP = str(ROOT / "app.py")
PAGES = ["Ask", "Simplify", "Bare acts", "Old → New", "Cases", "Maxims", "Clause check", "Practice", "About"]
HAS_ST = importlib.util.find_spec("streamlit") is not None and "streamlit_stub" not in str(sys.modules.get("streamlit"))


def run_stub(state=None, inputs=None, clicks=None):
    sys.path.insert(0, str(Path(__file__).parent))
    import streamlit_stub

    saved = sys.modules.get("streamlit")
    st = streamlit_stub.install(inputs=inputs, clicks=clicks)
    st.session_state.update(state or {})
    try:
        runpy.run_path(APP, run_name="__main__")
    except streamlit_stub.RerunException:
        pass
    finally:
        if saved is not None:
            sys.modules["streamlit"] = saved
        else:
            sys.modules.pop("streamlit", None)
    return st


@pytest.mark.skipif(not HAS_ST, reason="streamlit not installed; stub tests cover this")
@pytest.mark.parametrize("page", PAGES)
def test_pages_with_apptest(page):
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["entered"] = True
    at.session_state["nav"] = page
    at.run()
    assert not at.exception, at.exception


@pytest.mark.skipif(not HAS_ST, reason="streamlit not installed")
def test_gate_then_ask_with_apptest():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception
    at.button(key="enter").click().run()
    assert at.session_state["entered"]
    at.chat_input[0].set_value("What is IPC 420 now?").run()
    assert not at.exception
    assert any("318" in m.value for m in at.markdown)


def test_gate_renders_stub():
    st = run_stub()
    html = "\n".join(st.html_out)
    assert "LAWTRACE" in html and "lt-hero" in html
    assert "Enter the court" in [c[1][0] for c in st.calls if c[0] == "button"]


def test_enter_button_switches_to_app_stub():
    st = run_stub(clicks={"enter"})
    assert st.session_state["entered"] is True
    assert st.session_state["nav"] == "Ask"


@pytest.mark.parametrize("page", PAGES)
def test_every_page_renders_stub(page):
    st = run_stub(state={"entered": True, "nav": page})
    assert any("lt-masthead" in h for h in st.html_out), page


def test_ask_flow_stub():
    st = run_stub(state={"entered": True, "nav": "Ask"}, inputs={"chat": "IPC 420 under the new law?"})
    msgs = st.session_state["messages"]
    assert msgs[-1]["role"] == "assistant"
    assert "318" in msgs[-1]["answer"]
    assert any("lt-trace" in h and "BNS s. 318" in h for h in st.html_out)


def test_interactive_tools_stub():
    from lawtrace.tools import scanner

    st = run_stub(state={"entered": True, "nav": "Clause check", "scan_text": scanner.SAMPLE})
    assert any("lt-flag" in h for h in st.html_out)
    st = run_stub(state={"entered": True, "nav": "Simplify"}, inputs={"simplify_text": "The lessee shall forthwith pay; provided that no interest is due."})
    assert any("lt-jargon" in h for h in st.html_out)
    st = run_stub(state={"entered": True, "nav": "Old → New"}, inputs={"conv_q": "IPC 498A"})
    assert any("BNS 85" in h for h in st.html_out)
    st = run_stub(state={"entered": True, "nav": "Practice"}, clicks={"form_submit"})
    assert any("lt-score" in h for h in st.html_out)
