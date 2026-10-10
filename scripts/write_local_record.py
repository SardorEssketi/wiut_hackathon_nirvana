"""Generate the local verification document from measured artifacts."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT/'evaluation'/name).read_text(encoding='utf-8'))


def main():
    tests=read('tests.final.json')
    native=read('browser_results.json')
    web=read('browser.container_results.json')
    offline=read('container_results.json')
    release=read('local_release_manifest.json')
    benchmark=read('benchmark_results.json')
    integrity=read('integrity_results.json')
    fresh=benchmark['modes']['hybrid']['summary_by_split']['fresh_evaluation']
    lines=['# Actual local verification','',
        f"Recorded: {release['recorded_at']}. Source checkpoint: `{release['source_commit']}`.",'',
        '**Local prototype only; not hackathon submission-ready.** No public hosting',
        'was configured. Public deployment requires later authorization and an independent browser test.','',
        '## Commands actually exercised','',
        '```powershell',
        '.venv/Scripts/python.exe main.py',
        '.venv/Scripts/python.exe -m pytest -q --basetemp=local_data/pytest_temp --junitxml=evaluation/tests.final.xml',
        '.venv/Scripts/python.exe scripts/browser_check.py',
        '.venv/Scripts/python.exe scripts/local_smoke.py',
        'docker build -t polisdiff-ai:local .',
        '.venv/Scripts/python.exe scripts/run_container_check.py',
        'docker compose -p polisdiff-local up -d --no-build',
        '.venv/Scripts/python.exe scripts/browser_check.py --url http://localhost:8502 --output browser.container_results.json',
        '.venv/Scripts/python.exe scripts/local_smoke.py --url http://localhost:8502 --output smoke.container_results.json',
        '```','',
        'Native UI: [localhost:8501](http://localhost:8501). Isolated Compose UI:',
        '[localhost:8502](http://localhost:8502). Servers use `0.0.0.0` internally;',
        'Compose publishes only the host loopback interface. A separate local container',
        'also verified a changed `PORT=8503` through host port 8502 before Compose testing.','',
        '## Actual checks','',
        f"- Complete suite: **{tests['passed']} passed, {tests['failures']} failed, {tests['errors']} errors, {tests['skipped']} skipped**.",
        f"- Native Chromium: {len(native['cases'])} supported PDFs; success `{native['success']}`.",
        f"- Docker Chromium: {len(web['cases'])} supported PDFs; success `{web['success']}`.",
        '- Each full journey includes three script variants, a separately authored unseen',
        '  fixture, three actual public PDFs, exact quote/page checks, JSON/HTML review',
        '  exports, raster preview, mobile content and session clearing.',
        '- Fresh-start smoke checks exercise unknown-date abstention, changing the audit',
        '  date into 2024, the historical 40-million source version, and both AI modes.',
        f"- Offline read-only/non-root container: {len(offline['cases'])} PDFs; UID {offline['uid']}; networking disabled.",
        f"- Container CLI model initialization: {offline['model_initialization_seconds']:.3f} s; peak main-process RSS {offline['peak_main_process_rss_mib']:.1f} MiB.",
        f"- Full service cgroup peak: {release['service_cgroup_peak_memory_bytes']/1024**2:.1f} MiB, within configured {release['memory_limit_bytes']/1024**3:.1f} GiB. OOM kills: {release['memory_events']['oom_kill']}.",
        f"- Health: `{release['health']}`. Image: `{release['image_id']}`.",
        f"- All {len(release['source_hash_matches_container'])} recorded application/configuration source hashes match the tested image and committed source checkpoint.",
        f"- Dataset/model/public-input integrity: {len(integrity['checks'])} recorded hashes and Git exclusion checks; success `{integrity['success']}`.",'',
        'The offline CLI memory measurement excludes parser children; the service cgroup',
        'peak includes the container processes. These are different runs. Single-machine',
        'measurements do not establish production throughput, free-tier suitability or an SLA.','',
        '## Evaluation and limitations','',
        f"Fresh synthetic hybrid status accuracy: {fresh['rule_status_accuracy']*100:.1f}% across {fresh['labelled_rule_results']} labels; conflict recall {fresh['conflict_recall']*100:.1f}%.",
        'One Russian payment phrase was retrieved but missed by deterministic extraction.',
        'Real samples abstain extensively; no expert legal ground truth or AI accuracy gain',
        'is established. OCR remains disabled, with scans explicitly unsupported.',
        'All interpretations remain `PENDING_LEGAL_REVIEW`. No finding certifies an entire policy.','',
        'Artifacts: [tests](../evaluation/tests.final.json),',
        '[native browser](../evaluation/browser_results.json),',
        '[Docker browser](../evaluation/browser.container_results.json),',
        '[offline container](../evaluation/container_results.json),',
        '[image/source/resource record](../evaluation/local_release_manifest.json),',
        '[benchmark](../evaluation/RESULTS.md), [limitations](LIMITATIONS.md).','']
    (ROOT/'docs/LOCAL_VERIFICATION.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Generated actual local verification record.')


if __name__=='__main__':
    main()
