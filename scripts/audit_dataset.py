import hashlib
import json
from pathlib import Path
import pandas as pd
from PIL import Image, UnidentifiedImageError

DATA_DIR = Path("data")
OUT_DIR = Path("artifacts")
OUT_DIR.mkdir(exist_ok=True)

VALID_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif"}
CLASS_MAP = {"ai": "ai", "real": "real"}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def audit():
    rows, corrupt = [], []
    for class_dir, label in CLASS_MAP.items():
        folder = DATA_DIR / class_dir
        if not folder.exists():
            print(f"[WARN] missing folder: {folder}")
            continue
        for p in folder.rglob("*"):
            if p.suffix.lower() not in VALID_EXTS or not p.is_file():
                continue
            rec = {"path": str(p), "class": label, "file_size": p.stat().st_size}
            try:
                with Image.open(p) as im:
                    im.verify()                      # detects truncation
                with Image.open(p) as im:            # reopen after verify
                    rec.update(width=im.width, height=im.height,
                               mode=im.mode, format=im.format)
                rec["sha256"] = sha256(p)
            except (UnidentifiedImageError, OSError, Exception) as e:
                corrupt.append({"path": str(p), "error": str(e)})
                continue
            rows.append(rec)

    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "audit.csv", index=False)

    summary = df.groupby("class").agg(
        count=("path", "count"),
        width_min=("width", "min"), width_med=("width", "median"), width_max=("width", "max"),
        height_min=("height", "min"), height_med=("height", "median"), height_max=("height", "max"),
        size_min=("file_size", "min"), size_med=("file_size", "median"), size_max=("file_size", "max"),
    ).to_dict()

    dups = df[df.duplicated("sha256", keep=False)].sort_values("sha256")
    dups.to_csv(OUT_DIR / "duplicates.csv", index=False)

    with open(OUT_DIR / "audit_summary.json", "w") as f:
        json.dump({"summary": summary, "corrupt": corrupt,
                   "n_duplicates": len(dups)}, f, indent=2)

    print(json.dumps({"summary": summary, "corrupt": len(corrupt),
                      "duplicates": len(dups)}, indent=2))

if __name__ == "__main__":
    audit()