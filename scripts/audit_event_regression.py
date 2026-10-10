"""Read-only comparison with the inspected baseline engine; no checkout/reset."""
from datetime import date, datetime, timezone
from pathlib import Path
from types import ModuleType
import json
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.generate_fixtures import create_pdf
from polisdiff.engine import load_catalogue, evaluate
from polisdiff.extraction import extract_pdf

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = subprocess.run(['git','-c',f'safe.directory={ROOT.as_posix()}',
        'show','41dcafd:polisdiff/engine.py'],cwd=ROOT,check=True,capture_output=True).stdout.decode('utf-8')
    # Only the already inspected project baseline, never an uploaded file/module.
    baseline = ModuleType('polisdiff._audited_baseline_engine')
    baseline.__package__ = 'polisdiff'
    baseline.__file__ = str(ROOT/'polisdiff/engine.py')
    exec(compile(source,'audited-baseline-engine','exec'),baseline.__dict__)
    rules = {r.id:r for r in load_catalogue()[1]}
    dest = ROOT/'local_data/audit_events'
    dest.mkdir(parents=True,exist_ok=True)
    cases = [
        ('court','OSAGO_PAYMENT', 'Страховое возмещение выплачивается в срок 4 рабочих дней после принятия решения суда.', 'MATCH_FOUND','UNVERIFIABLE'),
        ('accident','OSAGO_DECISION_NOTICE', 'Страхователю сообщается решение о страховом возмещении в течение 12 дней после ДТП, письменное заявление хранится в деле.', 'MATCH_FOUND','UNVERIFIABLE'),
        ('transfer','OSAGO_PAYMENT', 'Страховое возмещение перечисляется получателю в срок 9 рабочих дней после принятия решения страховщиком.', 'NOT_FOUND','POTENTIAL_CONFLICT'),
    ]
    rows = []
    for key,rule_id,term,before,after in cases:
        path = dest/f'{key}.pdf'
        create_pdf(path,[[term]])
        doc = extract_pdf(path.read_bytes())
        old = baseline.evaluate(rules[rule_id],doc,doc.passages,date(2026,1,5),date(2026,10,10))
        new = evaluate(rules[rule_id],doc,doc.passages,date(2026,1,5),date(2026,10,10))
        assert old.status.value == before and new.status.value == after
        rows.append({'id':key,'rule_id':rule_id,'original_synthetic_term':term,
            'baseline_status':old.status.value,'current_status':new.status.value,
            'baseline_reason':old.reason,'current_reason':new.reason})
        print(key,before,'->',after,flush=True)
    result={'checked_at':datetime.now(timezone.utc).isoformat(),'baseline_commit':'41dcafd',
            'success':True,'cases':rows,'ground_truth':'Engineering regression assertions, not legal labels.'}
    (ROOT/'evaluation/audit_event_reproduction.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
