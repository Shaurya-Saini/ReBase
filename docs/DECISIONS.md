# Decisions log (append-only, both people)

One line per decision. Never edit old lines — add a new line that supersedes. Pull before appending.

| # | When | Who | Decision | Why |
|---|---|---|---|---|
| 1 | M0 | A+B | Stack: Flutter app + FastAPI/SQLite backend; all machine data simulated | Hackathon, 1–3 days |
| 2 | M0 | A+B | Sarvam + LLM called only from backend | Keep API keys off the tablet |
| 3 | M0 | A+B | Manual Q&A uses BM25, not a vector DB | Less setup, good enough for short manuals |
| 4 | M0 | A+B | Alert text localized in app by alert type | Backend stays English-only; B owns all strings |
| 5 | M0 | A+B | Re-split: A = AI + UI (all screens except Training Hub, all AI/voice), B = Infra (backend, DB, simulator, Flutter data layer, Training Hub end to end). Contract v1.1 | Play to each person's strengths |
| 6 | M0 | A+B | **v2.0 edge re-architecture.** Safety detection moves to the tablet (A); backend simulates sensors and stores app-posted alerts | Match the product's edge vision; make the demo's "edge AI" real |
| 7 | M0 | A+B | Operator-state alerts = **real on-device computer vision** (Google ML Kit face detection, pretrained — no training/quantization). Machine-sensor alerts = on-device threshold rules over streamed telemetry | ML Kit is free, on-device, and genuinely demoable on the tablet camera |
| 8 | M0 | A+B | Checklists + manual Q&A + briefing served from the **backend RAG (ChromaDB + sentence-transformers) + LLM**. Checklists are structured content; the vector store is for Q&A. **Supersedes #3** (BM25) | Simplify for the demo; keep the RAG story on the server |
| 9 | M0 | A+B | Task-time estimation = **XGBoost on the backend** (was scikit-learn/A). A owns no backend code now | Matches "fleet-wide prediction on cloud"; frees A for edge + UI |
| 10 | M0 | A+B | **STT is on-device** (`speech_to_text`); removed `/voice/stt`. Sarvam = **TTS + translate only**, backend proxy for the demo; prefer on-device `flutter_tts` where quality allows | On-device STT is free/offline; keep Sarvam optional |
| 11 | M0 | A+B | Translation: static UI = precompiled **ARB** (A); dynamic AI text = **LLM answers directly in target language** (B); Sarvam translate is fallback only | Zero-cost multilingual UI; minimal Sarvam dependence |
| 12 | M0 | A+B | **No offline mode / no local SQLite cache** in the demo. It's a proof of application; offline+sync described as real-product only | Cut scope that the demo can't meaningfully show |
| 13 | M0 | A+B | Demo languages = **en-IN, hi-IN, ta-IN** (te-IN stretch). Training Hub "heavy video synthesis" **deferred** to project end | Focus the demo |
