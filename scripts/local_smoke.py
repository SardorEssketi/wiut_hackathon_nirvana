"""Cold-start browser checks for unknown dates, historical dates and both AI modes."""
from pathlib import Path
import argparse
import json
import time
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright, expect
from browser_check import set_date, set_mode

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url",default="http://localhost:8501")
    parser.add_argument("--output",default="audit_smoke_results.json")
    args = parser.parse_args()
    rows = []
    dest = ROOT / "local_data" / "browser"
    dest.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(accept_downloads=True)
        page.goto(args.url)
        expect(page.get_by_role("heading",name="Условия полиса, с доказательствами")).to_be_visible(timeout=60000)
        page.locator('input[type=file]').set_input_files(str(ROOT/'tests/fixtures/evaluation/uz-Cyrl_historic.pdf'))

        def analyze(key, expected, mode, applicable):
            time.sleep(5.1)
            expect(page.get_by_role("button",name="Анализировать документ",exact=True)).to_be_enabled()
            page.get_by_role("button",name="Анализировать документ",exact=True).click()
            export = page.get_by_role("button",name="Скачать JSON отчет",exact=True)
            expect(export).to_be_visible(timeout=180000)
            with page.expect_download() as event:
                export.click()
            target = dest/f"{key}.json"
            event.value.save_as(str(target))
            report = json.loads(target.read_text(encoding="utf-8"))
            assert [f['status'] for f in report['findings']] == expected
            assert report['retrieval_used'] == mode
            assert report['applicable_date'] == applicable
            assert page.get_by_test_id('stException').count() == 0
            rows.append({'id':key,'mode':mode,'applicable_date':applicable,
                         'statuses':expected,'timings_seconds':report['timings_seconds']})

        analyze('unknown_date',['UNVERIFIABLE']*3,'hybrid',None)
        page.get_by_text("Я подтверждаю дату применимости договора",exact=True).click()
        set_date(page, 'Дата применимости договора', '2026-01-05')
        expect(page.get_by_role('button',name='Скачать JSON отчет',exact=True)).to_have_count(0,timeout=30000)
        analyze('historical_pdf_current_date',['POTENTIAL_CONFLICT','MATCH_FOUND','MATCH_FOUND'],'hybrid','2026-01-05')
        for field,value in zip(('year','month','day'),('2024','09','06')):
            control = page.get_by_role('spinbutton',name=f'{field}, Дата аудита',exact=True)
            control.fill(value)
            control.press('Tab')
            page.wait_for_timeout(750)
            expect(page.get_by_test_id('stApp')).to_have_attribute('data-test-script-state','notRunning',timeout=30000)
        for field,value in zip(('year','month','day'),('2024','09','06')):
            control = page.get_by_role('spinbutton',name=f'{field}, Дата применимости договора',exact=True)
            control.fill(value)
            control.press('Tab')
            page.wait_for_timeout(750)
            expect(page.get_by_test_id('stApp')).to_have_attribute('data-test-script-state','notRunning',timeout=30000)
        set_mode(page, 'AI поиск')
        expect(page.get_by_role('button',name='Скачать JSON отчет',exact=True)).to_have_count(0,timeout=30000)
        analyze('historical_date',['MATCH_FOUND']*3,'semantic','2024-09-06')
        browser.close()
    result = {'checked_at':datetime.now(timezone.utc).isoformat(),'url':args.url,'success':True,
              'public_deployment_tested':False,'cases':rows}
    (ROOT/'evaluation'/args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Verified unknown-date abstention, historical version and semantic/hybrid web modes.')


if __name__ == '__main__':
    main()
