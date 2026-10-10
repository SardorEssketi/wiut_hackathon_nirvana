"""Provision model once; runtime never downloads or contacts Hugging Face."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
os.environ["HF_HUB_OFFLINE"] = "0"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
from huggingface_hub import HfApi, snapshot_download

ROOT = Path(__file__).resolve().parents[1]

def main():
    repo = "intfloat/multilingual-e5-small"
    metadata = HfApi().model_info(repo)
    revision = os.getenv("POLISDIFF_MODEL_REVISION") or metadata.sha
    dest = ROOT / "models" / "multilingual-e5-small"
    snapshot_download(repo, revision=revision, local_dir=dest,
        allow_patterns=["*.json", "*.txt", "*.model", "model.safetensors", "1_Pooling/*", "README.md", "LICENSE"],
        max_workers=2)
    manifest = {"repository": repo, "revision": revision, "license": "MIT (model card)",
        "accessed_at": datetime.now(timezone.utc).isoformat(),
        "files": {str(p.relative_to(dest)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in dest.rglob("*") if p.is_file() and ".cache" not in p.parts}}
    (ROOT / "evaluation").mkdir(exist_ok=True)
    (ROOT / "evaluation" / "model_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Provisioned", repo, revision, len(manifest["files"]), "files")

if __name__ == "__main__":
    main()
