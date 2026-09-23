# backend/app/ai/CLAUDE.md — Person A (AI)

Read the root `CLAUDE.md` first. Person A owns: `backend/app/ai/`, `backend/data/checklists/`, `backend/data/manuals/`, `backend/data/models/`, `backend/tests/ai/`, `backend/requirements-ai.txt`. Everything else in `backend/` is B's — import it, never edit it.

## Layout

```
backend/app/ai/
├── router.py            APIRouter with E8, E15, E20, E21, E22        ← B mounts it
├── api.py               load_checklist(machine_type)                  ← B calls it
├── settings.py          A's own env settings (SARVAM_API_KEY, LLM_*) — don't touch B's config.py
├── llm.py               one complete(prompt) -> str, provider from env
├── sarvam.py            stt(), tts(), translate() — the only place Sarvam is called
├── rag.py               load manuals → split by heading → BM25 → top 3 sections
├── estimator.py         load trained model, predict hours + range + factors
├── train_estimator.py   `python -m app.ai.train_estimator` → data/models/estimator.joblib
├── briefing.py          machine + job + hazards → short briefing (LLM, with template fallback)
└── checklists.py        read data/checklists/<machine_type>.yaml
```

## Rules

- M0 duty: commit `router.py` and `api.py` as **stubs** returning `CONTRACT.md` §4 example data. B's `main.py` depends on them.
- Use B's `get_db()` and models from `app.db` / `app.models`. Need a new field? Request it in your progress file — don't add it.
- **Estimator:** train on `JobLog` (features: machine_type, planned_hours, weather, operator_experience → target actual_hours). Start with a simple model (e.g. gradient boosting or linear regression); report range from residuals. If the model file is missing, fall back to `planned_hours × factor` so the endpoint never fails.
- **Assistant flow:** translate question → English → BM25 → LLM answers in English using only retrieved sections, returns sources → translate to `lang`. If nothing relevant is found, say so instead of guessing.
- **Sarvam + LLM:** 15 s timeout; on failure return 503 `UPSTREAM_UNAVAILABLE`. Empty key → clear 503, never crash. Check docs.sarvam.ai for current model names and request formats before coding `sarvam.py` — don't guess.
- **Briefing** must work without the LLM (template fallback) so the demo survives an API outage.
- Run `pytest tests/ai -q` before every merge to `main`.
