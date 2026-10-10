"""A real browser verifies explicit lexical fallback in a separate local server."""
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import socket
import subprocess
import sys
import time
from urllib.request import urlopen
from playwright.sync_api import sync_playwright, expect
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from polisdiff.models import Report

ROOT = Path(__file__).resolve().parents[1]


def main():
    dest = ROOT/'local_data/audit_fallback'
    dest.mkdir(parents=True,exist_ok=True)
    with socket.socket() as port_probe:
        port_probe.bind(('127.0.0.1',0))
        port = port_probe.getsockname()[1]
    url = f'http://127.0.0.1:{port}'
    env = os.environ.copy()
    env['POLISDIFF_MODEL_PATH'] = str(dest/'intentionally_absent_model')
    process = subprocess.Popen([sys.executable,'-m','streamlit','run','app.py',
        '--server.address=127.0.0.1',f'--server.port={port}','--server.headless=true'],
        cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
    try:
        for _ in range(30):
            if process.poll() is not None:
                raise RuntimeError('Fallback test server exited')
            try:
                with urlopen(url+'/_stcore/health',timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(1)
        else:
            raise RuntimeError('Fallback server not ready')
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(accept_downloads=True)
            page.goto(url,wait_until='networkidle')
            page.locator('input[type=file]').set_input_files(str(ROOT/'tests/fixtures/evaluation/uz-Latn_match.pdf'))
            page.get_by_role('button',name='Анализировать документ',exact=True).click()
            button = page.get_by_role('button',name='Скачать JSON отчет',exact=True)
            expect(button).to_be_visible(timeout=60000)
            expect(page.get_by_test_id('stException')).to_have_count(0)
            expect(page.get_by_text('AI-модель недоступна.',exact=False)).to_be_visible()
            with page.expect_download() as event:
                button.click()
            path = dest/'report.json'
            event.value.save_as(str(path))
            report = Report.model_validate_json(path.read_bytes())
            assert report.retrieval_requested == 'hybrid' and report.retrieval_used == 'lexical'
            assert report.model_revision is None
            assert any('lexical fallback' in w for w in report.warnings)
            assert all(f.status.value == 'UNVERIFIABLE' for f in report.findings)
            page.get_by_role('heading',name='2. Краткий итог').scroll_into_view_if_needed()
            page.screenshot(path=str(dest/'fallback.png'))
            browser.close()
        result={'checked_at':datetime.now(timezone.utc).isoformat(),'success':True,
            'requested':'hybrid','used':'lexical','visible_warning_verified':True,
            'public_deployment_tested':False}
        (ROOT/'evaluation/audit_fallback_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print('Actual fallback browser/server verified; temporary server stopped.')
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == '__main__':
    main()
