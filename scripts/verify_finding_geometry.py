"""Produce bounded original-page highlight images for human geometry inspection."""
from datetime import date
from pathlib import Path
import json
import sys
import pymupdf
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from polisdiff.extraction import extract_pdf, render_evidence
from polisdiff.localization import canonical_map, trigger_range, locate_on_page
from polisdiff.models import Report
from polisdiff.service import audit_document
from polisdiff.retrieval import Retriever
from evaluation.generate_fixtures import create_pdf

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'local_data/finding_geometry'


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    cases=[]
    for script in ['uz-Latn','uz-Cyrl','ru-Cyrl']:
        path=ROOT/f'tests/fixtures/evaluation/{script}_sum_conflict.pdf'
        data=path.read_bytes()
        doc=extract_pdf(data)
        report=audit_document(doc,date(2026,10,10),date(2026,3,19),Retriever('lexical'))
        for f in report.findings:
            ev=f.evidence[0]
            result=render_evidence(data,doc,f,ev)
            (DEST/f'{script}-{f.rule_id}.png').write_bytes(result['png'])
            cases.append({'id':script,'rule_id':f.rule_id,'page':ev.page,'state':result['location']['state']})
    # Actual two-line value; write direct lines so textwrap cannot fold them.
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from evaluation.generate_fixtures import font_path
    path=DEST/'multiline.pdf'
    pdfmetrics.registerFont(TTFont('GeometryFont',str(font_path())))
    c=canvas.Canvas(str(path),pagesize=(595,842))
    c.setFont('GeometryFont',12)
    c.drawString(40,790,'Общая страховая сумма составляет 60 000')
    c.drawString(40,768,'000 сум.')
    c.save()
    for angle in [0,90,180,270]:
        with pymupdf.open(path) as pdf:
            pdf[0].set_rotation(angle)
            data=pdf.tobytes()
        doc=extract_pdf(data)
        report=audit_document(doc,date(2026,10,10),date(2026,3,19),Retriever('lexical'))
        f=report.findings[0]
        result=render_evidence(data,doc,f,f.evidence[0])
        assert result['location']['state']=='precise'
        (DEST/f'multiline-rotation-{angle}.png').write_bytes(result['png'])
        cases.append({'id':'multiline','rotation':angle,'state':result['location']['state'],'boxes':len(result['location']['rectangles'])})
    # Diagnostic state only; original public quotations remain in ignored files.
    for name in ['gross_latin','gross_cyrillic','inson_russian']:
        data=(ROOT/f'local_data/sources/{name}.pdf').read_bytes()
        doc=extract_pdf(data)
        report=Report.model_validate_json((ROOT/f'local_data/finding_browser/{name}.json').read_bytes())
        for f in report.findings:
            for ev in f.evidence:
                with pymupdf.open(stream=data,filetype='pdf') as pdf:
                    loc=locate_on_page(pdf[ev.page-1],f,ev)
                cases.append({'id':name,'rule_id':f.rule_id,'page':ev.page,'state':loc.state,
                    'trigger_mapped':trigger_range(f,ev) is not None})
                if loc.state=='precise':
                    result=render_evidence(data,doc,f,ev)
                    (DEST/f'{name}-{f.rule_id}-page{ev.page}.png').write_bytes(result['png'])
    (DEST/'geometry-results.json').write_text(json.dumps(cases,indent=2),encoding='utf-8')
    for row in cases: print(row,flush=True)


if __name__=='__main__': main()
