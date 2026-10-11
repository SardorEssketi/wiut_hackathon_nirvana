"""Read-only deployment diagnostics. Never downloads files or loads a model."""
from functools import lru_cache
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
import hashlib
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def model_path():
    return Path(os.getenv('POLISDIFF_MODEL_PATH', str(ROOT / 'models' / 'multilingual-e5-small')))


def model_files_status():
    path = model_path()
    names = ('config.json', 'model.safetensors', 'tokenizer.json', 'modules.json', '1_Pooling/config.json')
    missing = [name for name in names if not (path / name).is_file()]
    return dict(state='not_provisioned' if missing else 'files_present', missing=missing,
                path=str(path), bytes=sum((path/name).stat().st_size for name in names if (path/name).is_file()))


@lru_cache(maxsize=1)
def source_revision():
    try:
        result = subprocess.run(['git', '-c', f'safe.directory={ROOT.as_posix()}', 'rev-parse', 'HEAD'], cwd=ROOT,
                                capture_output=True, text=True, timeout=2)
        value = result.stdout.strip()
        if result.returncode == 0 and len(value) == 40 and all(c in '0123456789abcdef' for c in value):
            return value
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def deployment_diagnostics():
    from .provisioning import provisioning_status
    # The content fingerprint remains useful when a host omits .git or HEAD
    # differs from working-tree files. No uploaded evidence or secrets included.
    digest = hashlib.sha256()
    names = ['app.py', 'requirements.txt', '.streamlit/config.toml', 'rules/catalogue.v1.json']
    names += sorted(str(p.relative_to(ROOT)).replace('\\', '/') for p in (ROOT/'polisdiff').glob('*.py'))
    for name in names:
        digest.update(name.encode() + b'\0' + (ROOT/name).read_bytes() + b'\0')
    dependencies = {}
    for name in ('streamlit', 'pymupdf', 'pydantic', 'sentence-transformers', 'torch', 'transformers', 'numpy'):
        try:
            dependencies[name] = version(name)
        except PackageNotFoundError:
            dependencies[name] = None
    resource = {}
    for name in ('memory.max', 'memory.current', 'memory.peak', 'cpu.max'):
        try:
            resource[name] = (Path('/sys/fs/cgroup')/name).read_text().strip()
        except OSError:
            pass
    return dict(source_revision=source_revision(), source_content_sha256=digest.hexdigest(),
                python=sys.version.split()[0], dependencies=dependencies,
                model=model_files_status(), offline={'HF_HUB_OFFLINE': os.getenv('HF_HUB_OFFLINE'),
                'TRANSFORMERS_OFFLINE': os.getenv('TRANSFORMERS_OFFLINE')},
                torch_threads=os.getenv('POLISDIFF_TORCH_THREADS', '2'), resources=resource,
                provisioning=provisioning_status())
