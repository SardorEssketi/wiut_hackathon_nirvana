"""Operator opt-in provisioning, once per process before offline model loading.

Default is no network. A free host must expose a sufficient measured memory
limit before the operator-enabled download is attempted. No document bytes enter
this subprocess. A restart is required after changing configuration or files.
"""
from functools import lru_cache
import os
from pathlib import Path
import subprocess
import sys
from .deployment import ROOT, model_files_status

MIN_MEMORY = 2 * 1024**3
MIN_HEADROOM = 1536 * 1024**2


def enabled():
    return os.getenv('POLISDIFF_PROVISION_MODEL', '').lower() in {'1', 'true'}


def memory_limit():
    for path in ('/sys/fs/cgroup/memory.max', '/sys/fs/cgroup/memory/memory.limit_in_bytes'):
        try:
            value = int(Path(path).read_text().strip())
            if 0 < value < 2**60:
                return value
        except (OSError, ValueError):
            pass
    return None


def memory_current():
    for path in ('/sys/fs/cgroup/memory.current', '/sys/fs/cgroup/memory/memory.usage_in_bytes'):
        try:
            value = int(Path(path).read_text().strip())
            if value >= 0:
                return value
        except (OSError, ValueError):
            pass
    return None


@lru_cache(maxsize=1)
def provision_model():
    if model_files_status()['state'] == 'files_present':
        return 'already_present'
    if not enabled():
        return 'disabled'
    limit = memory_limit()
    if limit is None or limit < MIN_MEMORY:
        return 'insufficient_or_unknown_memory_budget'
    current = memory_current()
    if current is None or limit - current < MIN_HEADROOM:
        return 'insufficient_or_unknown_memory_headroom'
    try:
        result = subprocess.run([sys.executable, str(ROOT/'scripts/download_model.py')],
            cwd=ROOT, capture_output=True, timeout=180, env=os.environ.copy())
        if result.returncode == 0 and model_files_status()['state'] == 'files_present':
            return 'provisioned'
    except subprocess.TimeoutExpired:
        return 'download_timeout'
    except OSError:
        pass
    return 'download_failed'


def provisioning_status():
    # Reading readiness must never start a download.
    return dict(operator_enabled=enabled(), minimum_memory_bytes=MIN_MEMORY,
                minimum_headroom_bytes=MIN_HEADROOM, measured_limit_bytes=memory_limit(),
                measured_current_bytes=memory_current(),
                result=provision_model() if provision_model.cache_info().currsize else 'not_attempted')
