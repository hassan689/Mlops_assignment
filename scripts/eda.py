import random
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

random.seed(42)
FIG_DIR = Path("artifacts/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv("artifacts/audit.csv")
print(f"Loaded {len(df)} rows. Classes: {df['class'].unique().tolist()}")

# ---------- 1) Sample grids (one per class) ----------
for cls in sorted(df["class"].unique()):
    paths = df[df["class"] == cls]["path"].sample(10, random_state=42).tolist()
    fig, axes = plt.subplots(2, 5, figsize=(15, 6))
    for ax, p in zip(axes.ravel(), paths):
        ax.imshow(Image.open(p).convert("RGB"))
        ax.axis("off")
    fig.suptitle(f"Sample images — class: {cls}", fontsize=14)
    fig.tight_layout()
    out = FIG_DIR / f"samples_{cls}.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"wrote {out}")

# ---------- 2) Histograms ----------
for col, unit, scale in [
    ("width",    "px",    1),
    ("height",   "px",    1),
    ("file_size","KB",    1/1024),   # convert bytes -> KB for readability
]:
    fig, ax = plt.subplots(figsize=(8, 4))
    for cls in sorted(df["class"].unique()):
        vals = df.loc[df["class"] == cls, col] * scale
        ax.hist(vals, bins=40, alpha=0.55, label=f"{cls} (n={len(vals)})")
    ax.set_xlabel(f"{col} ({unit})")
    ax.set_ylabel("count")
    ax.set_title(f"Distribution of {col} per class")
    ax.legend()
    fig.tight_layout()
    out = FIG_DIR / f"hist_{col}.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"wrote {out}")

print("\nDone. Figures in", FIG_DIR)