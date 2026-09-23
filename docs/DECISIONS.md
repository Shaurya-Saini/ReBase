# Decisions log (append-only, both people)

One line per decision. Never edit old lines — add a new line that supersedes. Pull before appending.

| # | When | Who | Decision | Why |
|---|---|---|---|---|
| 1 | M0 | A+B | Stack: Flutter app + FastAPI/SQLite backend; all machine data simulated | Hackathon, 1–3 days |
| 2 | M0 | A+B | Sarvam + LLM called only from backend | Keep API keys off the tablet |
| 3 | M0 | A+B | Manual Q&A uses BM25, not a vector DB | Less setup, good enough for short manuals |
| 4 | M0 | A+B | Alert text localized in app by alert type | Backend stays English-only; B owns all strings |
| 5 | M0 | A+B | Re-split: A = AI + UI (all screens except Training Hub, all AI/voice), B = Infra (backend, DB, simulator, Flutter data layer, Training Hub end to end). Contract v1.1 | Play to each person's strengths |
