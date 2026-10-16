"""Pluggable, free LLM access.

LLM_BACKEND = none (default) | ollama | gemini | groq

With `none` every project falls back to deterministic logic, so the whole
repo runs with zero keys and zero downloads. Model names change over time,
so they are read from env vars instead of being hard-coded.
"""
import os
import requests

TIMEOUT = 60


def backend() -> str:
    return os.getenv("LLM_BACKEND", "none").lower()


def complete(prompt: str, system: str = "") -> str | None:
    """Return model text, or None when no backend is configured or the call fails."""
    b = backend()
    try:
        if b == "ollama":
            r = requests.post(
                os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate"),
                json={"model": os.getenv("OLLAMA_MODEL", "llama3.2"),
                      "prompt": prompt, "system": system, "stream": False},
                timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()["response"].strip()
        if b == "groq":
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
                json={"model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
                      "messages": [{"role": "system", "content": system},
                                   {"role": "user", "content": prompt}],
                      "temperature": 0.1},
                timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        if b == "gemini":
            model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                params={"key": os.environ["GEMINI_API_KEY"]},
                json={"systemInstruction": {"parts": [{"text": system}]},
                      "contents": [{"parts": [{"text": prompt}]}]},
                timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as exc:  # never let the LLM take the service down
        print(f"[llm] {b} call failed: {exc}")
    return None
