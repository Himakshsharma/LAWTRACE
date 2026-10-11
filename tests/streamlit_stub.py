"""A tiny stand-in for the `streamlit` module so app.py can be exercised in environments
where Streamlit is not installed. It records every call; it does not render anything."""
from __future__ import annotations

import sys
import types


class RerunException(Exception):
    pass


class SessionState(dict):
    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError as e:
            raise AttributeError(k) from e

    def __setattr__(self, k, v):
        self[k] = v


def make(inputs: dict | None = None, clicks: set | None = None):
    st = types.ModuleType("streamlit")
    st.calls = []
    st.html_out = []
    st.session_state = SessionState()
    st.query_params = {}
    st.secrets = {}
    inputs = inputs or {}
    clicks = clicks or set()

    class Ctx:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def __getattr__(self, name):
            return getattr(st, name)

    def rec(name, ret=None):
        def f(*a, **k):
            st.calls.append((name, a, k))
            return ret
        return f

    def markdown(body="", *a, **k):
        st.calls.append(("markdown", (body,), k))
        st.html_out.append(str(body))

    def columns(spec, **k):
        n = spec if isinstance(spec, int) else len(spec)
        return [Ctx() for _ in range(n)]

    def button(label, key=None, **k):
        st.calls.append(("button", (label,), {"key": key}))
        return (key or label) in clicks

    def _value(label, key, default):
        if key and key in st.session_state:
            return st.session_state[key]
        v = inputs.get(key or label, default)
        if key:
            st.session_state[key] = v
        return v

    def text_input(label, key=None, value="", **k):
        return _value(label, key, value)

    def text_area(label, key=None, value="", **k):
        return _value(label, key, value)

    def selectbox(label, options, index=0, format_func=str, key=None, **k):
        options = list(options)
        for o in options:
            format_func(o)
        return inputs.get(key or label, options[index] if options else None)

    def radio(label, options, index=0, key=None, **k):
        options = list(options)
        if key and key in st.session_state:
            return st.session_state[key]
        v = inputs.get(key or label, options[index] if index is not None and options else (options[0] if options else None))
        if key:
            st.session_state[key] = v
        return v

    def multiselect(label, options, default=None, **k):
        return inputs.get(label, list(default or []))

    def select_slider(label, options, value=None, **k):
        return value if value is not None else list(options)[0]

    def toggle(label, value=False, **k):
        return inputs.get(label, value)

    def chat_input(placeholder="", **k):
        return inputs.get("chat")

    def cache_resource(*da, **dk):
        if da and callable(da[0]):
            return da[0]
        return lambda f: f

    def rerun():
        raise RerunException()

    def form_submit_button(label, **k):
        return "form_submit" in clicks

    st.markdown = markdown
    st.columns = columns
    st.button = button
    st.text_input = text_input
    st.text_area = text_area
    st.selectbox = selectbox
    st.radio = radio
    st.multiselect = multiselect
    st.select_slider = select_slider
    st.toggle = toggle
    st.chat_input = chat_input
    st.cache_resource = cache_resource
    st.rerun = rerun
    st.form_submit_button = form_submit_button
    st.file_uploader = rec("file_uploader", None)
    for name in ("caption", "warning", "info", "success", "error", "metric", "dataframe", "download_button",
                 "set_page_config", "write"):
        setattr(st, name, rec(name))
    for name in ("container", "chat_message", "expander", "spinner", "form"):
        setattr(st, name, lambda *a, _n=name, **k: (st.calls.append((_n, a, k)), Ctx())[1])
    st.tabs = lambda labels, **k: [Ctx() for _ in labels]
    return st


def install(**kw):
    st = make(**kw)
    sys.modules["streamlit"] = st
    return st
