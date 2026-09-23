# Demo script (finalize together at M5, rehearse twice)

Target length: 5–6 minutes. A drives the tablet (knows the UI), B triggers scenarios from Swagger (`/docs` → `POST /sim/scenario`).

| # | Story beat | Screen | Trigger | Super point shown |
|---|---|---|---|---|
| 1 | Operator Ravi logs in, picks Tamil | Login | — | Multilingual UI |
| 2 | Sees today's job, estimate, rest status OK | Dashboard, Job | — | Planning + fatigue |
| 3 | 30-min pre-shift recap on the excavator, answers quiz | Training Hub | — | Training Hub |
| 4 | Docks tablet → machine identified → checklist, marks hose leak (critical) → blocked | Pre-start | — | Co-pilot checklist |
| 5 | Fixes, re-checks, completes → briefing read aloud in Tamil | Briefing | — | Voice |
| 6 | Working: live gauges | Live | `normal` | Telemetry |
| 7 | Seatbelt off → alert → ack | Live | `seatbelt_off` | Safety |
| 8 | Drowsiness → critical alert with sound | Live | `drowsiness` | Safety |
| 9 | Asks by voice in Tamil "How do I switch to power mode?" → spoken answer + source | Assistant | — | Voice assistant |
| 10 | Ends session → summary | Summary | — | Logging |

Backup plan if Wi-Fi/APIs fail: run app with `USE_MOCK=true` (every screen still works).
