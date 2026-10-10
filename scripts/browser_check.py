"""Actual localhost UX, evidence, session isolation and print/export regression journeys."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys
import time
from urllib.request import urlopen
import pymupdf
from playwright.sync_api import sync_playwright, expect
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.generate_fixtures import create_pdf
from polisdiff.extraction import extract_pdf
from polisdiff.models import Report
from polisdiff.presentation import summary, STATUS_LABELS

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'local_data/audit_browser'


def settled(page):
    expect(page.get_by_test_id('stApp')).to_have_attribute('data-test-script-state','notRunning',timeout=180000)
    expect(page.get_by_test_id('stException')).to_have_count(0)


def set_date(page, label, value):
    for part, content in zip(('year','month','day'), value.split('-')):
        control = page.get_by_role('spinbutton',name=f'{part}, {label}',exact=True)
        if control.inner_text() != content:
            control.fill(content)
            control.press('Tab')
            page.wait_for_timeout(400)
            settled(page)


def download_report(page, key):
    with page.expect_download() as event:
        page.get_by_role('button',name='Скачать JSON отчет',exact=True).click()
    path = DEST / f'{key}.json'
    event.value.save_as(str(path))
    return Report.model_validate_json(path.read_bytes())


def analyze(page, key, expected=None, actual_mode='hybrid'):
    # Actual application cooldown, not an invented progress indicator.
    page.wait_for_timeout(5100)
    page.get_by_role('button',name='Анализировать документ',exact=True).click()
    expect(page.get_by_role('button',name='Скачать JSON отчет',exact=True)).to_be_visible(timeout=180000)
    settled(page)
    report = download_report(page,key)
    assert report.retrieval_used == actual_mode, report.warnings
    if expected:
        assert [f.status.value for f in report.findings] == expected
    expect(page.get_by_text(summary(report),exact=True)).to_be_visible()
    for f in report.findings:
        expect(page.get_by_text(f'{ {"MATCH_FOUND":"✓", "POTENTIAL_CONFLICT":"!", "NOT_FOUND":"?", "UNVERIFIABLE":"—"}[f.status.value]} {STATUS_LABELS[f.status]}',exact=True).first).to_be_visible()
    return report


def no_result(page):
    expect(page.get_by_role('button',name='Скачать JSON отчет',exact=True)).to_have_count(0,timeout=30000)
    settled(page)


def set_mode(page, label):
    choice = page.get_by_text(label,exact=True)
    if not choice.is_visible():
        page.get_by_text('Дополнительные настройки поиска',exact=True).click()
    choice.click()
    expect(page.get_by_role('radio',name=label,exact=True)).to_be_checked()
    settled(page)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url',default='http://localhost:8501')
    parser.add_argument('--output',default='audit_browser_results.json')
    parser.add_argument('--only',nargs='+')
    args = parser.parse_args()
    for attempt in range(30):
        try:
            with urlopen(args.url + '/_stcore/health', timeout=1) as response:
                if response.status == 200:
                    break
        except OSError:
            time.sleep(1)
    else:
        raise RuntimeError('Local Streamlit health endpoint did not become ready')
    DEST.mkdir(parents=True,exist_ok=True)
    unseen = DEST/'independent-audit.pdf'
    create_pdf(unseen, [["Новый тест для аудита. ОСАГО. 19.03.2026."],
        ["Общая страховая сумма установлена в размере 62 345 678 сум."],
        ["Страховое возмещение перечисляется получателю в срок 9 рабочих дней после принятия решения страховщиком."],
        ["Страхователю сообщается решение о страховом возмещении через 12 дней после письменного заявления."]])
    results = {'checked_at':datetime.now(timezone.utc).isoformat(),'url':args.url,
               'public_deployment_tested':False,'cases':[],'errors':[],'external_requests':[]}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width':1365,'height':950},accept_downloads=True)
        page = context.new_page()
        page.on('pageerror',lambda error:results['errors'].append(str(error)))
        page.on('request',lambda request:results['external_requests'].append(request.url.split('?')[0]) if
                not request.url.startswith((args.url,args.url.replace('http:','ws:'),'data:','blob:')) else None)
        page.goto(args.url,wait_until='networkidle')
        expect(page.get_by_role('heading',name='Условия полиса, с доказательствами')).to_be_visible(timeout=60000)
        settled(page)
        page.screenshot(path=str(DEST/'initial-desktop.png'),full_page=True)
        expect(page.get_by_role('button',name='Анализировать документ',exact=True)).to_be_disabled()
        expect(page.get_by_text('Дата договора неизвестна или не указана.',exact=False)).to_be_visible()
        page.get_by_text('Я подтверждаю дату применимости договора',exact=True).click()
        expect(page.get_by_role('checkbox',name='Я подтверждаю дату применимости договора')).to_be_checked()
        set_date(page,'Дата применимости договора','2026-01-05')
        cases = [(f'synthetic_{lang}',ROOT/f'tests/fixtures/evaluation/{lang}_sum_conflict.pdf',
                  ['POTENTIAL_CONFLICT','MATCH_FOUND','MATCH_FOUND']) for lang in ['uz-Latn','uz-Cyrl','ru-Cyrl']]
        cases += [('independent_browser',unseen,['POTENTIAL_CONFLICT','POTENTIAL_CONFLICT','MATCH_FOUND'])]
        cases += [(key,ROOT/f'local_data/sources/{key}.pdf',None) for key in ['gross_latin','gross_cyrillic','inson_russian']]
        if args.only:
            cases = [c for c in cases if c[0] in args.only]
            assert cases, 'No selected cases'
        previous = None
        for key,path,statuses in cases:
            if previous:
                page.get_by_role('button',name=f'Remove {previous.name}',exact=True).click()
                expect(page.get_by_role('button',name='Анализировать документ',exact=True)).to_be_disabled(timeout=30000)
                no_result(page)
            applicable = {'gross_cyrillic':'2024-09-06','inson_russian':'2026-01-15','independent_browser':'2026-03-19'}.get(key,'2026-01-05')
            set_date(page,'Дата применимости договора',applicable)
            page.locator('input[type=file]').set_input_files(str(path))
            settled(page)
            no_result(page)
            previous = path
            report = analyze(page,key,statuses)
            doc = extract_pdf(path.read_bytes())
            assert report.document_sha256 == doc.sha256
            assert str(report.applicable_date) == applicable and not report.reviews
            for f in report.findings:
                assert f.reviewer_status == 'PENDING_LEGAL_REVIEW'
                for ev in f.evidence:
                    assert ev.quote == doc.pages[ev.page-1].text[ev.start:ev.end]
            results['cases'].append({'id':key,'statuses':[f.status.value for f in report.findings],
                'page_count':report.page_count,'retrieval_used':report.retrieval_used,
                'applicable_date':applicable,'evidence_verified':True,'timings_seconds':report.timings_seconds})
            print(key, 'passed', [f.status.value for f in report.findings],flush=True)
            if key.startswith('synthetic_') or key == 'independent_browser':
                page.set_viewport_size({'width':390,'height':844})
                page.get_by_role('heading',name='2. Краткий итог').scroll_into_view_if_needed()
                page.wait_for_timeout(600)
                overflow = page.evaluate('Math.max(0,document.documentElement.scrollWidth-window.innerWidth)')
                assert overflow == 0, overflow
                page.screenshot(path=str(DEST/f'{key}-mobile.png'))
                results['cases'][-1]['mobile_horizontal_overflow_px'] = overflow
                page.set_viewport_size({'width':1365,'height':950})
            if key == 'independent_browser':
                page.get_by_role('tab',name='Решение аналитика').click()
                for rationale in ['Original audit review <script>attack</script> Суғурта sugʻurta.', 'Second annotation; original statuses retained.']:
                    page.get_by_role('textbox',name='Обоснование').fill(rationale)
                    page.get_by_role('button',name='Записать решение',exact=True).click()
                    settled(page)
                    page.get_by_role('tab',name='Решение аналитика').click()
                    expect(page.get_by_text(rationale,exact=True).last).to_be_visible()
                page.get_by_role('tab',name='Результаты',exact=True).click()
                reviewed = download_report(page,'reviewed')
                assert len(reviewed.reviews) == 2
                assert reviewed.findings == report.findings
                with page.expect_download() as event:
                    page.get_by_role('button',name='Скачать HTML отчет',exact=True).click()
                html_path = DEST/'reviewed.html'
                event.value.save_as(str(html_path))
                html = html_path.read_text(encoding='utf-8')
                assert '<script>' not in html and '&lt;script&gt;' in html
                assert summary(reviewed) in html
                export_page = context.new_page()
                export_requests = []
                export_page.on('request',lambda req:export_requests.append(req.url))
                export_page.set_content(html,wait_until='networkidle')
                expect(export_page.get_by_role('heading',name='Краткий итог')).to_be_visible()
                for ev in reviewed.findings[0].evidence:
                    expect(export_page.locator('blockquote').filter(has_text=ev.quote.strip())).to_have_count(1)
                export_page.screenshot(path=str(DEST/'html-desktop.png'),full_page=True)
                export_page.emulate_media(media='print')
                printed = DEST/'reviewed-print.pdf'
                export_page.pdf(path=str(printed),format='A4',prefer_css_page_size=True,print_background=True)
                with pymupdf.open(printed) as pdf:
                    print_text = '\n'.join(pg.get_text() for pg in pdf)
                    assert len(pdf) >= 2 and all(abs(pg.rect.width-595.28)<2 for pg in pdf)
                    assert '62 345 678' in print_text and 'Original audit review' in print_text
                    first = pdf[0].get_pixmap()
                    first.save(str(DEST/'print-first-page.png'))
                assert not export_requests
                export_page.close()
                results['review_export_and_a4_print_verified'] = True
                ev = reviewed.findings[0].evidence[0]
                page.get_by_role('button',name=f'Посмотреть доказательство · стр. {ev.page}',exact=True).first.click()
                settled(page)
                viewer = page.get_by_text('Выбранное доказательство в PDF',exact=True)
                viewer.scroll_into_view_if_needed()
                expect(page.locator('[data-testid=stImage] img').first).to_be_visible(timeout=30000)
                expect(page.get_by_test_id('stExpander').filter(has_text='Выбранное доказательство в PDF').get_by_text(f'Страница PDF {ev.page} · Текст оферты',exact=False)).to_be_visible()
                page.screenshot(path=str(DEST/'evidence-desktop.png'))
                results['evidence_navigation_verified'] = True
                page.get_by_role('heading',name='2. Краткий итог').scroll_into_view_if_needed()
                page.screenshot(path=str(DEST/'results-desktop.png'))
                # Another independent browser session cannot see this report or annotations.
                other = browser.new_context()
                other_page = other.new_page()
                other_page.goto(args.url,wait_until='networkidle')
                no_result(other_page)
                other_page.locator('input[type=file]').set_input_files(str(ROOT/'tests/fixtures/evaluation/uz-Latn_match.pdf'))
                other_report = analyze(other_page,'separate_session',['UNVERIFIABLE']*3)
                assert not other_report.reviews and other_report.document_sha256 != report.document_sha256
                other.close()
                results['browser_session_isolation_verified'] = True
                # Changing either date, mode or date confirmation invalidates all exports/reviews.
                set_date(page,'Дата аудита','2026-10-09')
                no_result(page)
                set_mode(page,'Лексический поиск')
                no_result(page)
                rerun = analyze(page,'changed_config',statuses,actual_mode='lexical')
                assert not rerun.reviews and str(rerun.audit_date) == '2026-10-09'
                page.get_by_role('tab',name='Решение аналитика').click()
                expect(page.get_by_role('textbox',name='Обоснование')).to_have_value('')
                page.get_by_role('tab',name='Результаты',exact=True).click()
                page.get_by_text('Я подтверждаю дату применимости договора',exact=True).click()
                expect(page.get_by_role('checkbox',name='Я подтверждаю дату применимости договора')).not_to_be_checked()
                no_result(page)
                unknown = analyze(page,'unknown_date',['UNVERIFIABLE']*3,actual_mode='lexical')
                assert unknown.applicable_date is None and not unknown.reviews
                results['configuration_invalidation_and_unknown_date_verified'] = True
                page.get_by_text('Я подтверждаю дату применимости договора',exact=True).click()
                set_date(page,'Дата аудита','2026-10-10')
                set_mode(page,'AI + лексический поиск')
                settled(page)
        # Historic PDF / source version, and real semantic mode through the browser.
        if previous:
            page.get_by_role('button',name=f'Remove {previous.name}',exact=True).click()
            no_result(page)
        historic = ROOT/'tests/fixtures/evaluation/uz-Cyrl_historic.pdf'
        page.locator('input[type=file]').set_input_files(str(historic))
        set_date(page,'Дата аудита','2024-09-06')
        set_date(page,'Дата применимости договора','2024-09-06')
        set_mode(page,'AI поиск')
        historical = analyze(page,'historical',['MATCH_FOUND']*3,actual_mode='semantic')
        assert historical.findings[0].expected_value == 40000000
        results['historical_and_semantic_verified'] = True
        page.get_by_role('button',name='Очистить сессию',exact=True).click()
        expect(page.get_by_role('button',name='Анализировать документ',exact=True)).to_be_disabled(timeout=30000)
        no_result(page)
        expect(page.get_by_role('checkbox',name='Я подтверждаю дату применимости договора')).not_to_be_checked()
        # Original document uploaded again after clearing has no resurrected annotations.
        page.locator('input[type=file]').set_input_files(str(unseen))
        again = analyze(page,'after_clear',['UNVERIFIABLE']*3)
        assert not again.reviews
        page.get_by_role('tab',name='Решение аналитика').click()
        expect(page.get_by_role('textbox',name='Обоснование')).to_have_value('')
        page.get_by_role('button',name='Очистить сессию',exact=True).click()
        no_result(page)
        assert not results['errors'],results['errors']
        assert not results['external_requests'],results['external_requests']
        results['session_clear_and_reupload_verified'] = True
        context.close()
        browser.close()
    results['success'] = True
    (ROOT/'evaluation'/args.output).write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Verified desktop/mobile, real/synthetic PDFs, dates, reviews, evidence, isolated sessions and A4 HTML printing.')


if __name__ == '__main__':
    main()
