# Demo script (finalize together at M5, rehearse twice)

Target length: 5–6 minutes. A drives the tablet (knows the UI + edge), B triggers telemetry scenarios from Swagger (`/docs` → `POST /sim/scenario`). Camera alerts are triggered live by a face in front of the tablet.

| # | Story beat | Screen | Trigger | Super point shown |
|---|---|---|---|---|
| 1 | Operator Ravi logs in, picks Tamil (whole app switches) | Login | — | Multilingual UI |
| 2 | Sees today's job, XGBoost estimate, rest status OK | Dashboard, Job | — | Planning + fatigue |
| 3 | 30-min pre-shift recap on the excavator, answers quiz | Training Hub | — | Training Hub |
| 4 | Docks tablet → machine identified → checklist, marks hose leak (critical) → blocked | Pre-start | — | Co-pilot checklist |
| 5 | Fixes, re-checks, completes → briefing read aloud in Tamil | Briefing | — | Voice (TTS) |
| 6 | Working: live simulated gauges | Live | `normal` | Telemetry |
| 7 | Seatbelt off → **tablet rule** fires alert → ack | Live | `seatbelt_off` | On-device safety rules |
| 8 | **Operator looks away / eyes close → real camera CV** fires critical alert with sound | Live | **face at camera** | **Edge computer vision (headline)** |
| 9 | Asks by voice in Tamil "How do I switch to power mode?" → on-device STT → RAG answer + source, spoken back | Assistant | — | Voice assistant + RAG |
| 10 | Ends session → summary; alerts show in the incident log | Summary | — | Logging |

Notes:
- Beats 7 (rules) and 8 (camera CV) both run **on the tablet**; the alerts are POSTed to the backend for the incident log.
- Backup plan if Wi-Fi/APIs fail: run app with `USE_MOCK=true` (every screen works; camera CV still runs on-device).
