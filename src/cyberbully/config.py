"""Path proyek, nama model, dan konstanta yang dipakai lintas modul."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
DATA_EVAL = DATA_DIR / "eval"
DATA_SYNTHETIC = DATA_DIR / "synthetic"

MODELS_DIR = ROOT / "models"
OUT_DIR = ROOT / "out"

SEED = 42

BASE_MODEL = "indobenchmark/indobert-base-p1"
ALT_MODEL = "indolem/indobertweet-base-uncased"

TEXT_COLUMN = "text"
LABEL_COLUMN = "label"
LABEL_NAMES = {0: "non-bully", 1: "bully"}

# Urutan: train, validation, test. Threshold dan hyperparameter diambil dari validation.
SPLIT_RATIOS = (0.8, 0.1, 0.1)

MAX_LENGTH = 128
