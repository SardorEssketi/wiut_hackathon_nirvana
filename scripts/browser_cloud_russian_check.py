"""Actual public Cloud Russian pending-date UX, original GROSS evidence and exports."""
import json
import sys
from pathlib import Path
from html import unescape
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright, expect
from scripts.browser_cloud_readiness_check import connect, ROOT
from scripts.browser_check import settled
from scripts.browser_i18n_check import choose_language
from polisdiff.models import Report
from polisdiff.presentation import readiness_message, summary
from polisdiff.i18n import tr

dest=ROOT/'local_data/cloud_russian_browser'
dest.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch()
    context=browser.new_context(viewport={'width':1365,'height':950},accept_downloads=True)
    app=connect(context,'https://polis-diff-ai.streamlit.app/')
    choose_language(app,'ru')
    expect(app.get_by_text(readiness_message('ru'),exact=True)).to_have_count(1)
    app.locator('input[type=file]').set_input_files(str(ROOT/'local_data/sources/gross_latin.pdf'))
    expect(app.get_by_role('button',name='Remove gross_latin.pdf',exact=True)).to_be_visible(timeout=120000)
    settled(app)
    app.get_by_role('button',name=tr('Анализировать документ'),exact=True).click()
    expect(app.get_by_role('button',name=tr('Скачать JSON отчет'),exact=True)).to_be_visible(timeout=240000)
    settled(app)
    with app.expect_download(timeout=60000) as event:
        app.get_by_role('button',name=tr('Скачать JSON отчет'),exact=True).click()
    event.value.save_as(str(dest/'report.json'))
    report=Report.model_validate_json((dest/'report.json').read_bytes())
    assert report.applicable_date is None and all(f.status.value=='UNVERIFIABLE' for f in report.findings)
    expect(app.get_by_text(readiness_message('ru'),exact=True)).to_have_count(1)
    expect(app.get_by_text('Ожидает подтверждения даты',exact=True)).to_have_count(3)
    app.get_by_role('heading',name='4. Проверки условий',exact=True).scroll_into_view_if_needed()
    app.screenshot(path=str(dest/'pending-desktop.png'),full_page=True)
    app.set_viewport_size({'width':390,'height':844})
    app.wait_for_timeout(700)
    app.get_by_role('heading',name='4. Проверки условий',exact=True).scroll_into_view_if_needed()
    assert app.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    app.screenshot(path=str(dest/'pending-mobile.png'),full_page=True)
    with app.expect_download(timeout=60000) as event:
        app.get_by_role('button',name=tr('Скачать HTML отчет'),exact=True).click()
    event.value.save_as(str(dest/'report.html'))
    html=(dest/'report.html').read_text(encoding='utf-8')
    assert summary(report) in unescape(html)
    assert all(ev.quote in unescape(html) for f in report.findings for ev in f.evidence)
    evidence_count=sum(len(f.evidence) for f in report.findings)
    (dest/'results.json').write_text(json.dumps({'success':True,'ui_language':'ru','statuses':[f.status.value for f in report.findings],'retrieval_used':report.retrieval_used,'evidence_count':evidence_count,'original_quotes_preserved':True,'pending_checks':3,'shared_date_warning':1,'mobile_overflow_px':0},indent=2),encoding='utf-8')
    print(f'Russian Cloud desktop/mobile and three compact pending checks verified; {evidence_count} evidence quotations, no invented locations.')
    browser.close()
