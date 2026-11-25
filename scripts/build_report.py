"""Bangun laporan DOCX dari sumber Markdown, grafik, dan data proyek.

Jalankan: python scripts/build_report.py
Butuh Pandoc. Script memakai Pandoc di PATH, lalu `.tools/pandoc`, lalu
mengunduh rilis resmi arm64 macOS bila belum ada.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor
from matplotlib.patches import FancyArrowPatch, Rectangle
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
FIGURES = DOCS / "figures"
SOURCE = DOCS / "laporan_pipeline.md"
OUTPUT = DOCS / "laporan_pipeline_cyberbullying.docx"
TOOLS = ROOT / ".tools"

INK = "#1a1a1a"
MID = "#6b6b6b"
LIGHT = "#b8b8b8"
PALE = "#e6e6e6"
GRID = "#ececec"
PAPER = "#ffffff"

BASELINE_VAL = {
    "threshold": 0.40,
    "accuracy": 0.865,
    "precision_bully": 0.860,
    "recall_bully": 0.903,
    "f1_bully": 0.881,
}


def _fmt_int(value: float) -> str:
    return f"{int(round(value)):,}".replace(",", ".")


def _fmt(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def _comma_tick(value: float, _position: int) -> str:
    return f"{value:.2f}".replace(".", ",")


def _setup_matplotlib() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
            "font.size": 7.6,
            "axes.titlesize": 8.2,
            "axes.labelsize": 7.6,
            "xtick.labelsize": 7.0,
            "ytick.labelsize": 7.0,
            "legend.fontsize": 6.8,
            "axes.edgecolor": "#333333",
            "axes.linewidth": 0.6,
            "axes.facecolor": PAPER,
            "figure.facecolor": PAPER,
            "text.color": INK,
            "axes.labelcolor": INK,
            "xtick.color": "#333333",
            "ytick.color": "#333333",
            "savefig.dpi": 300,
            "savefig.facecolor": PAPER,
        }
    )


def _save(fig: plt.Figure, name: str) -> Path:
    FIGURES.mkdir(parents=True, exist_ok=True)
    path = FIGURES / name
    fig.savefig(path, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    return path


def _clean_axes(ax: plt.Axes, *, grid_axis: str = "y") -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.55)
    ax.set_axisbelow(True)


def _read_project_data() -> dict[str, object]:
    required = [
        ROOT / "data/processed/train.csv",
        ROOT / "data/processed/val.csv",
        ROOT / "data/processed/test.csv",
        ROOT / "data/synthetic/synthetic_train.csv",
        ROOT / "out/model_a/val_metrics.json",
        ROOT / "out/model_a/test_metrics.json",
        ROOT / "out/model_b/val_metrics.json",
        ROOT / "out/model_b/test_metrics.json",
        ROOT / "out/model_a/implicit_metrics.json",
        ROOT / "out/model_b/implicit_metrics.json",
        ROOT / "out/model_b/val_predictions.csv",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Artefak berikut belum ada; jalankan pipeline dan evaluasi dulu:\n- "
            + "\n- ".join(missing)
        )

    train = pd.read_csv(ROOT / "data/processed/train.csv")
    val = pd.read_csv(ROOT / "data/processed/val.csv")
    test = pd.read_csv(ROOT / "data/processed/test.csv")
    synthetic = pd.read_csv(ROOT / "data/synthetic/synthetic_train.csv")

    return {
        "train": train,
        "val": val,
        "test": test,
        "synthetic": synthetic,
        "metrics": {
            "a_val": json.loads((ROOT / "out/model_a/val_metrics.json").read_text()),
            "a_test": json.loads((ROOT / "out/model_a/test_metrics.json").read_text()),
            "b_val": json.loads((ROOT / "out/model_b/val_metrics.json").read_text()),
            "b_test": json.loads((ROOT / "out/model_b/test_metrics.json").read_text()),
            "a_implicit": json.loads((ROOT / "out/model_a/implicit_metrics.json").read_text()),
            "b_implicit": json.loads((ROOT / "out/model_b/implicit_metrics.json").read_text()),
        },
        "b_val_predictions": pd.read_csv(ROOT / "out/model_b/val_predictions.csv"),
    }


def figure_pipeline() -> Path:
    fig, ax = plt.subplots(figsize=(6.6, 4.6))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    def box(
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        lines: tuple[str, ...] = (),
        *,
        dashed: bool = False,
        fill: str = PAPER,
        title_size: float = 7.4,
        line_size: float = 6.2,
    ) -> None:
        ax.add_patch(
            Rectangle(
                (x, y),
                w,
                h,
                facecolor=fill,
                edgecolor=INK,
                linewidth=0.7,
                linestyle=(0, (3, 2)) if dashed else "solid",
                zorder=2,
            )
        )
        ax.text(
            x + w / 2,
            y + h - 2.4,
            title,
            ha="center",
            va="center",
            fontsize=title_size,
            fontweight="bold",
            zorder=3,
        )
        for index, line in enumerate(lines):
            ax.text(
                x + w / 2,
                y + h - 4.7 - index * 2.05,
                line,
                ha="center",
                va="center",
                fontsize=line_size,
                color=MID,
                zorder=3,
            )

    def arrow(x1: float, y1: float, x2: float, y2: float) -> None:
        ax.add_patch(
            FancyArrowPatch(
                (x1, y1),
                (x2, y2),
                arrowstyle="-|>",
                mutation_scale=7,
                linewidth=0.7,
                color=INK,
                shrinkA=0,
                shrinkB=0,
                zorder=1,
            )
        )

    def elbow(points: list[tuple[float, float]]) -> None:
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        if len(points) > 2:
            ax.plot(xs[:-1], ys[:-1], color=INK, linewidth=0.7, zorder=1)
        arrow(xs[-2], ys[-2], xs[-1], ys[-1])

    for label, y in (("DATA", 90), ("MODEL", 66), ("EVALUASI", 38), ("DEPLOY", 11)):
        ax.text(
            2.0,
            y,
            label,
            ha="center",
            va="center",
            rotation=90,
            fontsize=5.6,
            fontweight="bold",
            color=MID,
        )

    # Band 1: data.
    box(6, 85, 23, 10, "Data mentah", ("13.169 tweet",))
    arrow(29, 90, 33.5, 90)
    box(34, 85, 27, 10, "Bersihkan + dedup", ("12.997 baris",))
    arrow(61, 90, 65.5, 90)
    box(66, 85, 28, 10, "Split 80/10/10", ("seed 42",))

    # Band 2: models.
    box(6, 60, 23, 14, "Baseline", ("TF-IDF + LogReg", "F1 val 0,881"))
    box(34, 60, 23, 14, "Model A", ("IndoBERT real-only", "F1 val 0,929"))
    ax.add_patch(
        Rectangle(
            (62, 56),
            32,
            25,
            facecolor="none",
            edgecolor=INK,
            linewidth=0.7,
            linestyle=(0, (3, 2)),
            zorder=2,
        )
    )
    ax.text(
        78,
        78.6,
        "20.000 sintetis · hanya train",
        ha="center",
        va="center",
        fontsize=6.0,
        color=MID,
        zorder=3,
    )
    box(63.5, 57.3, 29, 17.5, "Model B2", ("IndoBERT + sintetis", "F1 val 0,917"))

    ax.plot([80, 80], [85, 82], color=INK, linewidth=0.7, zorder=1)
    ax.plot([17.5, 80], [82, 82], color=INK, linewidth=0.7, zorder=1)
    arrow(17.5, 82, 17.5, 74)
    arrow(45.5, 82, 45.5, 74)
    ax.plot([78, 78], [82, 81], color=INK, linewidth=0.7, zorder=1)

    # Band 3: evaluation.
    box(6, 30, 27, 12, "Validation 1.300", ("pilih threshold",))
    box(37, 30, 27, 12, "Test 1.300", ("evaluasi akhir",))
    box(68, 30, 26, 12, "Eval set manual", ("40 final + 10 usulan",))

    ax.plot([17.5, 17.5], [60, 54], color=INK, linewidth=0.7, zorder=1)
    ax.plot([45.5, 45.5], [60, 54], color=INK, linewidth=0.7, zorder=1)
    ax.plot([78, 78], [56, 54], color=INK, linewidth=0.7, zorder=1)
    ax.plot([17.5, 78], [54, 54], color=INK, linewidth=0.7, zorder=1)
    ax.plot([50.5, 50.5], [54, 49], color=INK, linewidth=0.7, zorder=1)
    ax.plot([19.5, 81], [49, 49], color=INK, linewidth=0.7, zorder=1)
    arrow(19.5, 49, 19.5, 42)
    arrow(50.5, 49, 50.5, 42)
    arrow(81, 49, 81, 42)

    # Band 4: deploy.
    box(24, 6, 26, 10, "API FastAPI", ("/compare · /predict",))
    arrow(50, 11, 55.5, 11)
    box(56, 6, 26, 10, "Frontend React", ("dua panel A/B",))
    elbow([(50.5, 30), (50.5, 22), (37, 22), (37, 16)])

    fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.005)
    return _save(fig, "01_pipeline.png")


def figure_labels_split(data: dict[str, object]) -> Path:
    train = data["train"]
    val = data["val"]
    test = data["test"]

    train_counts = train["label"].value_counts().to_dict()
    val_counts = val["label"].value_counts().to_dict()
    test_counts = test["label"].value_counts().to_dict()
    total_bully = int(train_counts.get(1, 0) + val_counts.get(1, 0) + test_counts.get(1, 0))
    total_safe = int(train_counts.get(0, 0) + val_counts.get(0, 0) + test_counts.get(0, 0))
    fig, (left, right) = plt.subplots(
        1,
        2,
        figsize=(6.5, 2.55),
        gridspec_kw={"width_ratios": [0.9, 1.25]},
    )

    # Left: label distribution after dedup.
    labels = ["Bully", "Non-bully"]
    dedup_values = [total_bully, total_safe]
    y = np.array([1, 0])
    height = 0.36
    left.barh(y, dedup_values, height, color=[INK, LIGHT], edgecolor=INK, linewidth=0.6)
    total = sum(dedup_values)
    for position, value, color in zip(y, dedup_values, (PAPER, INK)):
        left.text(value / 2, position, f"{value / total * 100:.1f}%".replace(".", ","), ha="center", va="center", fontsize=6.4, color=color)
        left.text(value + 90, position, _fmt_int(value), va="center", fontsize=6.4, color=INK)
    left.set_yticks(y)
    left.set_yticklabels(labels)
    left.set_xlim(0, 9000)
    left.set_xticks([])
    left.set_title("(a) Setelah dedup", loc="left", fontsize=8.0, fontweight="bold")
    for spine in ("top", "right", "bottom", "left"):
        left.spines[spine].set_visible(False)
    left.tick_params(axis="y", length=0)

    # Right: split composition.
    splits = [("Train", train), ("Validation", val), ("Test", test)]
    positions = np.arange(len(splits))[::-1]
    for position, (name, frame) in zip(positions, splits):
        counts = frame["label"].value_counts().to_dict()
        safe = int(counts.get(0, 0))
        bully = int(counts.get(1, 0))
        right.barh(position, safe, height=0.46, color=LIGHT, edgecolor=INK, linewidth=0.55)
        right.barh(position, bully, left=safe, height=0.46, color=INK, edgecolor=INK, linewidth=0.55)
        right.text(
            safe + bully + 90,
            position,
            _fmt_int(safe + bully),
            va="center",
            fontsize=6.4,
            color=INK,
        )
    right.set_yticks(positions)
    right.set_yticklabels([name for name, _ in splits])
    right.set_xlim(0, 11800)
    right.set_xticks([])
    right.set_title("(b) Komposisi split", loc="left", fontsize=8.0, fontweight="bold")
    for spine in ("top", "right", "bottom", "left"):
        right.spines[spine].set_visible(False)
    right.tick_params(axis="y", length=0)

    from matplotlib.patches import Patch

    handles = [
        Patch(facecolor=INK, edgecolor=INK, label="Bully"),
        Patch(facecolor=LIGHT, edgecolor=INK, label="Non-bully"),
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=2,
        frameon=False,
        bbox_to_anchor=(0.5, -0.02),
        fontsize=6.8,
    )
    fig.subplots_adjust(left=0.11, right=0.98, top=0.88, bottom=0.18, wspace=0.35)
    return _save(fig, "02_labels_split.png")


def figure_lengths(data: dict[str, object]) -> Path:
    real = data["train"]["text"].astype(str).str.split().str.len()
    synthetic = data["synthetic"]["text"].astype(str).str.split().str.len()

    fig, ax = plt.subplots(figsize=(6.2, 2.75))
    bins = np.arange(0, 51, 1.5)
    ax.hist(
        real.clip(upper=50),
        bins=bins,
        density=True,
        color=PALE,
        edgecolor=INK,
        linewidth=0.45,
        alpha=0.85,
        label=f"Asli (n={_fmt_int(len(real))})",
    )
    ax.hist(
        synthetic.clip(upper=50),
        bins=bins,
        density=True,
        histtype="step",
        color=INK,
        linewidth=1.25,
        label=f"Sintetis (n={_fmt_int(len(synthetic))})",
    )
    ax.axvline(real.median(), color=MID, linewidth=0.8, linestyle=(0, (3, 2)))
    ax.axvline(synthetic.median(), color=INK, linewidth=0.8, linestyle=(0, (3, 2)))
    ax.set_ylim(0, ax.get_ylim()[1] * 1.12)
    ax.set_xlabel("Jumlah kata per teks")
    ax.set_ylabel("Kepadatan")
    ax.set_xlim(0, 45)
    ax.set_yticks([0, 0.05, 0.10, 0.15])
    ax.yaxis.set_major_formatter(FuncFormatter(_comma_tick))
    _clean_axes(ax, grid_axis="x")
    ax.spines["left"].set_visible(False)
    ax.legend(loc="upper right", frameon=False)
    fig.subplots_adjust(left=0.06, right=0.99, top=0.97, bottom=0.16)
    return _save(fig, "03_lengths.png")


def _threshold_scores(frame: pd.DataFrame, threshold: float) -> tuple[float, float, float]:
    predicted = (frame["probability"] >= threshold).astype(int)
    truth = frame["label"].astype(int)
    tp = int(((predicted == 1) & (truth == 1)).sum())
    fp = int(((predicted == 1) & (truth == 0)).sum())
    fn = int(((predicted == 0) & (truth == 1)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def figure_threshold(data: dict[str, object]) -> Path:
    frame = data["b_val_predictions"]
    thresholds = np.arange(0.05, 0.951, 0.01)
    scores = np.array([_threshold_scores(frame, float(t)) for t in thresholds])
    precision, recall, f1 = scores[:, 0], scores[:, 1], scores[:, 2]

    fig, ax = plt.subplots(figsize=(6.1, 2.85))
    ax.plot(thresholds, precision, color=MID, linewidth=0.9, linestyle=(0, (4, 2)), label="Precision")
    ax.plot(thresholds, recall, color=LIGHT, linewidth=1.0, linestyle=(0, (1, 1.5)), label="Recall")
    ax.plot(thresholds, f1, color=INK, linewidth=1.5, label="F1")
    for threshold, marker, filled in ((0.05, "o", False), (0.50, "o", True)):
        value = _threshold_scores(frame, threshold)[2]
        ax.plot(
            threshold,
            value,
            marker=marker,
            markersize=4.5,
            markerfacecolor=INK if filled else PAPER,
            markeredgecolor=INK,
            markeredgewidth=0.9,
            zorder=4,
        )
        ax.axvline(threshold, color=LIGHT, linewidth=0.6, linestyle=(0, (2, 2)), zorder=0)
    ax.text(0.055, 0.899, "0,05 ditolak", fontsize=6.2, color=MID, va="bottom")
    ax.text(0.505, 0.899, "0,50 dipakai", fontsize=6.2, color=INK, va="bottom")
    ax.set_xlim(0, 1.0)
    ax.set_ylim(0.895, 0.94)
    ax.set_yticks(np.arange(0.90, 0.941, 0.01))
    ax.set_xlabel("Threshold")
    ax.set_ylabel("Skor pada validation")
    ax.yaxis.set_major_formatter(FuncFormatter(_comma_tick))
    ax.xaxis.set_major_formatter(FuncFormatter(_comma_tick))
    _clean_axes(ax)
    ax.legend(loc="upper left", frameon=False, ncol=3, handlelength=1.6, columnspacing=1.0)
    fig.subplots_adjust(left=0.09, right=0.99, top=0.97, bottom=0.19)
    return _save(fig, "04_threshold.png")


def figure_validation_test(data: dict[str, object]) -> Path:
    metrics = data["metrics"]
    labels = ["Accuracy", "Precision", "Recall", "F1"]
    keys = ["accuracy", "precision_bully", "recall_bully", "f1_bully"]
    baseline = [BASELINE_VAL[key] for key in keys]
    a_val = [metrics["a_val"][key] for key in keys]
    b_val = [metrics["b_val"][key] for key in keys]
    a_test = [metrics["a_test"][key] for key in keys]
    b_test = [metrics["b_test"][key] for key in keys]

    fig, (left, right) = plt.subplots(1, 2, figsize=(6.5, 2.75), sharey=True)
    x = np.arange(len(labels))

    def draw(ax: plt.Axes, series: list[tuple[str, list[float], str]], width: float) -> None:
        offsets = np.linspace(-width * (len(series) - 1), width * (len(series) - 1), len(series))
        for offset, (name, values, color) in zip(offsets, series):
            ax.bar(x + offset, values, width, color=color, edgecolor=INK, linewidth=0.45, label=name)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_ylim(0.80, 0.96)
        ax.set_yticks([0.80, 0.85, 0.90, 0.95])
        ax.yaxis.set_major_formatter(FuncFormatter(_comma_tick))
        _clean_axes(ax)
        ax.tick_params(axis="x", length=0)
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.12),
            ncol=len(series),
            frameon=False,
            handlelength=1.2,
            fontsize=6.3,
        )

    draw(left, [("Baseline", baseline, PALE), ("A (0,42)", a_val, LIGHT), ("B2 (0,50)", b_val, INK)], 0.22)
    left.set_title("(a) Validation", loc="left", fontsize=8.0, fontweight="bold", pad=5)
    draw(right, [("A (0,42)", a_test, LIGHT), ("B2 (0,05)", b_test, INK)], 0.28)
    right.set_title("(b) Test", loc="left", fontsize=8.0, fontweight="bold", pad=5)
    fig.subplots_adjust(left=0.085, right=0.99, top=0.90, bottom=0.28, wspace=0.12)
    return _save(fig, "05_validation_test.png")


def figure_categories(data: dict[str, object]) -> Path:
    a_metrics = data["metrics"]["a_implicit"]["per_category"]
    b_metrics = data["metrics"]["b_implicit"]["per_category"]
    names = {
        "body_shaming": "Body shaming",
        "gaslighting": "Gaslighting",
        "hinaan_langsung": "Hinaan langsung",
        "keluhan": "Keluhan",
        "kritik": "Kritik",
        "merendahkan": "Merendahkan",
        "netral": "Netral",
        "opini": "Opini",
        "pujian_menyindir": "Pujian menyindir",
        "sarkasme_karya": "Sarkasme karya",
        "sindiran": "Sindiran",
        "subtweet": "Subtweet",
    }
    rows = []
    for category in set(a_metrics) | set(b_metrics):
        a = a_metrics.get(category, {})
        b = b_metrics.get(category, {})
        rows.append(
            {
                "category": category,
                "a": float(a.get("accuracy", np.nan)),
                "b": float(b.get("accuracy", np.nan)),
                "n": int(max(a.get("n", 0), b.get("n", 0))),
            }
        )
    rows.sort(key=lambda row: (-row["b"], -row["n"], -row["a"], row["category"]))
    labels = [f"{names.get(row['category'], row['category'])} ({row['n']})" for row in rows]
    positions = np.arange(len(rows))[::-1]

    fig, ax = plt.subplots(figsize=(6.2, 3.9))
    for position, row in zip(positions, rows):
        ax.plot([row["a"], row["b"]], [position, position], color="#d4d4d4", linewidth=0.9, zorder=1)
    ax.scatter(
        [row["a"] for row in rows],
        positions,
        marker="o",
        s=42,
        facecolors=PAPER,
        edgecolors=MID,
        linewidths=1.0,
        label="A real-only",
        zorder=3,
    )
    ax.scatter(
        [row["b"] for row in rows],
        positions,
        marker="s",
        s=22,
        facecolors=INK,
        edgecolors=INK,
        linewidths=0.8,
        label="B2 real+sintetis",
        zorder=3,
    )
    ax.set_yticks(positions)
    ax.set_yticklabels(labels)
    ax.set_xlim(-0.04, 1.06)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xticks([0, 0.25, 0.50, 0.75, 1.0])
    ax.xaxis.set_major_formatter(FuncFormatter(_comma_tick))
    ax.set_xlabel("Akurasi pada eval set")
    ax.grid(axis="x", color=GRID, linewidth=0.55)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.10), ncol=2, frameon=False)
    fig.subplots_adjust(left=0.25, right=0.99, top=0.90, bottom=0.15)
    return _save(fig, "06_categories.png")


def build_figures() -> None:
    _setup_matplotlib()
    data = _read_project_data()
    figure_pipeline()
    figure_labels_split(data)
    figure_lengths(data)
    figure_threshold(data)
    figure_validation_test(data)
    figure_categories(data)
    print(f"Grafik ditulis ke {FIGURES.relative_to(ROOT)}")


def _strip_theme_fonts(rfonts) -> None:
    for attribute in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        key = qn(attribute)
        if key in rfonts.attrib:
            del rfonts.attrib[key]


def _set_style_font(style, name: str, size: float | None = None, *, bold: bool | None = None, italic: bool | None = None, color: str | None = None) -> None:
    style.font.name = name
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    _strip_theme_fonts(rfonts)
    for attribute in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attribute), name)
    if size is not None:
        style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold
    if italic is not None:
        style.font.italic = italic
    if color is not None:
        style.font.color.rgb = RGBColor.from_string(color)


def _configure_paragraph(style, *, before: float, after: float, line: float, keep_next: bool = False) -> None:
    paragraph = style.paragraph_format
    paragraph.space_before = Pt(before)
    paragraph.space_after = Pt(after)
    paragraph.line_spacing = line
    paragraph.keep_with_next = keep_next


def _add_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = "PAGE"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instruction)
    run._r.append(end)
    run.font.name = "Times New Roman"
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)


def make_reference_doc(path: Path) -> None:
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(1.8)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(1.8)
    section.right_margin = Cm(1.8)
    section.header_distance = Cm(0.8)
    section.footer_distance = Cm(0.8)

    styles = doc.styles
    _set_style_font(styles["Normal"], "Times New Roman", 10.5, color="1A1A1A")
    _configure_paragraph(styles["Normal"], before=0, after=2.5, line=1.05)

    for name in ("Body Text", "First Paragraph"):
        try:
            style = styles[name]
        except KeyError:
            style = styles.add_style(name, 1)
            style.base_style = styles["Normal"]
        _set_style_font(style, "Times New Roman", 10.5, color="1A1A1A")
        _configure_paragraph(style, before=0, after=2.5, line=1.05)

    for name, size, before, after in (
        ("Heading 1", 12.5, 10, 3),
        ("Heading 2", 10.8, 6, 2),
        ("Heading 3", 10.5, 5, 2),
    ):
        style = styles[name]
        _set_style_font(style, "Times New Roman", size, bold=True, italic=(name == "Heading 3"), color="1A1A1A")
        _configure_paragraph(style, before=before, after=after, line=1.0, keep_next=True)
        style.paragraph_format.keep_together = True

    for name, size, bold, italic, after in (
        ("Title", 16, True, False, 3),
        ("Subtitle", 11, False, True, 2),
        ("Date", 9, False, False, 8),
    ):
        try:
            style = styles[name]
        except KeyError:
            style = styles.add_style(name, 1)
            style.base_style = styles["Normal"]
        _set_style_font(style, "Times New Roman", size, bold=bold, italic=italic, color="1A1A1A" if name != "Date" else "555555")
        _configure_paragraph(style, before=0, after=after, line=1.0)
        style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

    from docx.enum.style import WD_STYLE_TYPE

    for name, size in (("Compact", 10.5), ("Block Text", 9.5), ("Source Code", 8.0), ("Verbatim Char", 8.5)):
        try:
            style = styles[name]
        except KeyError:
            style = styles.add_style(name, 1)
            style.base_style = styles["Normal"]
        if name in ("Source Code", "Verbatim Char"):
            _set_style_font(style, "Courier New", size, color="1A1A1A")
        else:
            _set_style_font(style, "Times New Roman", size, color="1A1A1A")
        if style.type == WD_STYLE_TYPE.PARAGRAPH:
            _configure_paragraph(style, before=0, after=2, line=1.0)

    for border in styles["Title"].element.get_or_add_pPr().findall(qn("w:pBdr")):
        styles["Title"].element.get_or_add_pPr().remove(border)

    for name in ("Image Caption", "Table Caption", "Caption"):
        try:
            style = styles[name]
        except KeyError:
            style = styles.add_style(name, 1)
            style.base_style = styles["Normal"]
        _set_style_font(style, "Times New Roman", 8.5, italic=True, color="444444")
        _configure_paragraph(style, before=2, after=7, line=1.0)

    footer = section.footer
    _add_page_number(footer.paragraphs[0])
    doc.core_properties.title = "Deteksi Cyberbullying Bahasa Indonesia"
    doc.core_properties.subject = "Perbandingan model NLP dengan data sintetis untuk sindiran non-kasar"
    doc.core_properties.author = ""
    doc.core_properties.last_modified_by = ""
    doc.save(path)


def _force_run_font(run, name: str, size: float, *, bold: bool | None = None) -> None:
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    _strip_theme_fonts(rfonts)
    for attribute in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attribute), name)
    run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)


def _set_table_borders(table) -> None:
    tbl_pr = table._tbl.tblPr
    for tag in ("w:tblBorders", "w:tblCellMar"):
        for existing in tbl_pr.findall(qn(tag)):
            tbl_pr.remove(existing)
    borders = OxmlElement("w:tblBorders")
    for edge, size, color in (
        ("top", 8, "1A1A1A"),
        ("bottom", 8, "1A1A1A"),
        ("insideH", 4, "D0D0D0"),
        ("left", 0, "FFFFFF"),
        ("right", 0, "FFFFFF"),
        ("insideV", 0, "FFFFFF"),
    ):
        element = OxmlElement(f"w:{edge}")
        if size:
            element.set(qn("w:val"), "single")
            element.set(qn("w:sz"), str(size))
            element.set(qn("w:space"), "0")
            element.set(qn("w:color"), color)
        else:
            element.set(qn("w:val"), "nil")
        borders.append(element)
    tbl_pr.append(borders)

    cell_margins = OxmlElement("w:tblCellMar")
    for side, width in (("top", 28), ("left", 70), ("bottom", 28), ("right", 70)):
        element = OxmlElement(f"w:{side}")
        element.set(qn("w:w"), str(width))
        element.set(qn("w:type"), "dxa")
        cell_margins.append(element)
    tbl_pr.append(cell_margins)


def _reorder_tbl_pr(tbl_pr) -> None:
    order = [
        "tblStyle", "tblpPr", "tblOverlap", "bidiVisual",
        "tblStyleRowBandSize", "tblStyleColBandSize", "tblW", "jc",
        "tblCellSpacing", "tblInd", "tblBorders", "shd", "tblLayout",
        "tblCellMar", "tblLook", "tblCaption", "tblDescription", "tblPrChange",
    ]
    children = list(tbl_pr)
    for child in children:
        tbl_pr.remove(child)
    for name in order:
        for child in children:
            if child.tag == qn(f"w:{name}"):
                tbl_pr.append(child)
    for child in children:
        if child.getparent() is None:
            tbl_pr.append(child)


def _autofit_columns(table) -> None:
    lengths = []
    for column in table.columns:
        values = [len(cell.text.strip()) for cell in column.cells]
        lengths.append(max(values + [1]))
    weights = [max(8, min(18, value)) for value in lengths]
    available = 6.65
    widths = [available * weight / sum(weights) for weight in weights]
    widths = [max(0.55, width) for width in widths]
    scale = available / sum(widths)
    widths = [width * scale for width in widths]

    table.autofit = False
    for index, width in enumerate(widths):
        table.columns[index].width = Inches(width)
        for cell in table.columns[index].cells:
            cell.width = Inches(width)

    tbl_pr = table._tbl.tblPr
    for existing in tbl_pr.findall(qn("w:tblW")):
        tbl_pr.remove(existing)
    table_width = OxmlElement("w:tblW")
    table_width.set(qn("w:type"), "pct")
    table_width.set(qn("w:w"), "5000")
    tbl_pr.append(table_width)
    for existing in tbl_pr.findall(qn("w:tblLayout")):
        tbl_pr.remove(existing)
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tbl_pr.append(layout)


def _style_tables(doc) -> None:
    for table in doc.tables:
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        for tag in ("w:tblStyle", "w:tblCaption", "w:tblLook"):
            for element in table._tbl.tblPr.findall(qn(tag)):
                table._tbl.tblPr.remove(element)
        _autofit_columns(table)
        _set_table_borders(table)
        for row_index, row in enumerate(table.rows):
            tr_pr = row._tr.get_or_add_trPr()
            for tag in ("w:cantSplit", "w:tblHeader"):
                for existing in tr_pr.findall(qn(tag)):
                    tr_pr.remove(existing)
            cant_split = OxmlElement("w:cantSplit")
            tr_pr.append(cant_split)
            if row_index == 0:
                header = OxmlElement("w:tblHeader")
                header.set(qn("w:val"), "true")
                tr_pr.append(header)
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.space_before = Pt(0.5)
                    paragraph.paragraph_format.space_after = Pt(0.5)
                    paragraph.paragraph_format.line_spacing = 1.0
                    for run in paragraph.runs:
                        _force_run_font(run, "Times New Roman", 8.5, bold=(row_index == 0) or None)
        _reorder_tbl_pr(table._tbl.tblPr)


def _style_figures(doc) -> None:
    for paragraph in doc.paragraphs:
        if paragraph._p.xpath(".//w:drawing"):
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.space_before = Pt(3)
            paragraph.paragraph_format.space_after = Pt(1)
            paragraph.paragraph_format.keep_together = True
            paragraph.paragraph_format.keep_with_next = True
        elif paragraph.style.name in ("Image Caption", "Caption"):
            paragraph.paragraph_format.keep_together = True


def postprocess(path: Path) -> None:
    doc = Document(path)
    for paragraph in doc.paragraphs:
        if paragraph.style.name in ("Body Text", "First Paragraph", "Normal"):
            for run in paragraph.runs:
                if run.style.name == "Verbatim Char" or run.font.name == "Courier New":
                    continue
                _force_run_font(run, "Times New Roman", 10.5)
    _style_figures(doc)
    _style_tables(doc)
    doc.core_properties.title = "Deteksi Cyberbullying Bahasa Indonesia"
    doc.core_properties.subject = "Perbandingan model NLP dengan data sintetis untuk sindiran non-kasar"
    doc.core_properties.author = ""
    doc.core_properties.last_modified_by = ""
    doc.save(path)


def find_pandoc() -> Path:
    configured = os.environ.get("PANDOC")
    if configured:
        candidate = Path(configured).expanduser()
        if candidate.exists():
            return candidate
        raise FileNotFoundError(f"PANDOC menunjuk ke file yang tidak ada: {candidate}")

    discovered = shutil.which("pandoc")
    if discovered:
        return Path(discovered)

    local = TOOLS / "pandoc" / "bin" / "pandoc"
    if local.exists():
        return local

    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise FileNotFoundError(
            "Pandoc tidak ditemukan. Pasang Pandoc 3.x lalu jalankan ulang, "
            "atau set PANDOC=/path/ke/pandoc."
        )

    print("Pandoc belum ada; mengunduh rilis resmi arm64 macOS ...")
    TOOLS.mkdir(parents=True, exist_ok=True)
    archive = TOOLS / "pandoc.zip"
    with urllib.request.urlopen("https://api.github.com/repos/jgm/pandoc/releases/latest") as response:
        release = json.load(response)
    asset = next(
        (
            item
            for item in release.get("assets", [])
            if "arm64-macOS.zip" in item.get("name", "")
        ),
        None,
    )
    if asset is None:
        raise RuntimeError("Aset Pandoc arm64 macOS tidak ditemukan di rilis terbaru.")
    urllib.request.urlretrieve(asset["browser_download_url"], archive)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(TOOLS)
    archive.unlink(missing_ok=True)
    candidates = list(TOOLS.glob("pandoc-*/bin/pandoc"))
    if not candidates:
        raise RuntimeError("Pandoc terunduh tetapi binary tidak ditemukan.")
    binary = candidates[0]
    binary.chmod(binary.stat().st_mode | 0o755)
    local.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(binary, local)
    local.chmod(local.stat().st_mode | 0o755)
    return local


def build_docx() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Sumber laporan tidak ada: {SOURCE}")
    pandoc = find_pandoc()
    reference = TOOLS / "reference.docx"
    TOOLS.mkdir(parents=True, exist_ok=True)
    make_reference_doc(reference)
    command = [
        str(pandoc),
        str(SOURCE),
        "--from=markdown+tex_math_dollars+pipe_tables+implicit_figures",
        "--to=docx",
        f"--reference-doc={reference}",
        f"--resource-path={DOCS}",
        "--metadata=lang:id",
        f"--output={OUTPUT}",
    ]
    subprocess.run(command, check=True, cwd=ROOT)
    postprocess(OUTPUT)
    print(f"DOCX ditulis ke {OUTPUT.relative_to(ROOT)}")


def validate_docx() -> None:
    doc = Document(OUTPUT)
    with zipfile.ZipFile(OUTPUT) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8")
        media = [name for name in archive.namelist() if name.startswith("word/media/")]

    text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                text += "\n" + cell.text

    problems: list[str] = []
    if doc.styles["Normal"].font.name != "Times New Roman":
        problems.append("style Normal bukan Times New Roman")
    if document_xml.count("m:oMath") < 10:
        problems.append(f"rumus OMML hanya {document_xml.count('m:oMath')}")
    if len(doc.inline_shapes) < 7:
        problems.append(f"gambar tertanam hanya {len(doc.inline_shapes)}")
    if len(doc.tables) < 5:
        problems.append(f"tabel hanya {len(doc.tables)}")
    for placeholder in ("TODO", "Lorem ipsum", "TBD", "PLACEHOLDER"):
        if placeholder.lower() in text.lower():
            problems.append(f"placeholder ditemukan: {placeholder}")
    if problems:
        raise RuntimeError("Validasi DOCX gagal:\n- " + "\n- ".join(problems))

    print(
        "Validasi: "
        f"{len(doc.paragraphs)} paragraf, {len(doc.tables)} tabel, "
        f"{len(doc.inline_shapes)} gambar, {len(media)} media, "
        f"{document_xml.count('m:oMath')} elemen OMML, font Normal Times New Roman."
    )
    print(f"Ukuran DOCX: {OUTPUT.stat().st_size / 1024:.0f} KB")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-figures", action="store_true", help="Pakai grafik yang sudah ada.")
    parser.add_argument("--figures-only", action="store_true", help="Hanya buat grafik.")
    args = parser.parse_args()

    if not args.skip_figures:
        build_figures()
    if args.figures_only:
        return 0
    build_docx()
    validate_docx()
    return 0


if __name__ == "__main__":
    sys.exit(main())
