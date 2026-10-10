"""Host-side isolated Docker verification; writes only a compact result artifact."""
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def main():
    command = ["docker","run","--rm","--network","none","--memory","3g","--cpus","2",
        "--read-only","--tmpfs","/tmp:rw,size=128m,mode=1777","--pids-limit","128",
        "--security-opt","no-new-privileges:true","--cap-drop","ALL",
        "--mount",f"type=bind,source={ROOT/'tests/fixtures'},target=/fixtures,readonly",
        "--mount",f"type=bind,source={ROOT/'local_data/sources'},target=/sources,readonly",
        "polisdiff-ai:local","python","scripts/container_check.py"]
    process = subprocess.run(command,capture_output=True,text=True,encoding="utf-8",timeout=360)
    if process.returncode:
        print(process.stderr[-3000:])
        raise SystemExit(process.returncode)
    result = json.loads(process.stdout)
    (ROOT/"evaluation/container_results.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Container analysis verified:",len(result["cases"]),"PDFs; peak main-process RSS",round(result["peak_main_process_rss_mib"],1),"MiB")

if __name__ == "__main__":
    main()
