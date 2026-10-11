"""Real Cloud/local Chromium journeys. Saves actual revision and execution mode.

Cloud renders the Streamlit app inside an iframe; browser-level downloads and
screenshots belong to the outer page. No owner credentials or private logs used.
"""
import argparse
from datetime import datetime, timezone
from html import unescape
from io import BytesIO
import json
from pathlib import Path
import sys
from urllib.parse import urljoin
from PIL import Image
import pymupdf
from playwright.sync_api import sync_playwright, expect

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding='utf-8')
from evaluation.generate_fixtures import create_pdf
from polisdiff.extraction import extract_pdf, render_evidence
from polisdiff.models import Report
from polisdiff.presentation import finding_details, readiness_message, summary
from scripts.browser_check import settled, set_date, click_tab
from scripts.browser_i18n_check import choose_language

ROOT = Path(__file__).resolve().parents[1]


class App:
    def __init__(self, page, frame):
        self.page, self.frame = page, frame

    def __getattr__(self, name):
        # Browser operations on Page, app selectors/evaluation on its Frame.
        if name in {'expect_download','screenshot','set_viewport_size','viewport_size','wait_for_timeout'}:
            return getattr(self.page, name)
        return getattr(self.frame, name)


def connect(context, url):
    page = context.new_page()
    page.goto(url, wait_until='domcontentloaded', timeout=60000)
    if '.streamlit.app' in url:
        expect(page.locator('iframe[src*="~/+/"]')).to_have_count(1, timeout=60000)
        frame = page.locator('iframe[src*="~/+/"]').element_handle().content_frame()
    else:
        frame = page.main_frame
    app = App(page, frame)
    expect(app.locator('input[type=file]')).to_have_count(1, timeout=60000)
    settled(app)
    return app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--legacy', action='store_true')
    parser.add_argument('--expected-revision')
    args = parser.parse_args()
    dest = ROOT/'local_data'/args.name
    dest.mkdir(parents=True, exist_ok=True)
    result = {'checked_at': datetime.now(timezone.utc).isoformat(), 'url':args.url,
              'cases':[], 'page_errors':[], 'cloud_owner_logs_available':False,
              'deployed_revision':None, 'success':False}
    fixture = dest/'synthetic-conflict.pdf'
    create_pdf(fixture, [
        ['Synthetic regression fixture. ОСАГО. Header date is not applicability evidence. 19.03.2026.'],
        ['Общая страховая сумма составляет 60 000 000 сум.'],
        ['Страховое возмещение выплачивается в течение 9 рабочих дней после принятия решения страховщиком.'],
        ['Страхователю сообщается решение о страховом возмещении в течение 20 дней после письменного заявления.']])
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width':1365,'height':950}, accept_downloads=True)
        app = connect(context, args.url)
        app.page.on('pageerror', lambda error: result['page_errors'].append(str(error)))
        choose_language(app, 'en')

        def download(kind, name):
            with app.expect_download(timeout=60000) as event:
                app.get_by_role('button', name=f'Download {kind} report', exact=True).click()
            path = dest/f'{name}.{kind.lower()}'
            event.value.save_as(str(path))
            return path

        def analyze(path, name):
            app.locator('input[type=file]').set_input_files(str(path))
            expect(app.get_by_role('button',name=f'Remove {path.name}',exact=True)).to_be_visible(timeout=30000)
            expect(app.get_by_role('button',name='Download JSON report',exact=True)).to_have_count(0)
            settled(app)
            app.wait_for_timeout(5100)
            app.get_by_role('button',name='Analyze document',exact=True).click()
            expect(app.get_by_role('button',name='Download JSON report',exact=True)).to_be_visible(timeout=240000)
            settled(app)
            app.wait_for_timeout(300)
            report = Report.model_validate_json(download('JSON',name).read_bytes())
            html = download('HTML',name).read_text(encoding='utf-8')
            assert summary(report,'en') in unescape(html)
            for f in report.findings:
                d = finding_details(report,f,'en')
                for key in ('checked','found','reference','reason','remediation'):
                    assert d[key] in unescape(html)
                for ev in f.evidence:
                    assert ev.quote in unescape(html)
                assert d['draft'] is None
            assert 'PENDING_LEGAL_REVIEW' in html
            if report.retrieval_requested != report.retrieval_used:
                expect(app.get_by_text('The AI model is unavailable.',exact=False)).to_be_visible()
                assert report.retrieval_used == 'lexical' and report.model_revision is None
            result['cases'].append({'id':name, 'statuses':[f.status.value for f in report.findings],
                'retrieval_requested':report.retrieval_requested,'retrieval_used':report.retrieval_used,
                'model_revision':report.model_revision,'warnings':report.warnings,
                'applicable_date':str(report.applicable_date) if report.applicable_date else None})
            print(name, result['cases'][-1]['statuses'], report.retrieval_used, flush=True)
            return report

        if not args.legacy:
            expect(app.get_by_text(readiness_message('en'),exact=True)).to_be_visible()
            app.get_by_text('Deployment diagnostics',exact=True).click()
            with app.expect_download() as event:
                app.get_by_role('button',name='Download diagnostics',exact=True).click()
            event.value.save_as(str(dest/'deployment.json'))
            diagnostics = json.loads((dest/'deployment.json').read_bytes())
            result['deployment'] = diagnostics
            result['deployed_revision'] = diagnostics['source_revision']
            if args.expected_revision:
                assert diagnostics['source_revision'] == args.expected_revision, diagnostics
            app.get_by_text('Deployment diagnostics',exact=True).click()
        def diagnostics_snapshot(name):
            app.get_by_text('Deployment diagnostics',exact=True).click()
            with app.expect_download(timeout=60000) as event:
                app.get_by_role('button',name='Download diagnostics',exact=True).click()
            path = dest/f'{name}.json'
            event.value.save_as(str(path))
            app.get_by_text('Deployment diagnostics',exact=True).click()
            return json.loads(path.read_bytes())

        unknown = analyze(fixture, 'unknown-date')
        if not args.legacy:
            result['deployment_after_analysis'] = diagnostics_snapshot('deployment-after-analysis')
        assert all(f.status.value == 'UNVERIFIABLE' and f.expected_value is None and not f.source_quote
                   for f in unknown.findings)
        assert unknown.applicable_date is None
        if not args.legacy:
            preview = context.new_page()
            preview.goto((dest/'unknown-date.html').as_uri())
            expect(preview.locator('details.pending[open]')).to_have_count(0)
            preview.emulate_media(media='print')
            preview.pdf(path=str(dest/'unknown-date-print.pdf'),prefer_css_page_size=True,print_background=True)
            with pymupdf.open(dest/'unknown-date-print.pdf') as pdf:
                assert abs(pdf[0].rect.width - 595.28) < 2
                text = '\n'.join(page.get_text() for page in pdf)
                for phrase in ('60 000 000', '9 рабочих дней', '20 дней', 'PENDING_LEGAL_REVIEW'):
                    assert phrase in text, (phrase, text)
            preview.close()
            result['unknown_html_a4_evidence_visible'] = True
        if not args.legacy:
            expect(app.get_by_text(readiness_message('en'),exact=True)).to_have_count(1)
            expect(app.get_by_text('Pending date confirmation',exact=True)).to_have_count(3)
            expect(app.get_by_role('link',name='Confirm date and rerun analysis',exact=True)).to_have_count(1)
            expect(app.locator('[data-testid=stExpander] details[open]')).to_have_count(0)
        app.get_by_text(summary(unknown,'en'),exact=True).scroll_into_view_if_needed()
        app.screenshot(path=str(dest/'unknown-desktop.png'),full_page=True)
        if not args.legacy:
            app.get_by_text('Pending date confirmation',exact=True).last.scroll_into_view_if_needed()
            app.screenshot(path=str(dest/'pending-checks-desktop.png'),full_page=True)
        app.set_viewport_size({'width':390,'height':844})
        app.wait_for_timeout(700)
        app.get_by_text(summary(unknown,'en'),exact=True).scroll_into_view_if_needed()
        assert app.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        app.screenshot(path=str(dest/'unknown-mobile.png'),full_page=True)
        app.set_viewport_size({'width':1365,'height':950})
        if not args.legacy:
            app.get_by_role('link',name='Confirm date and rerun analysis',exact=True).click()
            expect(app.get_by_role('checkbox',name='I confirm the contract applicability date',exact=True)).not_to_be_checked()
        app.get_by_text('I confirm the contract applicability date',exact=True).click()
        set_date(app,'Contract applicability date','2026-03-19')
        expect(app.get_by_role('button',name='Download JSON report',exact=True)).to_have_count(0)
        supported = analyze(fixture, 'supported-conflict')
        assert [f.status.value for f in supported.findings] == ['POTENTIAL_CONFLICT']*3
        data = fixture.read_bytes()
        doc = extract_pdf(data)
        for f in supported.findings:
            ev = f.evidence[0]
            app.get_by_role('button',name=f'View in PDF · page {ev.page}',exact=True).first.click()
            settled(app)
            viewer = app.get_by_role('tabpanel',name='Findings',exact=True).locator('[data-testid=stExpander]:has(> details > summary :text-is("Selected evidence in PDF"))')
            expect(viewer.get_by_test_id('stImage')).to_be_visible()
            expected = render_evidence(data,doc,f,ev)
            assert expected['location']['state'] == 'precise'
            image = viewer.get_by_test_id('stImage').locator('img')
            png = context.request.get(urljoin(app.frame.url,image.get_attribute('src'))).body()
            a,b = Image.open(BytesIO(png)).convert('RGB'), Image.open(BytesIO(expected['png'])).convert('RGB')
            assert a.size == b.size and a.tobytes() == b.tobytes()
            expect(viewer.locator('mark')).to_have_text(ev.quote[expected['location']['start']:expected['location']['end']])
            (dest/f'{f.rule_id}-verified-highlight.png').write_bytes(png)
        app.screenshot(path=str(dest/'conflict-desktop.png'),full_page=True)
        app.set_viewport_size({'width':390,'height':844})
        app.wait_for_timeout(700)
        assert app.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        app.screenshot(path=str(dest/'conflict-mobile.png'),full_page=True)
        app.set_viewport_size({'width':1365,'height':950})
        click_tab(app,'Analyst review')
        note = 'Pending specialist review <script>literal</script> & Ўзбекча'
        app.get_by_role('textbox',name='Rationale',exact=True).fill(note)
        app.get_by_role('button',name='Record review',exact=True).click()
        # The textarea also contains this literal. Wait for the saved record,
        # rather than mistaking the editor for a completed server rerun.
        saved_review = app.get_by_role('tabpanel',name='Analyst review',exact=True).get_by_test_id('stText')
        expect(saved_review.get_by_text(note,exact=True)).to_be_visible(timeout=30000)
        settled(app)
        click_tab(app,'Findings')
        reviewed = Report.model_validate_json(download('JSON','reviewed').read_bytes())
        html = download('HTML','reviewed').read_text(encoding='utf-8')
        consistent = bool(reviewed.reviews) and reviewed.reviews[0].rationale == note and note in unescape(html)
        result['review_export_consistent'] = consistent
        if not consistent and args.legacy:
            result['baseline_review_export_failure'] = dict(json_reviews=len(reviewed.reviews), html_has_review=note in unescape(html))
            (dest/'review-export-dom.txt').write_text(app.locator('body').inner_text(),encoding='utf-8')
            app.screenshot(path=str(dest/'review-export-failure.png'),full_page=True)
        else:
            assert consistent
        assert '<script>literal' not in html and reviewed.findings == supported.findings
        gross = ROOT/'local_data/sources/gross_latin.pdf'
        assert gross.exists(), 'Required real GROSS Latin fixture unavailable'
        real = analyze(gross, 'gross-latin-supported')
        assert [f.status.value for f in real.findings] == ['UNVERIFIABLE']*3
        assert not real.reviews
        app.get_by_text('I confirm the contract applicability date',exact=True).click()
        expect(app.get_by_role('button',name='Download JSON report',exact=True)).to_have_count(0)
        real_unknown = analyze(gross, 'gross-latin-unknown')
        assert all(f.status.value == 'UNVERIFIABLE' for f in real_unknown.findings)
        other = browser.new_context()
        fresh = connect(other,args.url)
        expect(fresh.get_by_role('button',name='Скачать JSON отчет',exact=True)).to_have_count(0)
        expect(fresh.get_by_test_id('stImage')).to_have_count(0)
        other.close()
        # Search-mode changes also discard reports and selected evidence.
        app.get_by_text('Advanced search settings',exact=True).click()
        app.get_by_text('Lexical search',exact=True).click()
        settled(app)
        expect(app.get_by_role('button',name='Download JSON report',exact=True)).to_have_count(0)
        expect(app.get_by_test_id('stImage')).to_have_count(0)
        assert not result['page_errors']
        result.update(success=consistent,unknown_date_abstention=True,confirmed_date_conflicts=True,
            original_gross_abstentions_preserved=True,html_json_consistent=True,review_preserved=consistent,
            precise_png_matches_worker=True,mobile_no_overflow=True,session_isolation=True,
            report_and_selection_invalidation=True)
        context.close()
        browser.close()
    (dest/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
