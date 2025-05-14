# testing_trained_model/test_model.py
"""
Quick smoke-tests for the lung-cancer model with diverse cases.

Run:
    (.venv) python testing_trained_model/test_model.py
"""

import glob, json, os, sys
from pathlib import Path

import joblib
import pandas as pd

# ───────────────── Locate newest pickle ────────────────────────────────────
TRAINED_DIR = Path(__file__).resolve().parents[1] / "trained_models"
try:
    MODEL_PATH = max(
        glob.glob(str(TRAINED_DIR / "lung_*.pkl")),
        key=os.path.getctime,
    )
except ValueError:
    sys.exit("❌  No trained_models/lung_*.pkl found – run train_script.py first!")

print(f"🔗  Loading model: {Path(MODEL_PATH).name}")
model = joblib.load(MODEL_PATH)

# ───────────────── Helper ──────────────────────────────────────────────────
COLS = [
    "YELLOW_FINGERS", "ANXIETY", "PEER_PRESSURE", "CHRONIC DISEASE", "FATIGUE",
    "ALLERGY", "WHEEZING", "ALCOHOL CONSUMING", "COUGHING",
    "SWALLOWING DIFFICULTY", "CHEST PAIN", "ANXYELFIN"
]

def make_row(**kwargs):
    row = {c: 0 for c in COLS}
    row.update(kwargs)
    # keep interaction term consistent
    row["ANXYELFIN"] = row["ANXIETY"] * row["YELLOW_FINGERS"]
    return row

# ───────────────── Twenty synthetic patients ───────────────────────────────
test_cases = [
    # 1. No symptoms
    ("NONE", make_row()),

    # 2–12. Exactly one symptom on
    ("ONLY_YELLOW",         make_row(**{"YELLOW_FINGERS": 1})),
    ("ONLY_ANXIETY",        make_row(**{"ANXIETY": 1})),
    ("ONLY_PEER_PRESSURE",  make_row(**{"PEER_PRESSURE": 1})),
    ("ONLY_CHRONIC",        make_row(**{"CHRONIC DISEASE": 1})),
    ("ONLY_FATIGUE",        make_row(**{"FATIGUE": 1})),
    ("ONLY_ALLERGY",        make_row(**{"ALLERGY": 1})),
    ("ONLY_WHEEZING",       make_row(**{"WHEEZING": 1})),
    ("ONLY_ALCOHOL",        make_row(**{"ALCOHOL CONSUMING": 1})),
    ("ONLY_COUGHING",       make_row(**{"COUGHING": 1})),
    ("ONLY_SWALLOW",        make_row(**{"SWALLOWING DIFFICULTY": 1})),
    ("ONLY_CHEST_PAIN",     make_row(**{"CHEST PAIN": 1})),

    # 13–17. Simple pairs
    ("YF_ANX",      make_row(**{"YELLOW_FINGERS": 1, "ANXIETY": 1})),
    ("COUGH_WHEEZE",make_row(**{"COUGHING": 1, "WHEEZING": 1})),
    ("ALLERGY_FAT", make_row(**{"ALLERGY": 1, "FATIGUE": 1})),
    ("ALC_PEER",    make_row(**{"ALCOHOL CONSUMING": 1, "PEER_PRESSURE": 1})),
    ("CHRON_CHEST", make_row(**{"CHRONIC DISEASE": 1, "CHEST PAIN": 1})),

    # 18. Triple combo
    ("TRIPLE_RISK", make_row(**{
        "YELLOW_FINGERS": 1,
        "ANXIETY": 1,
        "CHEST PAIN": 1
    })),

    # 19. All except interaction-only column
    ("WITHOUT_YF", make_row(**{
        c: 1 for c in COLS if c not in ["YELLOW_FINGERS", "ANXYELFIN"]
    })),

    # 20. Every symptom
    ("ALL", make_row(**{
        c: 1 for c in COLS if c != "ANXYELFIN"
    })),
]

# ───────────────── Evaluate & print ────────────────────────────────────────
print("\nID                 Probability   Risk")
print("―" * 50)
results = {}
for label, features in test_cases:
    df = pd.DataFrame([features])
    prob = model.predict_proba(df)[0, 1]
    if prob >= 0.5:
        risk = "HIGH"
    elif prob >= 0.2:
        risk = "MEDIUM"
    else:
        risk = "LOW"
    print(f"{label:<20} {prob:>7.1%}     {risk}")
    results[label] = prob

# save raw probabilities for later checks / CI
out_path = Path(__file__).with_suffix(".json")
out_path.write_text(json.dumps(results, indent=2))
print(f"\n📝  Probabilities also written to {out_path.name}")
