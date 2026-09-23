"""LLM provider wiring (Gemini). A fake genai.Client — no network, no key needed."""

import types as pytypes

import pytest

from app.ai import llm

SCHEMA = {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"],
          "additionalProperties": False}


class FakeModels:
    def __init__(self, behaviour):
        self.behaviour = behaviour
        self.calls = []

    def generate_content(self, *, model, contents, config):
        self.calls.append({"model": model, "contents": contents, "config": config})
        if isinstance(self.behaviour, Exception):
            raise self.behaviour
        return pytypes.SimpleNamespace(text=self.behaviour, candidates=[])


@pytest.fixture
def gemini(monkeypatch):
    """Install a fake google.genai.Client; returns a setter for its behaviour."""
    from google import genai

    state = {}

    def make(behaviour):
        models = FakeModels(behaviour)

        class FakeClient:
            def __init__(self, api_key, http_options):
                state["api_key"], state["timeout_ms"] = api_key, http_options.timeout
                state["attempts"] = http_options.retry_options.attempts
                self.models = models

        monkeypatch.setattr(genai, "Client", FakeClient)
        state["models"] = models
        return state

    monkeypatch.setattr(llm.settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(llm.settings, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm.settings, "LLM_MODEL", "")
    return make


def test_gemini_success(gemini):
    st = gemini('{"a": "வணக்கம்"}')
    assert llm.complete_json("sys", "prompt", SCHEMA) == {"a": "வணக்கம்"}
    call = st["models"].calls[0]
    assert call["model"] == "gemini-3.5-flash-lite" and call["contents"] == "prompt"
    assert call["config"].system_instruction == "sys"
    assert call["config"].response_mime_type == "application/json"
    assert call["config"].response_json_schema == SCHEMA
    assert st["api_key"] == "test-key" and st["timeout_ms"] == 10000
    assert st["attempts"] == 1  # no hidden SDK retries (they caused ~2 min calls)


def test_gemini_model_override(gemini, monkeypatch):
    st = gemini('{"a": "x"}')
    monkeypatch.setattr(llm.settings, "LLM_MODEL", "gemini-3.8-flash")
    llm.complete_json("s", "p", SCHEMA)
    assert st["models"].calls[0]["model"] == "gemini-3.8-flash"


@pytest.mark.parametrize("behaviour", [RuntimeError("429 quota"), "", "not json"])
def test_gemini_failures_become_unavailable(gemini, behaviour):
    gemini(behaviour)
    with pytest.raises(llm.LLMUnavailable):
        llm.complete_json("s", "p", SCHEMA)


def _api_error(code):
    from google.genai import errors

    return errors.ServerError(code, {"error": {"code": code, "message": "busy", "status": "UNAVAILABLE"}})


def test_gemini_falls_back_to_next_model_when_overloaded(gemini):
    st = gemini(None)
    outcomes = iter([_api_error(503), '{"a": "ok"}'])

    def generate(*, model, contents, config):
        st["models"].calls.append(model)
        nxt = next(outcomes)
        if isinstance(nxt, Exception):
            raise nxt
        return pytypes.SimpleNamespace(text=nxt, candidates=[])

    st["models"].generate_content = generate
    assert llm.complete_json("s", "p", SCHEMA) == {"a": "ok"}
    assert st["models"].calls == ["gemini-3.5-flash-lite", "gemini-3.8-flash"]


def test_gemini_thinking_level_per_model(gemini, monkeypatch):
    st = gemini('{"a": "x"}')
    llm.complete_json("s", "p", SCHEMA, fast=True)
    assert st["models"].calls[-1]["config"].thinking_config is None  # flash-lite: default minimal
    monkeypatch.setattr(llm.settings, "LLM_MODEL", "gemini-3.8-flash")
    llm.complete_json("s", "p", SCHEMA)
    assert st["models"].calls[-1]["config"].thinking_config.thinking_level.value.lower() == "low"


def test_gemini_all_overloaded_becomes_unavailable(gemini):
    gemini(_api_error(503))
    with pytest.raises(llm.LLMUnavailable, match="503"):
        llm.complete_json("s", "p", SCHEMA)


def test_gemini_without_key(monkeypatch):
    monkeypatch.setattr(llm.settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(llm.settings, "LLM_API_KEY", "")
    with pytest.raises(llm.LLMUnavailable, match="LLM_API_KEY"):
        llm.complete_json("s", "p", SCHEMA)


def test_briefing_uses_gemini_end_to_end(client, gemini):
    from app.ai import briefing

    briefing._cache.clear()
    gemini('{"machine_summary": "20 டன் அகழ்வாராய்ச்சி", "job_summary": "J", '
           '"hazards": ["மேல்நிலை மின் கம்பி"], "reminders": ["R"]}')
    sid = client.post("/sessions", json={"operator_id": "op_001", "machine_id": "mc_001",
                                         "job_id": "job_001"}).json()["id"]
    for sec in client.get(f"/sessions/{sid}/checklist").json()["sections"]:
        for i in sec["items"]:
            client.put(f"/sessions/{sid}/checklist/items/{i['id']}", json={"status": "ok"})
    client.post(f"/sessions/{sid}/checklist/complete")
    b = client.get(f"/sessions/{sid}/briefing", params={"lang": "ta-IN"}).json()
    assert b["machine_summary"] == "20 டன் அகழ்வாராய்ச்சி" and b["hazards"] == ["மேல்நிலை மின் கம்பி"]
    briefing._cache.clear()


# ---------- Groq (fallback + primary) ----------

@pytest.fixture
def groq(monkeypatch):
    """Fake groq.Groq; returns a setter for its behaviour + the recorded calls."""
    import groq as groq_mod

    state = {"calls": []}

    def make(behaviour, finish="stop"):
        class FakeCompletions:
            def create(self, **kw):
                state["calls"].append(kw)
                if isinstance(behaviour, Exception):
                    raise behaviour
                msg = pytypes.SimpleNamespace(content=behaviour)
                return pytypes.SimpleNamespace(choices=[pytypes.SimpleNamespace(message=msg, finish_reason=finish)])

        class FakeGroq:
            def __init__(self, api_key, timeout, max_retries):
                state.update(api_key=api_key, timeout=timeout, max_retries=max_retries)
                self.chat = pytypes.SimpleNamespace(completions=FakeCompletions())

        monkeypatch.setattr(groq_mod, "Groq", FakeGroq)
        return state

    monkeypatch.setattr(llm.settings, "GROQ_API_KEY", "gsk-test")
    monkeypatch.setattr(llm.settings, "GROQ_MODEL", "")
    monkeypatch.setattr(llm.settings, "LLM_MODEL", "")
    return make


def test_groq_is_the_fallback_when_gemini_fails(gemini, groq):
    gemini(_api_error(503))  # both Gemini models overloaded
    st = groq('{"a": "from groq"}')
    assert llm.complete_json("sys", "p", SCHEMA) == {"a": "from groq"}
    call = st["calls"][0]
    assert call["model"] == "openai/gpt-oss-120b" and call["reasoning_effort"] == "low"
    assert call["messages"][0] == {"role": "system", "content": "sys"}
    assert call["response_format"]["json_schema"]["strict"] is True
    assert call["response_format"]["json_schema"]["schema"] == SCHEMA
    assert st["max_retries"] == 0 and st["api_key"] == "gsk-test"


def test_groq_fast_model_and_not_used_when_gemini_works(gemini, groq):
    gemini('{"a": "from gemini"}')
    st = groq('{"a": "from groq"}')
    assert llm.complete_json("s", "p", SCHEMA) == {"a": "from gemini"} and st["calls"] == []


def test_groq_fast_model(gemini, groq):
    gemini(_api_error(503))
    st = groq('{"a": "x"}')
    llm.complete_json("s", "p", SCHEMA, fast=True)
    assert st["calls"][0]["model"] == "openai/gpt-oss-20b"


def test_no_groq_key_means_no_fallback(gemini, groq, monkeypatch):
    gemini(_api_error(503))
    st = groq('{"a": "x"}')
    monkeypatch.setattr(llm.settings, "GROQ_API_KEY", "")
    with pytest.raises(llm.LLMUnavailable, match="503"):
        llm.complete_json("s", "p", SCHEMA)
    assert st["calls"] == []


@pytest.mark.parametrize("behaviour,finish", [(RuntimeError("down"), "stop"), ("", "stop"), ('{"a"', "length")])
def test_both_fail_becomes_unavailable(gemini, groq, behaviour, finish):
    gemini(_api_error(503))
    groq(behaviour, finish)
    with pytest.raises(llm.LLMUnavailable) as e:
        llm.complete_json("s", "p", SCHEMA)
    assert "gemini" in str(e.value) and "groq" in str(e.value)


def test_groq_as_primary(groq, monkeypatch):
    monkeypatch.setattr(llm.settings, "LLM_PROVIDER", "groq")
    st = groq('{"a": "x"}')
    assert llm._providers() == ["groq"]
    assert llm.complete_json("s", "p", SCHEMA) == {"a": "x"} and len(st["calls"]) == 1
