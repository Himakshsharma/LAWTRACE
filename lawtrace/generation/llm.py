"""One interface over Gemini, Ollama, or no model (offline extractive mode)."""
from __future__ import annotations

import json
import logging
import urllib.request

from ..config import get_settings

log = logging.getLogger(__name__)


class LLMError(RuntimeError):
    pass


def provider_label() -> str:
    s = get_settings()
    if s.llm_provider == "gemini" and s.gemini_api_key:
        return f"Gemini · {s.gemini_model}"
    if s.llm_provider == "ollama":
        return f"Ollama · {s.ollama_model}"
    return "Offline (grounded extracts)"


def available() -> bool:
    s = get_settings()
    return (s.llm_provider == "gemini" and bool(s.gemini_api_key)) or s.llm_provider == "ollama"


def generate(system: str, prompt: str, temperature: float = 0.2) -> str:
    s = get_settings()
    if s.llm_provider == "gemini" and s.gemini_api_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=s.gemini_api_key)
            r = client.models.generate_content(
                model=s.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=system, temperature=temperature),
            )
            if not r.text:
                raise LLMError("Gemini returned an empty response.")
            return r.text
        except LLMError:
            raise
        except Exception as e:
            raise LLMError(f"Gemini request failed: {e}") from e
    if s.llm_provider == "ollama":
        body = json.dumps({
            "model": s.ollama_model, "stream": False, "options": {"temperature": temperature},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(f"{s.ollama_url}/api/chat", data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read())["message"]["content"]
        except Exception as e:
            raise LLMError(f"Ollama request failed: {e}") from e
    raise LLMError("No language model configured.")
