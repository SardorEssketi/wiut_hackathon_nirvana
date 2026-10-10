"""Independent Chromium journey against the actual localhost server."""
from datetime import datetime, timezone
from pathlib import Path
import json
import argparse
import sys
import time
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright, expect
from evaluation.generate_fixtures import create_pdf
from polisdiff.extraction import extract_pdf

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "local_data" / "browser"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8501")
    parser.add_argument("--output", default="browser_results.json")
    parser.add_argument("--only", nargs="+")
    args = parser.parse_args()
    DEST.mkdir(parents=True,exist_ok=True)
    unseen = DEST / "unseen-browser.pdf"
    create_pdf(unseen, [["Original browser test, OSAGO. 05.01.2026.",
        "Страховая сумма установлена в размере 51 234 567 сум.",
        "Выплата страхового возмещения осуществляется в течение 4 рабочих дней со дня принятия решения страховщика.",
        "Решение о страховом возмещении сообщено страхователю через 14 дней после письменного обращения."]])
    results = {"checked_at":datetime.now(timezone.utc).isoformat(),"url":args.url, "public_deployment_tested":False,
        "browser":"Chromium (Playwright)","cases":[],"errors":[],"external_requests":[]}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width":1365,"height":950}, accept_downloads=True)
        page = context.new_page()
        page.on("pageerror",lambda error:results["errors"].append(str(error)))
        page.on("request",lambda request:results["external_requests"].append(request.url.split('?')[0]) if
                not request.url.startswith((args.url, args.url.replace("http:","ws:"), "data:", "blob:")) else None)
        page.goto(results["url"],wait_until="networkidle",timeout=60000)
        expect(page.get_by_role("heading", name="Условия полиса, с доказательствами")).to_be_visible(timeout=60000)
        page.screenshot(path=str(DEST / "initial-desktop.png"),full_page=True)
        expect(page.get_by_role("button",name="Анализировать документ",exact=True)).to_be_disabled()
        page.get_by_text("Я подтверждаю дату применимости договора",exact=True).click()
        expect(page.get_by_role("checkbox",name="Я подтверждаю дату применимости договора")).to_be_checked()
        cases = [(f"synthetic_{lang}",ROOT / f"tests/fixtures/evaluation/{lang}_sum_conflict.pdf", True) for lang in ["uz-Latn","uz-Cyrl","ru-Cyrl"]]
        cases += [("unseen_browser",unseen,True)]
        cases += [(key,ROOT / f"local_data/sources/{key}.pdf",False) for key in ["gross_latin","gross_cyrillic","inson_russian"]]
        if args.only:
            cases = [case for case in cases if case[0] in args.only]
            assert cases, "No selected browser cases"
        previous = None
        for key,path,labelled in cases:
            # UI has a measured per-session five-second cooldown.
            page.wait_for_timeout(5100)
            if previous is not None:
                page.get_by_role("button",name=f"Remove {previous.name}",exact=True).click()
                expect(page.get_by_role("button",name="Анализировать документ",exact=True)).to_be_disabled(timeout=30000)
                expect(page.get_by_role("button",name="Скачать JSON отчет",exact=True)).to_have_count(0,timeout=30000)
            applicable = {"gross_cyrillic":"2024-09-06", "inson_russian":"2026-01-15"}.get(key,"2026-01-05")
            for part,value in zip(("year","month","day"),applicable.split("-")):
                control = page.get_by_role("spinbutton",name=f"{part}, Дата применимости договора",exact=True)
                if control.inner_text() != value:
                    control.fill(value)
                    control.press("Tab")
                    expect(control).to_have_text(value,timeout=30000)
                    page.wait_for_timeout(750)
                    expect(page.get_by_test_id("stApp")).to_have_attribute("data-test-script-state","notRunning",timeout=30000)
            page.wait_for_timeout(750)
            expect(page.get_by_test_id("stApp")).to_have_attribute("data-test-script-state","notRunning",timeout=30000)
            page.locator("input[type=file]").set_input_files(str(path))
            previous = path
            expect(page.get_by_role("button",name="Скачать JSON отчет",exact=True)).to_have_count(0,timeout=30000)
            button = page.get_by_role("button",name="Анализировать документ",exact=True)
            expect(button).to_be_enabled(timeout=30000)
            start = time.perf_counter()
            button.click()
            export = page.get_by_role("button",name="Скачать JSON отчет",exact=True)
            expect(export).to_be_visible(timeout=180000)
            with page.expect_download() as downloaded:
                export.click()
            report_path = DEST / f"{key}.json"
            downloaded.value.save_as(str(report_path))
            report = json.loads(report_path.read_text(encoding="utf-8"))
            assert report["retrieval_used"] == "hybrid", report["warnings"]
            statuses = [f["status"] for f in report["findings"]]
            if labelled:
                assert statuses == ["POTENTIAL_CONFLICT","MATCH_FOUND","MATCH_FOUND"], statuses
            document = extract_pdf(path.read_bytes())
            assert report["document_sha256"] == document.sha256
            assert report["applicable_date"] == applicable
            for finding in report["findings"]:
                assert finding["reviewer_status"] == "PENDING_LEGAL_REVIEW"
                for ev in finding["evidence"]:
                    assert document.pages[ev["page"]-1].text[ev["start"]:ev["end"]] == ev["quote"]
            results["cases"].append({"id":key,"statuses":statuses,"page_count":report["page_count"],
                "applicable_date":report["applicable_date"],
                "languages":report["detected_languages"],"analysis_seconds":report["timings_seconds"]["end_to_end"],
                "browser_journey_seconds":time.perf_counter()-start,"evidence_verified":True})
            print(key,"passed",statuses,flush=True)
            if key == "unseen_browser":
                page.get_by_role("tab",name="Решение аналитика").click()
                page.get_by_role("textbox",name="Обоснование").fill("Original browser reviewer rationale; confirm source context manually.")
                page.get_by_role("button",name="Записать решение",exact=True).click()
                record = page.locator('[data-testid="stText"]').filter(has_text="Original browser reviewer rationale; confirm source context manually.")
                expect(record).to_have_count(1,timeout=30000)
                page.get_by_role("tab",name="Решение аналитика").click()
                expect(record).to_be_visible(timeout=30000)
                page.get_by_role("tab",name="Результаты",exact=True).click()
                with page.expect_download() as downloaded_review:
                    page.get_by_role("button",name="Скачать JSON отчет",exact=True).click()
                reviewed_path = DEST / "reviewed.json"
                downloaded_review.value.save_as(str(reviewed_path))
                reviewed = json.loads(reviewed_path.read_text(encoding="utf-8"))
                assert len(reviewed["reviews"]) == 1
                assert reviewed["reviews"][0]["action"] == "further_review"
                results["review_export_verified"] = True
                with page.expect_download() as downloaded_html:
                    page.get_by_role("button",name="Скачать HTML отчет",exact=True).click()
                downloaded_html.value.save_as(str(DEST / "reviewed.html"))
                assert "Original browser reviewer rationale" in (DEST/"reviewed.html").read_text(encoding="utf-8")
                results["html_export_verified"] = True
                page.screenshot(path=str(DEST / "results-desktop.png"),full_page=True)
                page.set_viewport_size({"width":390,"height":844})
                page.evaluate("window.scrollTo(0,0)")
                page.wait_for_function("()=>{const el=document.querySelector('[data-testid=stSidebar]'); return !el || el.getBoundingClientRect().right<=1 || getComputedStyle(el).display==='none'}")
                page.wait_for_timeout(500)
                page.screenshot(path=str(DEST / "results-mobile.png"),full_page=True)
                results["mobile_horizontal_overflow_px"] = page.evaluate("Math.max(0,document.documentElement.scrollWidth-window.innerWidth)")
                assert results["mobile_horizontal_overflow_px"] <= 20
                page.set_viewport_size({"width":1365,"height":950})
                page.wait_for_function("()=>document.querySelector('[data-testid=stSidebar]').getBoundingClientRect().left>=0")
                page.get_by_role("tab",name="Доказательства документа").click()
                page.get_by_role("button",name="Показать изображение страницы",exact=True).click()
                expect(page.locator('[data-testid="stImage"] img')).to_be_visible(timeout=30000)
                results["page_preview_verified"] = True
                page.get_by_role("tab",name="Результаты",exact=True).click()
        assert not results["errors"], results["errors"]
        page.get_by_role("button",name="Очистить сессию",exact=True).click()
        expect(page.get_by_role("button",name="Анализировать документ",exact=True)).to_be_disabled(timeout=30000)
        expect(page.get_by_role("button",name="Скачать JSON отчет",exact=True)).to_have_count(0)
        results["session_clear_verified"] = True
        context.close()
        browser.close()
    results["success"] = True
    (ROOT / "evaluation" / args.output).write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Verified actual localhost journey, review/export, preview, mobile layout and session clearing.")

if __name__ == "__main__":
    main()
