"""B11: manual Q&A (E23) — translate → retrieve → answer, with every fallback.

Real vector store (English embeddings); the LLM is a scripted fake, so no network.
"""

import pytest

from app.ai import assistant, rag

Q_EN = "How do I switch to power mode?"
Q_TA = "பவர் மோடுக்கு எப்படி மாற்றுவது?"


@pytest.fixture(scope="module", autouse=True)
def store():
    rag._collection = None
    rag.build()


class FakeLLM:
    """Answers the translate call and the answer call like the real schemas."""

    def __init__(self, english=Q_EN, answer="ANSWER", answerable=True, used=("4.2 Operating modes",),
                 fail=False):
        self.english, self.answer, self.answerable, self.used, self.fail = english, answer, answerable, used, fail
        self.calls = []

    def __call__(self, system, prompt, schema, max_tokens=2000, fast=False):
        self.calls.append({"system": system, "prompt": prompt, "schema": schema})
        if self.fail:
            raise assistant.LLMUnavailable("no key")
        if "english" in schema["properties"]:
            return {"english": self.english}
        return {"answerable": self.answerable, "answer": self.answer, "used_sections": list(self.used)}


@pytest.fixture
def llm(monkeypatch):
    def install(**kw):
        fake = FakeLLM(**kw)
        monkeypatch.setattr(assistant, "complete_json", fake)
        return fake
    return install


def ask(client, question, lang="en-IN", machine_id="mc_001", **extra):
    return client.post("/assistant/ask", json={"machine_id": machine_id, "question": question,
                                               "lang": lang, **extra})


def test_english_answer_with_sources(client, llm):
    fake = llm(answer="Put both joysticks in neutral and press M until P shows.")
    r = ask(client, Q_EN)
    assert r.status_code == 200
    assert r.json() == {"answer": "Put both joysticks in neutral and press M until P shows.", "lang": "en-IN",
                        "sources": [{"doc": "excavator_manual.md", "section": "4.2 Operating modes"}]}
    assert len(fake.calls) == 1  # English: no translation call
    assert "[4.2 Operating modes]" in fake.calls[0]["prompt"] and "mode button (M)" in fake.calls[0]["prompt"]


def test_tamil_question_is_translated_then_answered_in_tamil(client, llm):
    fake = llm(english="How do I switch to power mode?", answer="இரண்டு ஜாய்ஸ்டிக்குகளையும் நடுநிலையில் வைக்கவும்.")
    r = ask(client, Q_TA, lang="ta-IN").json()
    assert r["lang"] == "ta-IN" and r["answer"].startswith("இரண்டு")
    assert r["sources"] == [{"doc": "excavator_manual.md", "section": "4.2 Operating modes"}]
    translate, answer = fake.calls
    assert "english" in translate["schema"]["properties"] and Q_TA in translate["prompt"]
    assert "Tamil" in answer["prompt"] and Q_TA in answer["prompt"]


def test_machine_manual_is_used(client, llm):
    fake = llm(english="How do I tip the load?", used=("4.3 Tipping the load",))
    r = ask(client, "How do I tip the load?", machine_id="mc_004").json()
    assert r["sources"] == [{"doc": "dump_truck_manual.md", "section": "4.3 Tipping the load"}]
    assert "dump_truck_manual.md" in fake.calls[0]["prompt"]


def test_hallucinated_section_titles_are_dropped(client, llm):
    llm(used=("9.9 Made up", "4.2 Operating modes"))
    assert ask(client, Q_EN).json()["sources"] == [{"doc": "excavator_manual.md", "section": "4.2 Operating modes"}]
    llm(used=("9.9 Made up",))  # nothing valid → best retrieved section
    assert ask(client, Q_EN).json()["sources"][0]["section"] == "4.2 Operating modes"


def test_llm_says_not_answerable(client, llm):
    llm(answerable=False, answer="The manual does not cover that.")
    r = ask(client, "How do I switch to power mode on the radio?").json()
    assert r["sources"] == [] and r["answer"] == "The manual does not cover that."


def test_off_topic_never_reaches_the_llm(client, llm):
    fake = llm()
    r = ask(client, "What is the cricket score today?").json()
    assert r["sources"] == [] and "couldn't find that in the excavator manual" in r["answer"]
    assert fake.calls == []


def test_off_topic_localized(client, llm):
    llm(english="What is the weather tomorrow?")
    r = ask(client, "நாளை வானிலை எப்படி இருக்கும்?", lang="ta-IN").json()
    assert r["lang"] == "ta-IN" and "கையேட்டில்" in r["answer"] and r["sources"] == []


def test_no_llm_reads_the_manual_in_english(client, llm):
    llm(fail=True)
    r = ask(client, Q_EN, lang="hi-IN").json()  # English words, Hindi UI, LLM down
    assert r["lang"] == "en-IN"
    assert r["answer"].startswith("From the excavator manual, 4.2 Operating modes:")
    assert r["sources"] == [{"doc": "excavator_manual.md", "section": "4.2 Operating modes"}]


def test_no_llm_tamil_question_cannot_be_matched(client, llm):
    """Without translation the English index can't match Tamil → honest 'not found'."""
    llm(fail=True)
    r = ask(client, Q_TA, lang="ta-IN").json()
    assert r["sources"] == [] and r["lang"] == "ta-IN"


def test_default_config_has_no_llm(client):
    """Tests run with LLM_PROVIDER=none → real code path falls back, never 500."""
    r = ask(client, Q_EN)
    assert r.status_code == 200 and r.json()["sources"][0]["section"] == "4.2 Operating modes"


def test_errors(client):
    r = ask(client, Q_EN, machine_id="mc_999")
    assert r.status_code == 404 and r.json()["error"]["code"] == "MACHINE_NOT_FOUND"
    r = ask(client, Q_EN, session_id="ses_999")
    assert r.status_code == 404 and r.json()["error"]["code"] == "SESSION_NOT_FOUND"
    r = ask(client, "   ")
    assert r.status_code == 422 and r.json()["error"]["code"] == "EMPTY_QUESTION"
    r = ask(client, Q_EN, lang="fr-FR")
    assert r.status_code == 422
