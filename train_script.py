#!/usr/bin/env python3
"""train_script.py – train or retrain the lung‑cancer model (emoji debug)

Quick start
===========
$ python train_script.py               # uses data/master.csv
$ python train_script.py data/new.csv  # merges then retrains
$ python train_script.py -v            # verbose

Outputs
-------
trained_models/lung_<timestamp>.pkl   – model consumed by Flask app
runs/<timestamp>/report.html          – standalone HTML notebook report
runs/<timestamp>/metrics.json         – basic scores & metadata

The Jupyter notebook has been renamed **train_model.ipynb** and now lives in
`train_model/`.  This script executes that notebook after training and
converts it to HTML.
"""
import argparse, datetime, json, pathlib, shutil, time, warnings
from typing import List


warnings.filterwarnings("ignore", category=FutureWarning)

# ── Imports (heavy) ─────────────────────────────────────────────────────────
print("🐍  Loading libraries …", flush=True)
import joblib
import pandas as pd
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.over_sampling import ADASYN
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# ── Paths & constants ───────────────────────────────────────────────────────
BASE_DIR       = pathlib.Path(__file__).resolve().parent
DATA_DIR       = BASE_DIR / "data"
MASTER_CSV     = DATA_DIR / "master.csv"
RUNS_DIR       = BASE_DIR / "runs"
TRAINED_DIR    = BASE_DIR / "trained_models"
NOTEBOOK_DIR   = BASE_DIR / "train_model"
NOTEBOOK_PATH  = NOTEBOOK_DIR / "train_model.ipynb"
RANDOM_STATE   = 42

for p in (DATA_DIR, RUNS_DIR, TRAINED_DIR, NOTEBOOK_DIR):
    p.mkdir(parents=True, exist_ok=True)

# ── CLI args ────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("csv", nargs="?", default=str(MASTER_CSV),
                    help="extra CSV to merge before retrain")
parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
args = parser.parse_args()
LOG  = (lambda *m: print(*m)) if args.verbose else (lambda *_: None)
info = lambda m: print(m, flush=True)

# ── Merge new data ──────────────────────────────────────────────────────────
new_csv = pathlib.Path(args.csv).resolve()
if new_csv != MASTER_CSV:
    info("📥  Merging new data into master.csv …")
    combined = (pd.concat(
                   [pd.read_csv(p) for p in [MASTER_CSV, new_csv] if p.exists()]
               ).drop_duplicates())
    combined.to_csv(MASTER_CSV, index=False)
    info(f"🗃️  Master now has {len(combined)} rows")

# ── Load dataset ────────────────────────────────────────────────────────────
info("📖  Loading master dataset …")
df = pd.read_csv(MASTER_CSV).drop_duplicates()
info(f"✅  Loaded {len(df)} rows × {df.shape[1]} cols")

# ── Clean & encode ─────────────────────────────────────────────────────────
info("🧹  Cleaning data …")
from sklearn import preprocessing
le = preprocessing.LabelEncoder()

binary_cols: List[str] = [
    "SMOKING", "YELLOW_FINGERS", "ANXIETY", "PEER_PRESSURE",
    "CHRONIC DISEASE", "FATIGUE ", "ALLERGY ", "WHEEZING",
    "ALCOHOL CONSUMING", "COUGHING", "SHORTNESS OF BREATH",
    "SWALLOWING DIFFICULTY", "CHEST PAIN",
]

# ---- FIXED MAPPING --------------------------------------------------------
def bin_map(x):
    """Map YES variants to 1, NO variants to 0.

    • In raw CSV: YES = 2, NO = 1
    • If the value is a string, look at the first letter.
    """
    if isinstance(x, str):
        return 1 if x.upper().startswith("Y") else 0
    return 1 if x == 2 else 0          # ← ONLY 2 becomes 1
# --------------------------------------------------------------------------

for col in binary_cols:
    if col in df.columns:
        df[col] = df[col].apply(bin_map)

df.rename(columns={"FATIGUE ": "FATIGUE", "ALLERGY ": "ALLERGY"}, inplace=True)
if df["GENDER"].dtype == object:
    df["GENDER"] = le.fit_transform(df["GENDER"])
if df["LUNG_CANCER"].dtype == object:
    df["LUNG_CANCER"] = le.fit_transform(df["LUNG_CANCER"])

# ── Feature engineering ────────────────────────────────────────────────────
DROP = [c for c in ["GENDER", "AGE", "SMOKING", "SHORTNESS OF BREATH"] if c in df.columns]
if DROP:
    df.drop(columns=DROP, inplace=True)

df["ANXYELFIN"] = df["ANXIETY"] * df["YELLOW_FINGERS"]
X, y = df.drop("LUNG_CANCER", axis=1), df["LUNG_CANCER"]
info(f"🧾  Feature matrix → {X.shape[1]} columns")

# ── Pipeline & training ────────────────────────────────────────────────────
info("🚀  Training model …")
train_X, test_X, train_y, test_y = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=RANDOM_STATE)

pre = ColumnTransformer([("pass", "passthrough", X.columns)])
pipe = ImbPipeline([
    ("pre", pre),
    ("adasyn", ADASYN(random_state=RANDOM_STATE)),
    ("clf", GradientBoostingClassifier(random_state=RANDOM_STATE)),
])
pipe.fit(train_X, train_y)
info("🎯  Model trained!")

probs   = pipe.predict_proba(test_X)[:, 1]
auc     = roc_auc_score(test_y, probs)
report  = classification_report(
    test_y, (probs >= 0.5).astype(int), zero_division=0
)
info(f"📈  Hold‑out AUROC = {auc:.3f}")
LOG(report)

# ── Save artifacts ─────────────────────────────────────────────────────────
run_id   = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
run_dir  = RUNS_DIR / run_id
run_dir.mkdir(parents=True)
model_path = TRAINED_DIR / f"lung_{run_id}.pkl"
joblib.dump(pipe, model_path)
json.dump(
    {"auc": auc, "rows": len(df), "created": run_id},
    (run_dir / "metrics.json").open("w")
)
info(f"💾  Model → {model_path.relative_to(BASE_DIR)}")

# ── Execute notebook & export HTML ─────────────────────────────────────────
try:
    import papermill as pm, nbformat, nbconvert
    info("📝  Executing train_model/train_model.ipynb …")
    executed = run_dir / "executed.ipynb"
    pm.execute_notebook(
        str(NOTEBOOK_PATH), str(executed),
        kernel_name="python3", log_output=args.verbose
    )
    info("🌐  Converting to HTML …")
    nb = nbformat.read(executed, as_version=4)
    html = nbconvert.HTMLExporter(exclude_input=True)\
          .from_notebook_node(nb)[0]
    (run_dir / "report.html").write_text(html, encoding="utf-8")
    info("✅  HTML report saved!")
except Exception as e:
    info(f"⚠️  Notebook step skipped: {e.__class__.__name__}: {e}")

info("🎉  Training run complete: " + run_id)
