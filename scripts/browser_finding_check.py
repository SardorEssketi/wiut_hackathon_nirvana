"""Actual localhost review workflow, precise rendered evidence and abstentions.

Public-document quotations/screenshots remain in ignored local_data only.
"""
from datetime import date, datetime, timezone
from pathlib import Path
from html import unescape
import argparse
import hashlib
import json
import sys
from io import BytesIO
from PIL import Image
import pymupdf
from playwright.sync_api import sync_playwright, expect
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evaluation.generate_fixtures import create_pdf
from polisdiff.models import Report
from polisdiff.extraction import extract_pdf, render_evidence
from polisdiff.presentation import finding_details, summary
from scripts.browser_check import settled, set_date, click_tab
from scripts.browser_i18n_check import choose_language

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'local_data/finding_browser'


def download(page,kind,name):
    with page.expect_download() as event:
        page.get_by_role('button',name=f'Download {kind} report',exact=True).click()
    path=DEST/f'{name}.{kind.lower()}'
    event.value.save_as(str(path))
    return path


def analyze(page,name):
    page.wait_for_timeout(5100)
    page.get_by_role('button',name='Analyze document',exact=True).click()
    expect(page.get_by_role('button',name='Download JSON report',exact=True)).to_be_visible(timeout=180000)
    settled(page)
    report=Report.model_validate_json(download(page,'JSON',name).read_bytes())
    expect(page.get_by_text(summary(report,'en'),exact=True)).to_be_visible()
    return report


def upload(page,path):
    page.locator('input[type=file]').set_input_files(str(path))
    # Visible filenames are truncated by the uploader; the remove control keeps
    # the complete accessible name and appears when the upload completes.
    expect(page.get_by_role('button',name=f'Remove {path.name}',exact=True)).to_be_visible(timeout=30000)
    expect(page.get_by_role('button',name='Download JSON report',exact=True)).to_have_count(0,timeout=30000)
    settled(page)


def mobile(page):
    page.set_viewport_size({'width':390,'height':844})
    sidebar=page.get_by_test_id('stSidebar')
    # Streamlit closes it responsively; clicking while it slides can race that
    # transition and target a control which has already moved off screen.
    expect(sidebar).to_have_attribute('aria-expanded','false')
    expect(sidebar).not_to_be_in_viewport()


