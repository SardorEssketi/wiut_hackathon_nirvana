"""Record actual OCR availability; OCR remains disabled until a labelled quality evaluation passes."""
from pathlib import Path
from datetime import datetime, timezone
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def main():
    binary = shutil.which("tesseract")
    candidates = ["C:/Program Files/Tesseract-OCR/tesseract.exe", "C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"]
    binary = binary or next((p for p in candidates if Path(p).exists()), None)
    row = {"checked_at": datetime.now(timezone.utc).isoformat(), "binary_available": bool(binary),
        "required_languages": ["uzb", "uzb_cyrl", "rus"], "ocr_enabled": False,
        "quality_metrics": None, "reason": "No evaluated local OCR path; scanned pages must produce UNVERIFIABLE."}
    if binary:
        result = subprocess.run([binary, "--list-langs"], capture_output=True, text=True, timeout=10)
        row["installed_languages"] = result.stdout.splitlines()[1:]
        row["missing_languages"] = sorted(set(row["required_languages"])-set(row["installed_languages"]))
    (ROOT / "evaluation" / "ocr_probe.json").write_text(json.dumps(row, indent=2), encoding="utf-8")
    print(json.dumps(row))

if __name__ == "__main__":
    main()
