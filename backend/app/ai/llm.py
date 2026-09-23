"""The one place the backend calls an LLM (briefing E15, assistant E23).

Provider comes from LLM_PROVIDER in .env:
- `gemini`    — Google Gemini API (free tier), key in LLM_API_KEY. Default model
                `gemini-3.8-flash`.
- `anthropic` — Claude, key in LLM_API_KEY (or the SDK's own credential
                resolution). Default model `claude-opus-5`.
LLM_MODEL overrides the default model. Anything else (or a missing key,
timeout, refusal, API error) raises `LLMUnavailable`, and every caller has a
non-LLM fallback — the demo must survive an API outage.
"""

import json
import logging

from app.config import settings

log = logging.getLogger(__name__)

DEFAULT_MODELS = {"gemini": "gemini-3.8-flash", "anthropic": "claude-opus-5"}
TIMEOUT_S = 15.0


class LLMUnavailable(Exception):
    pass


def complete_json(system: str, prompt: str, schema: dict, max_tokens: int = 2000) -> dict:
    """One structured-output call. Returns the parsed JSON object matching `schema`."""
    provider = settings.LLM_PROVIDER
    call = {"gemini": _gemini, "anthropic": _anthropic}.get(provider)
    if call is None:
        raise LLMUnavailable(f"LLM_PROVIDER '{provider}' is not implemented")
    model = settings.LLM_MODEL or DEFAULT_MODELS[provider]
    try:
        text = call(model, system, prompt, schema, max_tokens)
    except LLMUnavailable:
        raise
    except Exception as e:  # noqa: BLE001 — any SDK/network/credential failure → fallback, never a 500
        raise LLMUnavailable(f"{provider} call failed: {type(e).__name__}: {e}") from e
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMUnavailable(f"Model returned invalid JSON: {e}") from e


# ---------- Gemini (google-genai SDK) ----------

def _gemini(model: str, system: str, prompt: str, schema: dict, max_tokens: int) -> str:
    if not settings.LLM_API_KEY:
        raise LLMUnavailable("LLM_API_KEY is empty (get a free key at aistudio.google.com)")
    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=settings.LLM_API_KEY,
        http_options=types.HttpOptions(timeout=int(TIMEOUT_S * 1000)),  # milliseconds
    )
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_json_schema=schema,
            max_output_tokens=max_tokens,
        ),
    )
    text = response.text
    if not text:
        reason = response.candidates[0].finish_reason if response.candidates else "no candidates"
        raise LLMUnavailable(f"Gemini returned no text ({reason})")
    return text


# ---------- Anthropic (official SDK) ----------

def _anthropic(model: str, system: str, prompt: str, schema: dict, max_tokens: int) -> str:
    import anthropic

    # LLM_API_KEY from .env wins; otherwise the SDK's own resolution
    # (ANTHROPIC_API_KEY, `ant auth login` profile, ...).
    kwargs = {"timeout": TIMEOUT_S, "max_retries": 1}
    if settings.LLM_API_KEY:
        kwargs["api_key"] = settings.LLM_API_KEY
    client = anthropic.Anthropic(**kwargs)
    response = client.beta.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
        # Short, factual generation: low effort keeps it fast.
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": schema}},
        # On a safety decline, re-run server-side on Anthropic's recommended fallback model.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if response.stop_reason == "refusal":
        raise LLMUnavailable("Model declined the request")
    if response.stop_reason == "max_tokens":
        raise LLMUnavailable("Model output truncated")
    text = next((b.text for b in response.content if b.type == "text"), None)
    if text is None:
        raise LLMUnavailable("No text in model response")
    return text
