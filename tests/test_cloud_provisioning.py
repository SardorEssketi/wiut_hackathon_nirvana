from types import SimpleNamespace
import subprocess
import pytest
from polisdiff import provisioning
import hashlib
import json
import sys


@pytest.fixture(autouse=True)
def reset_cache(monkeypatch):
    provisioning.provision_model.cache_clear()
    monkeypatch.delenv('POLISDIFF_PROVISION_MODEL', raising=False)
    yield
    provisioning.provision_model.cache_clear()


def test_default_no_network_even_without_model(monkeypatch):
    monkeypatch.setattr(provisioning, 'model_files_status', lambda: {'state':'not_provisioned'})
    monkeypatch.setattr(subprocess,'run', lambda *a, **k:pytest.fail('Unexpected download'))
    assert provisioning.provision_model() == 'disabled'
    assert provisioning.provisioning_status()['result'] == 'disabled'


def test_preflight_is_read_only_when_operator_enabled(monkeypatch):
    monkeypatch.setenv('POLISDIFF_PROVISION_MODEL','true')
    monkeypatch.setattr(subprocess,'run', lambda *a, **k:pytest.fail('Unexpected download'))
    assert provisioning.provisioning_status()['operator_enabled']
    assert provisioning.provisioning_status()['result'] == 'not_attempted'


@pytest.mark.parametrize('limit', [None, 690*1024**2, 1024*1024**2])
def test_unknown_or_small_budget_abstains(monkeypatch, limit):
    monkeypatch.setenv('POLISDIFF_PROVISION_MODEL','1')
    monkeypatch.setattr(provisioning,'model_files_status', lambda: {'state':'not_provisioned'})
    monkeypatch.setattr(provisioning,'memory_limit', lambda:limit)
    monkeypatch.setattr(subprocess,'run', lambda *a, **k:pytest.fail('Unsafe download'))
    assert provisioning.provision_model() == 'insufficient_or_unknown_memory_budget'


def test_existing_files_never_redownload(monkeypatch):
    monkeypatch.setenv('POLISDIFF_PROVISION_MODEL','1')
    monkeypatch.setattr(provisioning,'model_files_status', lambda: {'state':'files_present'})
    monkeypatch.setattr(subprocess,'run', lambda *a, **k:pytest.fail('Redownload'))
    assert provisioning.provision_model() == 'already_present'


@pytest.mark.parametrize('outcome', ['success','nonzero','timeout','os_error'])
def test_bounded_single_attempt_without_document_bytes(monkeypatch, outcome):
    monkeypatch.setenv('POLISDIFF_PROVISION_MODEL','1')
    monkeypatch.setattr(provisioning,'memory_limit', lambda:3*1024**3)
    monkeypatch.setattr(provisioning,'memory_current', lambda:0)
    calls=[]
    present = False
    monkeypatch.setattr(provisioning,'model_files_status', lambda: {'state':'files_present' if present else 'not_provisioned'})
    def run(command, **kwargs):
        nonlocal present
        calls.append(command)
        assert command[-1].endswith('download_model.py')
        assert kwargs['timeout'] == 180 and kwargs['capture_output']
        assert 'input' not in kwargs
        if outcome == 'timeout':
            raise subprocess.TimeoutExpired(command,180)
        if outcome == 'os_error':
            raise OSError('cannot spawn')
        present = outcome == 'success'
        return SimpleNamespace(returncode=0 if present else 2)
    monkeypatch.setattr(subprocess,'run',run)
    expected={'success':'provisioned','nonzero':'download_failed','timeout':'download_timeout','os_error':'download_failed'}[outcome]
    assert provisioning.provision_model() == expected
    assert provisioning.provision_model() == expected
    assert provisioning.provisioning_status()['result'] == expected
    assert len(calls) == 1


@pytest.mark.parametrize('current', [None, 2500*1024**2])
def test_insufficient_or_unknown_headroom_abstains(monkeypatch, current):
    monkeypatch.setenv('POLISDIFF_PROVISION_MODEL','1')
    monkeypatch.setattr(provisioning,'memory_limit',lambda:3*1024**3)
    monkeypatch.setattr(provisioning,'memory_current',lambda:current)
    monkeypatch.setattr(provisioning,'model_files_status',lambda:{'state':'not_provisioned'})
    monkeypatch.setattr(subprocess,'run',lambda *a,**k:pytest.fail('Unsafe download'))
    assert provisioning.provision_model() == 'insufficient_or_unknown_memory_headroom'


@pytest.mark.parametrize('separator', ['/', '\\'])
def test_linux_and_legacy_windows_manifest_provenance(tmp_path, monkeypatch, separator):
    import polisdiff.retrieval as retrieval
    model = tmp_path/'model'
    records = {}
    for name in ['config.json','model.safetensors','tokenizer.json','1_Pooling/config.json']:
        path = model/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'fixture bytes')
        records[name.replace('/',separator)] = hashlib.sha256(path.read_bytes()).hexdigest()
    (tmp_path/'evaluation').mkdir()
    (tmp_path/'evaluation/model_manifest.json').write_text(json.dumps({'revision':'fixture-revision','files':records}))
    fake_model = SimpleNamespace(max_seq_length=0)
    monkeypatch.setitem(sys.modules,'torch',SimpleNamespace(set_num_threads=lambda _:None))
    monkeypatch.setitem(sys.modules,'sentence_transformers',SimpleNamespace(SentenceTransformer=lambda *a,**k:fake_model))
    monkeypatch.setattr(retrieval,'ROOT',tmp_path)
    retriever = retrieval.Retriever('hybrid',model_path=model)
    assert retriever.model is fake_model
    assert retriever.model_revision == 'fixture-revision'
