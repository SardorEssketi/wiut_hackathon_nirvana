"""Record only local image identity, health and measured resource counters."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def command(*args):
    return subprocess.check_output(args,cwd=ROOT,text=True,encoding="utf-8").strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--container",required=True)
    args = parser.parse_args()
    check = json.loads((ROOT/'evaluation/container_results.json').read_text(encoding='utf-8'))
    matches = {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
               for name,digest in check['source_code_sha256'].items()}
    assert all(matches.values()),matches
    commit=command('git','-c',f'safe.directory={ROOT.as_posix()}','rev-parse','HEAD')
    committed_matches={name:hashlib.sha256(subprocess.check_output(
        ['git','-c',f'safe.directory={ROOT.as_posix()}','show',f'{commit}:{name}'],cwd=ROOT)).hexdigest()==digest
        for name,digest in check['source_code_sha256'].items()}
    assert all(committed_matches.values()),committed_matches
    container = json.loads(command('docker','inspect',args.container))[0]
    image = json.loads(command('docker','image','inspect',container['Image']))[0]
    events = dict(line.split() for line in command('docker','exec',args.container,'cat','/sys/fs/cgroup/memory.events').splitlines())
    health = container['State']['Health']['Status']
    assert health == 'healthy',health
    assert events.get('oom_kill') == '0',events
    result = {'recorded_at':datetime.now(timezone.utc).isoformat(),
              'source_commit':commit,
              'scope':'local verification only','submission_ready':False,'public_deployment_tested':False,
              'image_id':image['Id'],'image_size_bytes':image['Size'],
              'container_name':container['Name'].lstrip('/'),'health':health,
              'non_root_user':container['Config']['User'],
              'configured_port':next(v.split('=',1)[1] for v in container['Config']['Env'] if v.startswith('PORT=')),
              'memory_limit_bytes':container['HostConfig']['Memory'],
              'service_cgroup_peak_memory_bytes':int(command('docker','exec',args.container,'cat','/sys/fs/cgroup/memory.peak')),
              'memory_events':{key:int(value) for key,value in events.items()},
              'read_only_root':container['HostConfig']['ReadonlyRootfs'],
              'offline_pipeline_check':check['success'],'source_hash_matches_container':matches,
              'committed_source_hash_matches_container':committed_matches,
              'tested_source_sha256':check['source_code_sha256']}
    (ROOT/'evaluation/local_release_manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Local image identity, source hashes, health and resource counters verified.')


if __name__=='__main__':
    main()
