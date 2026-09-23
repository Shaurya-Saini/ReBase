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
    assert call["model"] == "gemini-3.8-flash" and call["contents"] == "prompt"
    assert call["config"].system_instruction == "sys"
    assert call["config"].response_mime_type == "application/json"
    assert call["config"].response_json_schema == SCHEMA
    assert st["api_key"] == "test-key" and st["timeout_ms"] == 15000


def test_gemini_model_override(gemini, monkeypatch):
    st = gemini('{"a": "x"}')
    monkeypatch.setattr(llm.settings, "LLM_MODEL", "gemini-3.5-flash-lite")
    llm.complete_json("s", "p", SCHEMA)
    assert st["models"].calls[0]["model"] == "gemini-3.5-flash-lite"


@pytest.mark.parametrize("behaviour", [RuntimeError("429 quota"), "", "not json"])
def test_gemini_failures_become_unavailable(gemini, behaviour):
    gemini(behaviour)
    with pytest.raises(llm.LLMUnavailable):
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
