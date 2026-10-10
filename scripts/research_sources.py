"""Download public research inputs to an ignored directory; never republish PDFs."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import requests

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "gross_latin": "https://gross.uz/uploaded/new-site/documents/osago-doc-mPGc-Wd1fg.pdf",
    "gross_cyrillic": "https://gross.uz/public_offers/osago-offer-uz.pdf",
    "inson_russian": "https://insuranceon.uz/media/attachments/2026/01/15/ruOsago_offer.pdf",
    "law_current_uz": "https://lex.uz/docs/1366339",
    "law_2024_uz": "https://lex.uz/docs/1366339?ONDATE=06.09.2024%2000",
    "law_2019_uz": "https://lex.uz/docs/1366339?ONDATE=17.06.2019%2000",
    "model_card": "https://huggingface.co/intfloat/multilingual-e5-small/raw/main/README.md",
}

def main():
    dest = ROOT / "local_data" / "sources"
    dest.mkdir(parents=True, exist_ok=True)
    manifest = []
    for key, url in SOURCES.items():
        row = {"id": key, "url": url, "accessed_at": datetime.now(timezone.utc).isoformat()}
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            content = response.content
            suffix = ".pdf" if key in {"gross_latin", "gross_cyrillic", "inson_russian"} else ".txt"
            if suffix == ".pdf" and not content.startswith(b"%PDF-"):
                raise ValueError("Response is not a PDF")
            (dest / (key + suffix)).write_bytes(content)
            row.update(sha256=hashlib.sha256(content).hexdigest(), bytes=len(content),
                       content_type=response.headers.get("Content-Type"), final_url=response.url,
                       http_status=response.status_code, status="downloaded")
        except (requests.RequestException, ValueError) as exc:
            row.update(status="unavailable", error=type(exc).__name__)
        manifest.append(row)
        print(key, row["status"], row.get("bytes", ""))
    (ROOT / "evaluation").mkdir(exist_ok=True)
    (ROOT / "evaluation" / "source_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
