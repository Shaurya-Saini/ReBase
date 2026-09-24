"""The one place the backend calls an LLM (briefing E15, assistant E23).

Provider comes from LLM_PROVIDER in .env:
- `gemini`    — Google Gemini API (free tier), key in LLM_API_KEY. Default model
                `gemini-3.5-flash-lite` (fast), falls back to `gemini-3.8-flash`.
- `anthropic` — Claude, key in LLM_API_KEY (or the SDK's own credential
                resolution). Default model `claude-opus-5`.
- `groq`      — Groq (free tier), key in GROQ_API_KEY (or LLM_API_KEY).
                Default model `openai/gpt-oss-120b`.
LLM_MODEL overrides the primary's default model.

**Groq is also the automatic fallback:** if GROQ_API_KEY is set and the
primary provider fails for any reason, the same request goes to Groq.
If everything fails, `LLMUnavailable` is raised and every caller has a non-LLM
fallback — the demo must survive an API outage.
"""

import json
import logging

from app.config import settings

log = logging.getLogger(__name__)

DEFAULT_MODELS = {"gemini": "gemini-3.5-flash-lite", "anthropic": "claude-opus-5",
                  "groq": "openai/gpt-oss-120b"}
# `fast=True` (simple tasks like translating a question): a quicker model where one exists.
FAST_MODELS = {"gemini": "gemini-3.5-flash-lite", "groq": "openai/gpt-oss-20b"}
TIMEOUT_S = 15.0
GEMINI_TIMEOUT_S = 10.0  # per model attempt; with one fallback ≤ ~20 s per call
GROQ_TIMEOUT_S = 10.0


class LLMUnavailable(Exception):
    pass


def status() -> str:
    """One line for the startup log: which LLMs this server can use."""
    primary = settings.LLM_PROVIDER
    has_key = {"gemini": bool(settings.LLM_API_KEY), "anthropic": True,  # SDK may find its own credentials
               "groq": bool(settings.GROQ_API_KEY or (primary == "groq" and settings.LLM_API_KEY))}
    parts = [f"{p} {'✓ key set' if has_key.get(p) else '✗ NO KEY'}" for p in _providers()]
    if not any(has_key.get(p) for p in _providers()):
        return ("LLM: " + " → ".join(parts) + " — briefing uses templates; Hindi/Tamil questions "
                "can't be translated (set LLM_API_KEY / GROQ_API_KEY in .env and restart)")
    return "LLM: " + " → ".join(parts)


def _providers() -> list[str]:
    """Primary provider, then Groq as fallback when a Groq key is configured."""
    chain = [settings.LLM_PROVIDER]
    if settings.GROQ_API_KEY and "groq" not in chain:
        chain.append("groq")
    return chain


def _model_for(provider: str, fast: bool) -> str:
    if provider == settings.LLM_PROVIDER and settings.LLM_MODEL:
        return settings.LLM_MODEL
    if provider == "groq" and settings.GROQ_MODEL:
        return settings.GROQ_MODEL
    return (FAST_MODELS.get(provider) if fast else None) or DEFAULT_MODELS[provider]


def _call_one(provider: str, system: str, prompt: str, schema: dict, max_tokens: int, fast: bool) -> dict:
    call = {"gemini": _gemini, "anthropic": _anthropic, "groq": _groq}.get(provider)
    if call is None:
        raise LLMUnavailable(f"LLM_PROVIDER '{provider}' is not implemented")
    try:
        text = call(_model_for(provider, fast), system, prompt, schema, max_tokens)
    except LLMUnavailable as e:
        raise LLMUnavailable(f"{provider}: {e}") from e
    except Exception as e:  # noqa: BLE001 — any SDK/network/credential failure → fallback, never a 500
        raise LLMUnavailable(f"{provider} call failed: {type(e).__name__}: {e}") from e
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMUnavailable(f"{provider} returned invalid JSON: {e}") from e


