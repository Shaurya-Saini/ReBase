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
| 14 | M0 | B (pending A OK) | **Whole Flutter app → Person A** (project setup, pubspec, `main.dart`, `core/` data layer + mock/HTTP/WS clients, mock fixtures, Training Hub screens). B = whole backend only. Contract v2.1 (ownership only, no API change). Moved tasks: B0 (Flutter half), B4, B5, B14 → A | B has no Flutter toolchain; clean split by toolchain avoids cross-editing |
| 15 | M0 | A | Edge telemetry safety model: new top-level `ml/` pipeline (A-owned) — generator mirrors the sim + rule thresholds → Keras MLP → quantized **TFLite**. App loads `assets/models/safety.tflite` via `tflite_flutter`; falls back to the rule engine if absent. Operator CV stays hardcoded (ML Kit) | Real trained on-device model for the demo, with graceful fallback |
| 15 | M3 | B | New Python dep `anthropic` (official SDK) for the LLM in briefing (E15) / assistant (E23); default model `claude-opus-5` (override `LLM_MODEL`). LLM is **optional**: no key / other provider / any error → template fallback, so the demo never depends on it | Official SDK is the supported path; fallback keeps the demo offline-safe |
| 16 | M3 | B | **Default LLM = Google Gemini free tier** (`google-genai` SDK, `gemini-3.8-flash`, `LLM_PROVIDER=gemini`); Anthropic stays as an option. Supersedes the default in #15. Speech stays on-device (STT `speech_to_text`, TTS `flutter_tts`, A); Sarvam TTS optional (B12) | No paid keys: Gemini free tier handles Tamil/Hindi; on-device speech is free |
| 17 | M4 | B | RAG embeddings stay **English** (`all-MiniLM-L6-v2`, as configured). Hindi/Tamil questions are translated to English (Gemini) before retrieval in B11; answers are generated/translated back into the operator's language | Keep the embedding model small + standard; translation happens once at the LLM step |
| 18 | M4 | B | Gemini defaults tuned from live measurement (2026-09-24): primary `gemini-3.5-flash-lite` (~1–4 s, good ta/hi), fallback `gemini-3.8-flash` (often 503 on free tier), SDK retries off (they caused ~2 min calls), 10 s per attempt. Supersedes the model in #16 | Demo latency + reliability on the free tier |
| 19 | M4 | B | **Groq as automatic LLM fallback** (`groq` SDK, `openai/gpt-oss-120b`, strict JSON schema, `reasoning_effort=low`, no SDK retries): chain = primary provider → Groq when `GROQ_API_KEY` is set → non-LLM fallback. Live: good ta/hi answers, ~0.6–0.9 s per call | Gemini free tier was often overloaded (503) |
