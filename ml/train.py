"""Train a small MLP on the generated telemetry and export a quantized TFLite
model for the Flutter app.

Run (after gen_data.py):  python train.py
Outputs:
  artifacts/safety.tflite, artifacts/labels.txt
  ../app/assets/models/safety.tflite   (copied so the app bundles it)
"""
import os

import numpy as np
import pandas as pd
import tensorflow as tf

LABELS = [
    "normal",
    "seatbelt_off",
    "proximity",
    "excessive_idle",
    "overheat",
    "overload",
    "unsafe_operation",
]

FEATURES = [
    "engine_rpm",
    "hydraulic_temp_c",
    "fuel_pct",
    "load_pct",
    "speed_kmh",
    "idle_seconds",
    "seatbelt",
    "proximity_m",
]

# Fixed normalization scales — MUST match app/lib/edge/edge_model.dart (_scale).
SCALE = np.array([3000, 150, 100, 150, 40, 600, 1, 30], dtype=np.float32)


def main() -> None:
    df = pd.read_csv("data/telemetry.csv")
    x = df[FEATURES].values.astype("float32") / SCALE
    y = df["label"].values.astype("int32")

    idx = np.random.RandomState(0).permutation(len(x))
    x, y = x[idx], y[idx]
    split = int(0.85 * len(x))
    x_tr, x_te = x[:split], x[split:]
    y_tr, y_te = y[:split], y[split:]

    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(len(FEATURES),)),
            tf.keras.layers.Dense(32, activation="relu"),
            tf.keras.layers.Dense(16, activation="relu"),
            tf.keras.layers.Dense(len(LABELS), activation="softmax"),
        ]
    )
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.fit(x_tr, y_tr, epochs=25, batch_size=64, validation_split=0.1, verbose=2)
    _, acc = model.evaluate(x_te, y_te, verbose=0)
    print(f"test accuracy: {acc:.3f}")

    # Quantized TFLite (float in/out interface, int8 weights) via a
    # representative dataset.
    def representative():
        for i in range(min(200, len(x_tr))):
            yield [x_tr[i : i + 1]]

    conv = tf.lite.TFLiteConverter.from_keras_model(model)
    conv.optimizations = [tf.lite.Optimize.DEFAULT]
    conv.representative_dataset = representative
    tfl = conv.convert()

    os.makedirs("artifacts", exist_ok=True)
    with open("artifacts/safety.tflite", "wb") as f:
        f.write(tfl)
    with open("artifacts/labels.txt", "w") as f:
        f.write("\n".join(LABELS))

    dst = os.path.join("..", "app", "assets", "models")
    os.makedirs(dst, exist_ok=True)
    with open(os.path.join(dst, "safety.tflite"), "wb") as f:
        f.write(tfl)

    print(f"wrote artifacts/safety.tflite ({len(tfl)} bytes) and copied to app assets")


if __name__ == "__main__":
    main()
