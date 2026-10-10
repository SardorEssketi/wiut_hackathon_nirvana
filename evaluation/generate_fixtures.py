"""Create reproducible, original labelled PDFs. Labels are independent of engine execution."""
from pathlib import Path
import hashlib
import json
import os
import textwrap
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
RULE_IDS = ["OSAGO_SUM", "OSAGO_PAYMENT", "OSAGO_DECISION_NOTICE"]


def font_path():
    candidates = [os.getenv("POLISDIFF_FIXTURE_FONT", ""), "C:/Windows/Fonts/arial.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    return next(Path(p) for p in candidates if p and Path(p).exists())


def create_pdf(path, pages, *, title="Original synthetic OSAGO test document"):
    pdfmetrics.registerFont(TTFont("FixtureFont", str(font_path())))
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=(595,842), invariant=1)
    c.setTitle(title)
    c.setAuthor("PolisDiff AI synthetic fixture generator")
    for i, paragraphs in enumerate(pages):
        c.setFont("FixtureFont", 10)
        y = 790
        for paragraph in paragraphs:
            for line in textwrap.wrap(paragraph, width=84, break_long_words=False, break_on_hyphens=False):
                c.drawString(40,y,line)
                y -= 16
            y -= 20
        c.setFont("FixtureFont", 8)
        c.drawString(40,35,f"Synthetic fixture · page {i+1}")
        c.showPage()
    c.save()


def generate():
    source = json.loads((ROOT / "evaluation" / "fixture_texts.json").read_text(encoding="utf-8"))
    manifest = []
    for split in ["development", "evaluation"]:
        for language, original in source[split].items():
            cases = ["match"] if split == "development" else ["match", "sum_conflict", "payment_conflict", "notice_conflict", "omission", "historic", "unknown_date", "reference", "ambiguous"]
            for case in cases:
                terms = list(original)
                expected = dict.fromkeys(RULE_IDS, "MATCH_FOUND")
                applicable = "2026-01-05"
                if case == "sum_conflict":
                    terms[0] = terms[0].replace("80", "60")
                    expected[RULE_IDS[0]] = "POTENTIAL_CONFLICT"
                elif case == "payment_conflict":
                    terms[1] = terms[1].replace(" 5 ", " 9 ")
                    expected[RULE_IDS[1]] = "POTENTIAL_CONFLICT"
                elif case == "notice_conflict":
                    terms[2] = terms[2].replace(" 15 ", " 22 ")
                    expected[RULE_IDS[2]] = "POTENTIAL_CONFLICT"
                elif case == "omission":
                    terms[1] = "No payment-deadline clause is provided in this original synthetic fixture."
                    expected[RULE_IDS[1]] = "NOT_FOUND"
                elif case == "historic":
                    terms[0] = terms[0].replace("80", "40")
                    applicable = "2024-09-06"
                elif case == "unknown_date":
                    applicable = None
                    expected = dict.fromkeys(RULE_IDS, "UNVERIFIABLE")
                elif case == "reference":
                    ref = {"uz-Latn": "Shartnoma Vazirlar Mahkamasining 141-son qarori bilan tasdiqlangan qoidalarga havola qiladi.",
                           "uz-Cyrl": "Шартнома Вазирлар Маҳкамасининг 141-сон қарори билан тасдиқланган қоидаларга ҳавола қилади.",
                           "ru-Cyrl": "Договор ссылается на правила, утвержденные постановлением Кабинета Министров №141."}[language]
                    terms = [ref, "Document reference only.", "Document reference only."]
                    expected = dict.fromkeys(RULE_IDS, "UNVERIFIABLE")
                elif case == "ambiguous":
                    terms[1] = terms[1].replace("ish kuni", "kalendar kuni").replace("иш куни", "календар куни").replace("рабочих дней", "календарных дней")
                    expected[RULE_IDS[1]] = "UNVERIFIABLE"
                pages = [["PUBLIC TEST OFFER · ОСАГО · synthetic", "06.09.2024" if case == "historic" else "05.01.2026"] + source["distractors"][language]]
                for term in terms:
                    pages.append([term] + source["distractors"][language])
                name = f"{language}_{case}"
                relative = f"tests/fixtures/{split}/{name}.pdf"
                path = ROOT / relative
                create_pdf(path, pages)
                manifest.append({"id": name, "split": split, "language": language, "case": case, "path": relative,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "applicable_date": applicable,
                    "expected": expected, "relevant_pages": {rule: [i+2] for i, rule in enumerate(RULE_IDS)
                        if not (case in {"reference"} or case == "omission" and i==1)}, "ground_truth_pages": pages})
    (ROOT / "evaluation" / "dataset_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Generated", len(manifest), "original synthetic PDFs; development and evaluation splits are separate.")

if __name__ == "__main__":
    generate()