def select_and_verify(page,context,data,doc,report,f,name):
    ev=f.evidence[0]
    page.get_by_role('button',name=f'View in PDF · page {ev.page}',exact=True).first.click()
    settled(page)
    active=page.get_by_role('tabpanel',name='Findings',exact=True)
    # The exact tab title comes from the existing interface catalogue.
    viewer=active.locator('[data-testid="stExpander"]:has(> details > summary :text-is("Selected evidence in PDF"))')
    expect(viewer).to_have_count(1)
    expect(viewer.get_by_test_id('stImage')).to_be_visible()
    expect(viewer.get_by_text(f'PDF page {ev.page}',exact=False)).to_be_visible()
    details=finding_details(report,f,'en')
    expect(active.get_by_text(details['found'],exact=True).first).to_be_visible()
    resolution=viewer.locator("xpath=ancestor::div[@data-testid='stExpander'][1]")
    for key in ['checked','reference','reason','remediation']:
        expect(resolution.get_by_text(details[key],exact=True).first).to_be_visible()
    result=render_evidence(data,doc,f,ev)
    note='Precise highlighting of the validated amount or deadline.' if result['location']['state']=='precise' else 'Precise PDF highlighting is unavailable.'
    expect(viewer.get_by_text(note,exact=False)).to_be_visible()
    image=viewer.get_by_test_id('stImage').locator('img')
    rendered=context.request.get(image.get_attribute('src')).body()
    # Streamlit may re-encode PNG compression; compare actual pixels and size.
    actual=Image.open(BytesIO(rendered)).convert('RGB')
    validated=Image.open(BytesIO(result['png'])).convert('RGB')
    (DEST/f'{name}-browser-pdf.png').write_bytes(rendered)
    (DEST/f'{name}-validated-pdf.png').write_bytes(result['png'])
    assert actual.size==validated.size and actual.tobytes()==validated.tobytes(), (actual.size,validated.size)
    (DEST/f'{name}-pdf.png').write_bytes(rendered)
    if result['location']['state']=='precise':
        expect(viewer.locator('mark')).to_have_count(1)
        target=ev.quote[result['location']['start']:result['location']['end']]
        expect(viewer.locator('mark')).to_have_text(target)
    viewer.scroll_into_view_if_needed()
    page.screenshot(path=str(DEST/f'{name}-desktop.png'),full_page=True)
    mobile(page)
    image.scroll_into_view_if_needed()
    assert page.evaluate('Math.max(0,document.documentElement.scrollWidth-window.innerWidth)')==0
    page.screenshot(path=str(DEST/f'{name}-mobile.png'),full_page=True)
    page.set_viewport_size({'width':1365,'height':950})
    return result['location']['state']


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',default='http://127.0.0.1:8512')
    args=parser.parse_args()
    DEST.mkdir(parents=True,exist_ok=True)
    fixture=DEST/'independent-localization.pdf'
    create_pdf(fixture,[['Independent localization regression. ОСАГО. 19.03.2026.'],
        ['Премия по другому продукту: 60 000 000 сум.',
         'Общая страховая сумма составляет 60 000 000 сум. <script>literal</script> & original.'],
        ['Страховое возмещение выплачивается в течение 9 рабочих дней после принятия решения страховщиком.'],
        ['Страхователю сообщается решение о страховом возмещении в течение 20 дней после письменного заявления.']])
    missing=DEST/'missing.pdf'
    create_pdf(missing,[['Original ordinary text without insurance conditions, amounts or deadlines.']])
    wrong=DEST/'wrong-trigger.pdf'
    create_pdf(wrong,[['Страховое возмещение выплачивается в течение 4 рабочих дней после принятия решения суда.']])
    results={'checked_at':datetime.now(timezone.utc).isoformat(),'cases':[], 'errors':[], 'external_requests':[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        context=browser.new_context(viewport={'width':1365,'height':950},accept_downloads=True)
        page=context.new_page()
        page.on('pageerror',lambda error:results['errors'].append(str(error)))
        page.on('request',lambda request:results['external_requests'].append(request.url) if not
            request.url.startswith((args.url,args.url.replace('http:','ws:'),'data:','blob:')) else None)
        page.goto(args.url,wait_until='networkidle')
        settled(page)
        choose_language(page,'en')
        page.get_by_text('I confirm the contract applicability date',exact=True).click()
        set_date(page,'Contract applicability date','2026-03-19')
        page.get_by_text('Advanced search settings',exact=True).click()
        page.get_by_text('Lexical search',exact=True).click()
        settled(page)
        upload(page,fixture)
        report=analyze(page,'independent')
        assert [f.status.value for f in report.findings]==['POTENTIAL_CONFLICT']*3
        page.get_by_text(summary(report,'en'),exact=True).scroll_into_view_if_needed()
        page.screenshot(path=str(DEST/'summary-desktop.png'))
        mobile(page)
        page.get_by_text(summary(report,'en'),exact=True).scroll_into_view_if_needed()
        assert page.evaluate('Math.max(0,document.documentElement.scrollWidth-window.innerWidth)')==0
        page.screenshot(path=str(DEST/'summary-mobile.png'))
        page.set_viewport_size({'width':1365,'height':950})
        data=fixture.read_bytes()
        doc=extract_pdf(data)
        for f in report.findings:
            assert finding_details(report,f,'en')['draft'] is None
            state=select_and_verify(page,context,data,doc,report,f,f.rule_id)
            assert state=='precise'
            results['cases'].append({'id':f.rule_id,'status':f.status.value,'page':f.evidence[0].page,'localization':state})
        # Annotation and JSON/HTML share the same deterministic explanations.
        click_tab(page,'Analyst review')
        rationale='Specialist review pending <script>literal</script> & Ўзбекча'
        page.get_by_role('textbox',name='Rationale',exact=True).fill(rationale)
        page.get_by_role('button',name='Record review',exact=True).click()
        settled(page)
        click_tab(page,'Findings')
        reviewed=Report.model_validate_json(download(page,'JSON','reviewed').read_bytes())
        assert reviewed.reviews[0].rationale==rationale
        assert reviewed.findings==report.findings
        html_path=download(page,'HTML','reviewed')
        html=html_path.read_text(encoding='utf-8')
        assert '<script>literal' not in html and rationale in unescape(html)
        for f in reviewed.findings:
            d=finding_details(reviewed,f,'en')
            for key in ['checked','found','reference','reason','remediation']:
                assert d[key] in unescape(html)
        # Date changes invalidate the selected page and original annotation.
        page.get_by_text('I confirm the contract applicability date',exact=True).click()
        settled(page)
        expect(page.get_by_role('button',name='Download JSON report',exact=True)).to_have_count(0)
        unknown=analyze(page,'unknown')
        assert all(f.status.value=='UNVERIFIABLE' for f in unknown.findings)
        assert not unknown.reviews
        f=unknown.findings[0]
        assert select_and_verify(page,context,data,doc,unknown,f,'unknown')=='precise_unavailable'
        page.get_by_text('I confirm the contract applicability date',exact=True).click()
        set_date(page,'Contract applicability date','2026-03-19')
        upload(page,missing)
        absent=analyze(page,'missing')
        assert all(f.status.value=='NOT_FOUND' and not f.evidence for f in absent.findings)
        expect(page.get_by_role('button',name='View in PDF',exact=False)).to_have_count(0)
        upload(page,wrong)
        incorrect=analyze(page,'wrong-trigger')
        assert incorrect.findings[1].status.value=='UNVERIFIABLE'
        assert 'insurer' in finding_details(incorrect,incorrect.findings[1],'en')['reason']
        # Public samples: preserve all eight abstentions and historical ambiguity.
        annotations=json.loads((ROOT/'evaluation/real_annotations.json').read_text(encoding='utf-8'))
        for case in annotations['cases']:
            path=ROOT/f"local_data/sources/{case['id']}.pdf"
            if not path.exists():
                results['cases'].append({'id':case['id'],'available':False})
                continue
            set_date(page,'Contract applicability date',case['applicable_date'])
            upload(page,path)
            public=analyze(page,case['id'])
            expected=['POTENTIAL_CONFLICT','UNVERIFIABLE','UNVERIFIABLE'] if case['id']=='gross_cyrillic' else ['UNVERIFIABLE']*3
            assert [f.status.value for f in public.findings]==expected
            f=public.findings[0] if case['id']!='inson_russian' else public.findings[2]
            pdf_data=path.read_bytes()
            document=extract_pdf(pdf_data)
            state=select_and_verify(page,context,pdf_data,document,public,f,case['id'])
            results['cases'].append({'id':case['id'],'statuses':expected,'localization':state,
                'date_context':case['note'],'legal_violation_established':False})
            print(case['id'],expected,state,flush=True)
        # Separate session has no report or selected evidence.
        other=browser.new_context()
        fresh=other.new_page()
        fresh.goto(args.url,wait_until='networkidle')
        settled(fresh)
        expect(fresh.get_by_role('button',name='Скачать JSON отчет',exact=True)).to_have_count(0)
        other.close()
        # Actual A4 printing with no externally loaded resources.
        print_context=browser.new_context()
        preview=print_context.new_page()
        external=[]
        preview.on('request',lambda r:external.append(r.url) if not r.url.startswith(('file:','data:')) else None)
        preview.goto(html_path.as_uri())
        preview.emulate_media(media='print')
        preview.pdf(path=str(DEST/'reviewed-print.pdf'),prefer_css_page_size=True,print_background=True)
        with pymupdf.open(DEST/'reviewed-print.pdf') as pdf:
            assert abs(pdf[0].rect.width-595.28)<2 and abs(pdf[0].rect.height-841.89)<2
            text='\n'.join(p.get_text() for p in pdf)
            assert '80 000 000' in text and 'Conditional action' in text and 'PENDING_LEGAL_REVIEW' in text
            pdf[0].get_pixmap().save(DEST/'print-first-page.png')
        assert not external
        print_context.close()
        assert not results['errors'] and not results['external_requests'],results
        results.update(success=True,missing_evidence_has_no_pdf_action=True,stale_selection_discarded=True,
            original_annotations_preserved=True,unknown_date_abstention=True,wrong_event_abstention=True,
            session_isolation=True,a4_print=True,precise_browser_png_matches_worker=True)
        context.close()
        browser.close()
    (ROOT/'evaluation/finding_browser_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Finding workflow verified in desktop/mobile Chromium, original PNG geometry, public documents and A4 export.')


if __name__=='__main__': main()
