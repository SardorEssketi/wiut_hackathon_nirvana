"""Actual localhost translation, language-switch state and multilingual export journeys."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import sys
import time
from html import unescape
from urllib.request import urlopen
import pymupdf
from playwright.sync_api import sync_playwright, expect
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from polisdiff.i18n import LANGUAGES, tr
from polisdiff.models import Report
from polisdiff.presentation import summary, labels, STATUS_LABELS, rule_name
from scripts.browser_check import settled, set_date, click_tab

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT/'local_data/i18n_browser'
LABEL = 'Language / Til / Тил / Язык'


def open_sidebar(page):
    control = page.get_by_role('combobox',name=LABEL,exact=True)
    sidebar = page.get_by_test_id('stSidebar')
    if sidebar.get_attribute('aria-expanded') != 'true':
        page.get_by_test_id('stExpandSidebarButton').click()
    expect(sidebar).to_have_attribute('aria-expanded','true')
    expect(control).to_be_in_viewport()


def choose_language(page,language):
    open_sidebar(page)
    control = page.get_by_role('combobox',name=LABEL,exact=True)
    control.click()
    page.get_by_role('option',name=LANGUAGES[language],exact=True).click()
    settled(page)
    if page.viewport_size['width'] < 640:
        page.get_by_test_id('stSidebarCollapseButton').click()
        expect(page.get_by_test_id('stSidebar')).to_have_attribute('aria-expanded','false')
    expect(page.get_by_role('heading',name=tr('Условия полиса, с доказательствами',language),exact=True)).to_be_visible()


def download(page,language,kind,key):
    with page.expect_download() as event:
        page.get_by_role('button',name=tr(f'Скачать {kind} отчет',language),exact=True).click()
    path = DEST/f'{key}.{kind.lower()}'
    event.value.save_as(str(path))
    return path


def analyze(page,language,key):
    page.wait_for_timeout(5100)
    page.get_by_role('button',name=tr('Анализировать документ',language),exact=True).click()
    expect(page.get_by_role('button',name=tr('Скачать JSON отчет',language),exact=True)).to_be_visible(timeout=180000)
    settled(page)
    report = Report.model_validate_json(download(page,language,'JSON',key).read_bytes())
    expect(page.get_by_text(summary(report,language),exact=True)).to_be_visible()
    for f in report.findings:
        expect(page.get_by_text(labels(STATUS_LABELS,language)[f.status],exact=False).first).to_be_visible()
    return report


def overflow(page):
    return page.evaluate('Math.max(0,document.documentElement.scrollWidth-window.innerWidth)')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url',default='http://localhost:8501')
    parser.add_argument('--output',default='i18n_browser_results.json')
    parser.add_argument('--artifact-dir',default=None)
    args = parser.parse_args()
    global DEST
    if args.artifact_dir:
        DEST = ROOT / args.artifact_dir
    for _ in range(30):
        try:
            with urlopen(args.url+'/_stcore/health',timeout=1) as response:
                if response.status == 200:
                    break
        except OSError:
            time.sleep(1)
    else:
        raise RuntimeError('Streamlit is unavailable')
    DEST.mkdir(parents=True,exist_ok=True)
    results={'checked_at':datetime.now(timezone.utc).isoformat(),'cases':[],'errors':[],'external_requests':[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        context=browser.new_context(viewport={'width':1365,'height':950},accept_downloads=True)
        page=context.new_page()
        page.on('pageerror',lambda error:results['errors'].append(str(error)))
        page.on('request',lambda request:results['external_requests'].append(request.url) if not
            request.url.startswith((args.url,args.url.replace('http:','ws:'),'data:','blob:')) else None)
        page.goto(args.url,wait_until='networkidle')
        settled(page)
        expect(page.get_by_role('heading',name=tr('Условия полиса, с доказательствами'),exact=True)).to_be_visible()
        for language in ['uz-Latn','uz-Cyrl','en']:
            choose_language(page,language)
            expect(page.get_by_text(tr('Дата договора неизвестна или не указана. Можно найти связанный текст, но все три числовые проверки останутся без вывода о соответствии.',language),exact=True)).to_be_visible()
            page.get_by_text(tr('Я подтверждаю дату применимости договора',language),exact=True).click()
            set_date(page,tr('Дата применимости договора',language),'2026-01-05')
            page.get_by_text(tr('Дополнительные настройки поиска',language),exact=True).click()
            page.get_by_text(tr('Лексический поиск',language),exact=True).click()
            settled(page)
            for script in ['uz-Latn','uz-Cyrl','ru-Cyrl']:
                path=ROOT/f'tests/fixtures/evaluation/{script}_sum_conflict.pdf'
                page.locator('input[type=file]').set_input_files(str(path))
                settled(page)
                key=f'{language}_{script}'
                report=analyze(page,language,key)
                assert report.document_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
                assert report.retrieval_requested == report.retrieval_used == 'lexical'
                assert [f.status.value for f in report.findings] == ['POTENTIAL_CONFLICT','MATCH_FOUND','MATCH_FOUND']
                html_path=download(page,language,'HTML',key)
                html=html_path.read_text(encoding='utf-8')
                assert f'<html lang="{language}"' in html
                assert summary(report,language) in unescape(html)
                assert all(ev.quote in unescape(html) for f in report.findings for ev in f.evidence)
                assert all(f.source_quote in unescape(html) for f in report.findings)
                assert overflow(page) == 0
                page.screenshot(path=str(DEST/f'{key}-desktop.png'),full_page=True)
                page.set_viewport_size({'width':390,'height':844})
                assert overflow(page) == 0
                page.screenshot(path=str(DEST/f'{key}-mobile.png'),full_page=True)
                ev=report.findings[0].evidence[0]
                page.get_by_role('button',name=tr('Открыть в PDF · стр. {page}',language,page=ev.page),exact=True).first.click()
                settled(page)
                active_results=page.get_by_role('tabpanel',name=tr('Результаты',language),exact=True)
                viewer=active_results.locator('[data-testid="stExpander"]').filter(has=page.locator(':scope > details > summary').get_by_text(tr('Выбранное доказательство в PDF',language),exact=True))
                expect(viewer).to_have_count(1)
                expect(viewer.get_by_text(tr('Цитата выбранной находки',language),exact=True)).to_be_visible()
                expect(viewer.get_by_test_id('stImage')).to_have_count(1)
                expect(viewer.get_by_test_id('stImage')).to_be_visible()
                expect(viewer.get_by_text(tr('Страница PDF {page}',language,page=ev.page),exact=False)).to_be_visible()
                assert overflow(page) == 0
                page.screenshot(path=str(DEST/f'{key}-evidence-mobile.png'),full_page=True)
                page.set_viewport_size({'width':1365,'height':950})
                results['cases'].append({'ui_language':language,'document_script':script,'sha256':report.document_sha256,
                    'statuses':[f.status.value for f in report.findings],'desktop_mobile_overflow_px':0})
                print(key,'verified',flush=True)
            # Annotate, then switch all languages without reanalysis or changed dates/mode.
            click_tab(page,tr('Решение аналитика',language))
            page.get_by_role('combobox',name=tr('Проверка',language),exact=True).click()
            page.get_by_role('option',name=rule_name(report.findings[1],language),exact=True).click()
            page.get_by_role('combobox',name=tr('Действие',language),exact=True).click()
            page.get_by_role('option',name=tr('Подтвердить находку',language),exact=True).click()
            rationale='Ўзбекча izoh & English <script>literal</script>'
            page.get_by_role('textbox',name=tr('Обоснование',language),exact=True).fill(rationale)
            page.get_by_role('button',name=tr('Записать решение',language),exact=True).click()
            settled(page)
            click_tab(page,tr('Результаты',language))
            original=Report.model_validate_json(download(page,language,'JSON',f'{language}-reviewed').read_bytes())
            assert len(original.reviews) == 1 and original.reviews[0].rationale == rationale
            assert original.reviews[0].rule_id == 'OSAGO_PAYMENT' and original.reviews[0].action == 'confirm'
            for target in LANGUAGES:
                choose_language(page,target)
                expect(page.get_by_text(summary(original,target),exact=True)).to_be_visible()
                current=Report.model_validate_json(download(page,target,'JSON',f'{language}-switch-{target}').read_bytes())
                assert current == original
                html=download(page,target,'HTML',f'{language}-switch-{target}').read_text(encoding='utf-8')
                assert rationale in unescape(html) and '<script>literal' not in html
                click_tab(page,tr('Решение аналитика',target))
                expect(page.get_by_role('combobox',name=tr('Проверка',target),exact=True)).to_have_value(rule_name(report.findings[1],target))
                expect(page.get_by_role('combobox',name=tr('Действие',target),exact=True)).to_have_value(tr('Подтвердить находку',target))
                expect(page.get_by_role('textbox',name=tr('Обоснование',target),exact=True)).to_have_value(rationale)
                click_tab(page,tr('Результаты',target))
            choose_language(page,language)
            page.set_viewport_size({'width':390,'height':844})
            # Wait for Streamlit's responsive resize to finish collapsing the sidebar.
            expect(page.get_by_test_id('stSidebar')).to_have_attribute('aria-expanded','false')
            choose_language(page,'en' if language != 'en' else 'uz-Cyrl')
            mobile_language='en' if language != 'en' else 'uz-Cyrl'
            assert Report.model_validate_json(download(page,mobile_language,'JSON',f'{language}-mobile-switch').read_bytes()) == original
            assert overflow(page) == 0
            choose_language(page,language)
            page.set_viewport_size({'width':1365,'height':950})
            # Unknown-date abstention and a clear retain language but discard reports/reviews.
            page.get_by_text(tr('Я подтверждаю дату применимости договора',language),exact=True).click()
            settled(page)
            expect(page.get_by_role('button',name=tr('Скачать JSON отчет',language),exact=True)).to_have_count(0)
            unknown=analyze(page,language,f'{language}-unknown')
            assert all(f.status.value == 'UNVERIFIABLE' for f in unknown.findings) and unknown.applicable_date is None
            open_sidebar(page)
            page.get_by_role('button',name=tr('Очистить сессию',language),exact=True).click()
            settled(page)
            expect(page.get_by_role('heading',name=tr('Условия полиса, с доказательствами',language),exact=True)).to_be_visible()
            expect(page.get_by_role('button',name=tr('Анализировать документ',language),exact=True)).to_be_disabled()
        # The interface preference is session-local.
        other=browser.new_context(viewport={'width':1365,'height':950})
        other_page=other.new_page()
        other_page.goto(args.url,wait_until='networkidle')
        settled(other_page)
        expect(other_page.get_by_role('heading',name=tr('Условия полиса, с доказательствами'),exact=True)).to_be_visible()
        expect(other_page.get_by_role('button',name=tr('Скачать JSON отчет'),exact=True)).to_have_count(0)
        other.close()
        # Print every language's downloaded self-contained HTML to actual A4.
        for language in ['uz-Latn','uz-Cyrl','en']:
            print_context=browser.new_context()
            preview=print_context.new_page()
            external=[]
            preview.on('request',lambda request:external.append(request.url) if not request.url.startswith(('file:','data:')) else None)
            preview.goto((DEST/f'{language}-switch-{language}.html').as_uri())
            preview.emulate_media(media='print')
            output=DEST/f'{language}-print.pdf'
            preview.pdf(path=str(output),prefer_css_page_size=True,print_background=True)
            with pymupdf.open(output) as pdf:
                assert abs(pdf[0].rect.width-595.28)<2 and abs(pdf[0].rect.height-841.89)<2
                text='\n'.join(p.get_text() for p in pdf)
                assert '80 000 000' in text and 'literal' in text and 'PENDING_LEGAL_REVIEW' in text
                first=pdf[0].get_pixmap(matrix=pymupdf.Matrix(1,1))
                first.save(DEST/f'{language}-print-first-page.png')
            assert not external
            print_context.close()
        assert not results['errors'] and not results['external_requests'],results
        results.update(success=True,language_switch_preserves_report_reviews=True,unknown_date_abstention=True,
            session_local_language=True,print_a4_all_languages=True)
        context.close()
        browser.close()
    (ROOT/'evaluation'/args.output).write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print('All three new interface languages, document scripts, desktop/mobile, state and A4 exports verified.')


if __name__ == '__main__':
    main()
