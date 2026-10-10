"""Record the actual tested environment without exposing environment variables."""
from pathlib import Path
import subprocess
import sys
from importlib import metadata
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    result = subprocess.run([sys.executable,"-m","pip","freeze"],capture_output=True,text=True,check=True)
    (ROOT / "requirements.lock.txt").write_text(result.stdout.replace("\r\n","\n"),encoding="utf-8")
    pending = ["streamlit","pymupdf","pydantic","sentence-transformers","numpy","requests"]
    versions = {}
    while pending:
        name = canonicalize_name(pending.pop())
        if name in versions:
            continue
        dist = metadata.distribution(name)
        versions[name] = dist.version
        for raw in dist.requires or []:
            requirement = Requirement(raw)
            if requirement.marker is None or requirement.marker.evaluate({"extra":""}):
                pending.append(requirement.name)
    (ROOT / "requirements.runtime.lock.txt").write_text(
        "# Exact versions of the tested runtime dependency graph; CPU torch provisioned separately in Docker.\n" +
        "\n".join(f"{name}=={version}" for name,version in sorted(versions.items()))+"\n",encoding="utf-8")
    print("Saved exact tested local dependency versions")
