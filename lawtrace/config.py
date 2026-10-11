"""Settings, read from Streamlit secrets first, then environment variables / .env."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(__file__).resolve().parent / "data"
PROCESSED_DIR = ROOT / "data" / "processed"
RAW_DIR = ROOT / "data" / "raw"
ASSETS_DIR = ROOT / "assets"


def _load_dotenv() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _get(name: str, default: str = "") -> str:
    try:  # Streamlit Cloud secrets
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Settings:
    llm_provider: str      # "gemini" | "ollama" | "offline"
    gemini_api_key: str
    gemini_model: str
    ollama_url: str
    ollama_model: str
    use_dense: bool        # sentence-transformers embeddings (needs extra install)
    dense_model: str
    use_cross_encoder: bool
    reranker_model: str


def get_settings() -> Settings:
    _load_dotenv()
    key = _get("GEMINI_API_KEY")
    provider = _get("LLM_PROVIDER", "gemini" if key else "offline").lower()
    return Settings(
        llm_provider=provider,
        gemini_api_key=key,
        gemini_model=_get("GEMINI_MODEL", "gemini-2.5-flash"),
        ollama_url=_get("OLLAMA_URL", "http://localhost:11434"),
        ollama_model=_get("OLLAMA_MODEL", "llama3.1"),
        use_dense=_get("USE_DENSE_EMBEDDINGS", "false").lower() == "true",
        dense_model=_get("DENSE_MODEL", "BAAI/bge-m3"),
        use_cross_encoder=_get("USE_CROSS_ENCODER", "false").lower() == "true",
        reranker_model=_get("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3"),
    )