def complete_json(system: str, prompt: str, schema: dict, max_tokens: int = 2000, fast: bool = False) -> dict:
    """One structured-output call. Returns the parsed JSON object matching `schema`.
    Tries the primary provider, then Groq (if configured). `fast=True` picks the
    provider's quicker model (ignored when LLM_MODEL / GROQ_MODEL is set)."""
    errors = []
    for provider in _providers():
        try:
            return _call_one(provider, system, prompt, schema, max_tokens, fast)
        except LLMUnavailable as e:
            log.info("llm: %s unavailable (%s)", provider, e)
            errors.append(str(e))
    raise LLMUnavailable(" | ".join(errors))


# ---------- Gemini (google-genai SDK) ----------

# Free-tier models are sometimes overloaded (503/504) or rate-limited (429): try
# the next one. Measured 2026-09-24: 3.5-flash-lite ~1-4 s and good Tamil/Hindi
# answers → default; 3.8-flash ~3-4 s when up but often 503 → fallback;
# 3.5-flash kept timing out → not used. Set LLM_MODEL to pick a different primary.
GEMINI_FALLBACKS = ["gemini-3.8-flash"]
GEMINI_RETRY_CODES = {429, 503, 504}
# Gemini 3.x can't turn thinking off, only lower it; default is "medium" (slow).
# 3.8-flash rejects "minimal"; flash-lite already defaults to minimal.
GEMINI_THINKING = {"gemini-3.8-flash": "low"}


def _gemini(model: str, system: str, prompt: str, schema: dict, max_tokens: int) -> str:
    if not settings.LLM_API_KEY:
        raise LLMUnavailable("LLM_API_KEY is empty (get a free key at aistudio.google.com)")
    from google import genai
    from google.genai import errors, types

    client = genai.Client(
        api_key=settings.LLM_API_KEY,
        # One attempt per model: the SDK's default is 5 attempts with backoff up to 60 s,
        # which produced ~2-minute calls on an overloaded free tier. We fall back to the
        # next model ourselves instead.
        http_options=types.HttpOptions(timeout=int(GEMINI_TIMEOUT_S * 1000),  # milliseconds
                                       retry_options=types.HttpRetryOptions(attempts=1)),
    )
    def config(m: str):
        level = GEMINI_THINKING.get(m)
        return types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_json_schema=schema,
            max_output_tokens=max_tokens,
            thinking_config=types.ThinkingConfig(thinking_level=level) if level else None,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )

    models = [model] + [m for m in GEMINI_FALLBACKS if m != model]
    for i, m in enumerate(models):
        try:
            response = client.models.generate_content(model=m, contents=prompt, config=config(m))
            break
        except errors.APIError as e:
            if e.code in GEMINI_RETRY_CODES and i < len(models) - 1:
                log.info("gemini: %s returned %s, trying %s", m, e.code, models[i + 1])
                continue
            raise
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


# ---------- Groq (official SDK) ----------

def _groq(model: str, system: str, prompt: str, schema: dict, max_tokens: int) -> str:
    key = settings.GROQ_API_KEY or (settings.LLM_API_KEY if settings.LLM_PROVIDER == "groq" else "")
    if not key:
        raise LLMUnavailable("GROQ_API_KEY is empty")
    from groq import Groq

    client = Groq(api_key=key, timeout=GROQ_TIMEOUT_S, max_retries=0)  # we fall back ourselves
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        # Strict mode: constrained decoding, guaranteed to match the schema.
        response_format={"type": "json_schema",
                         "json_schema": {"name": "result", "strict": True, "schema": schema}},
        max_completion_tokens=max_tokens,
        reasoning_effort="low",  # gpt-oss is a reasoning model; low keeps it fast
    )
    choice = response.choices[0]
    if choice.finish_reason == "length":
        raise LLMUnavailable("Groq output truncated")
    if not choice.message.content:
        raise LLMUnavailable(f"Groq returned no text ({choice.finish_reason})")
    return choice.message.content
