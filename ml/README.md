# ml/ — edge telemetry safety-risk model

Trains a small classifier that maps a telemetry tick → safety class
(`normal`, `seatbelt_off`, `proximity`, `excessive_idle`, `overheat`, `overload`,
`unsafe_operation`) and exports a **quantized TFLite** model the Flutter app runs
on-device. The dataset mirrors the backend simulator's distributions and the
on-device rule thresholds (`app/lib/edge/telemetry_rules.dart`).

> Operator computer-vision (drowsiness/distraction) is **not** trained here — it
> stays hardcoded (ML Kit) in the app.

## Run

```bash
cd ml
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python gen_data.py     # -> data/telemetry.csv
python train.py        # -> artifacts/safety.tflite  AND  ../app/assets/models/safety.tflite
```

`train.py` copies the model straight into `app/assets/models/safety.tflite`, so
the next `flutter run` bundles it. Nothing else to wire — the app auto-detects it
(see `app/lib/edge/edge_model.dart`) and uses it instead of the rule engine;
if the file is absent it silently falls back to the rules.

## Contract with the app (keep in sync)

- **Feature order** (`FEATURES` in `train.py` == `_features()` in `edge_model.dart`):
  `engine_rpm, hydraulic_temp_c, fuel_pct, load_pct, speed_kmh, idle_seconds, seatbelt, proximity_m`
- **Normalization** (`SCALE` == `_scale`): `[3000, 150, 100, 150, 40, 600, 1, 30]`
- **Labels/order** (`LABELS` == `_labels`): as listed above.

If you change features, scales, or labels, update **both** files.
