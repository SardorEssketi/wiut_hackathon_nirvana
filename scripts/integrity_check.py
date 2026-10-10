"""Verify recorded dataset/model/catalogue hashes without changing evidence."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT/'evaluation'/name).read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks={}
    dataset=read('dataset_manifest.json')
    for case in dataset:
        checks[case['path']]=digest(ROOT/case['path'])==case['sha256']
    benchmark=read('benchmark_results.json')
    for name,expected in benchmark['dataset_files_sha256'].items():
        checks[f'evaluation/{name}']=digest(ROOT/'evaluation'/name)==expected
    for case in benchmark['modes']['lexical']['cases']:
        if case['split']=='fresh_evaluation':
            name=f"tests/fixtures/blind/{case['id']}.pdf"
            checks[name]=digest(ROOT/name)==case['sha256']
    for name,expected in read('model_manifest.json')['files'].items():
        checks[f'models/{name}']=digest(ROOT/'models/multilingual-e5-small'/name)==expected
    checks['rules/catalogue.v1.json']=digest(ROOT/'rules/catalogue.v1.json')==benchmark['rules_catalogue_sha256']
    for case in read('source_manifest.json'):
        if case['id'] in {'gross_latin','gross_cyrillic','inson_russian'}:
            checks[f"local_data/sources/{case['id']}.pdf"]=digest(ROOT/f"local_data/sources/{case['id']}.pdf")==case['sha256']
    tracked=subprocess.check_output(['git','-c',f'safe.directory={ROOT.as_posix()}','ls-files'],cwd=ROOT,text=True).splitlines()
    checks['third_party_originals_and_model_weights_excluded_from_git']=not any(name.startswith(('local_data/','models/','.venv/')) for name in tracked)
    assert all(checks.values()),[name for name,ok in checks.items() if not ok]
    result={'checked_at':datetime.now(timezone.utc).isoformat(),'success':True,'checks':checks}
    (ROOT/'evaluation/integrity_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Verified',len(checks),'recorded hashes and repository exclusion checks.')


if __name__=='__main__':
    main()
