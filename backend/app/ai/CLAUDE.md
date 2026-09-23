# backend/app/ai/CLAUDE.md — Person B (Backend AI)

Read the root `CLAUDE.md` and `backend/CLAUDE.md` first. In v2.0 all backend AI is **Person B**. This folder holds the RAG assistant, the XGBoost estimator, the LLM briefing, and the Sarvam proxy. (The tablet's edge CV is Person A, in the Flutter app — not here.)

## Layout

```
backend/app/ai/
├── router_assistant.py   E23 /assistant/ask (RAG + LLM)                 ← mounted by main.py
├── router_voice.py       E24 /voice/tts, E25 /translate (Sarvam)        ← mounted by main.py
├── llm.py                one complete(prompt, lang) -> str, provider from env
├── sarvam.py             tts(), translate() — the only place Sarvam is called
├── rag.py                ChromaDB store: ingest manuals + checklists → embed → retrieve top-k
├── checklists.py         read data/checklists/<machine_type>.yaml → Checklist (served by E12)
├── estimator.py          load XGBoost model, predict hours + range + factors (E8)
├── train_estimator.py    `python -m app.ai.train_estimator` → data/models/estimator.json
└── briefing.py           machine + job + hazards → short briefing (LLM, template fallback)
```

## Rules

- **RAG (ChromaDB + sentence-transformers):** ingest the synthetic manuals in `data/manuals/` at startup (persist to `data/models/chroma/`). Checklists are **structured content** (`data/checklists/*.yaml`) — serve them directly via E12; they don't need vector retrieval. The vector store is for the **Q&A assistant**.
- **Assistant flow (E23):** retrieve top-k manual sections for the question → LLM answers **in `lang`** using only retrieved sections → return `sources`. If nothing relevant is found, say so instead of guessing. Prefer having the LLM answer directly in the target language over a separate translate call.
- **Estimator (XGBoost):** train on `JobLog` (features: machine_type, planned_hours, weather, operator_experience → target actual_hours). Report `range_hours` from residuals/quantiles and `factors` from feature effects. If the model file is missing, fall back to `planned_hours × factor` so E8 never fails.
- **Briefing (E15):** must work without the LLM (template fallback) so the demo survives an API outage.
- **Sarvam + LLM:** 15 s timeout; on failure return 503 `UPSTREAM_UNAVAILABLE`. Empty key → clear 503, never crash. Check docs.sarvam.ai for current model names and request formats before coding `sarvam.py` — don't guess.
- Use B's own `get_db()` / models from `app.db` / `app.models`.
- Run `pytest tests -q` before every merge to `main`.
