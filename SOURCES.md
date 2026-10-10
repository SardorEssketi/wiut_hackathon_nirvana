# Verified sources and access record

Access date: 10 October 2026. Hashes, response statuses and timestamps are in
`evaluation/source_manifest.json`. Original downloads remain in ignored
`local_data/sources/`; public insurer PDFs are not redistributed in this repository.

## Problem evidence

[Competition Committee report, 18 February 2026](https://raqobat.gov.uz/uz/raqobat-qomitasi-tomonidan-sugurta-xizmatlari-yonalishida-1-000-ga-yaqin-murojaatlar-korib-chiqilib-istemolchilar-foydasiga-28-mlrd-som-mablag/)
reports deficiencies in electronic insurance offers, insurer-obligation information,
state-language availability and access to updated rules. It reports approximately
1,000 insurance-related complaints and 2.8 billion UZS paid in consumers' favor;
those complaints are not a count of defective contracts or this product's savings.
This is market-problem evidence, not a legal rule catalogue or partner endorsement.

## Law and amendment verification

- [Resolution 141, official Uzbek text](https://lex.uz/docs/1366339): operative
  paragraph 1 and appendix 4, paragraphs 66–67 inspected.
- [Russian reference text](https://lex.uz/docs/1366341): LexUZ marks amended
  Russian passages as unofficial translations. Official Uzbek wording controls
  source verification for this prototype.
- [Historical official text reached through paragraph 1's previous-version link](https://lex.uz/docs/1366339?ONDATE=17.06.2019%2000):
  historical total sum and paragraphs 66–67 inspected.
- [Resolution 458 of 23 July 2025, Russian reference](https://lex.uz/docs/7645190):
  amendment source linked by LexUZ. The clause-specific sum change applies from
  1 January 2026. Publication date is not substituted for that effective date.
- Paragraph 67's current official annotation identifies the distinct Resolution
  458 of **30 July 2024**, published 5 August 2024, adding electronic requests.
  The two resolutions share a number but have different years and subjects.

The requested 6 September 2024 historical snapshot was unreachable in both web
and direct-download attempts. The 2019 historical and current official documents
were reachable; the engine uses a conservative supported boundary of 5 August
2024. Paragraph 66's supported-version boundary is not its original enactment
date. No version after the verification date is assumed verified.

The catalogue contains short exact source excerpts with full provision references,
version notes, effective intervals and engineering interpretations. It does not
establish that an offer must reproduce every provision. Human interpretation
approval remains `PENDING_LEGAL_REVIEW` for all three checks.

## Public document observations

| Document | Original URL | Observed input |
| --- | --- | --- |
| GROSS Uzbek Latin | [PDF](https://gross.uz/uploaded/new-site/documents/osago-doc-mPGc-Wd1fg.pdf) | 8 pages; damaged text; some mixed characters; one near-empty final page |
| GROSS Uzbek Cyrillic | [PDF](https://gross.uz/public_offers/osago-offer-uz.pdf) | 6 pages; first-page date 06.09.2024; metadata mentions 2026 and current bytes contain newer numeric wording |
| INSON Russian | [PDF](https://insuranceon.uz/media/attachments/2026/01/15/ruOsago_offer.pdf) | 66 pages; offer pages 1–8, appended statutory rules from page 9; OCR-like letter O in numeric amounts |

URLs may change in place. Metadata and a document header do not establish that
the current file was served in 2024 or that its conditions apply to an active
contract. The Cyrillic sample is used for language and historical handling.
Public-document benchmarks label relevant pages, not legal compliance.

## Models, OCR and software

- [E5 author model card](https://huggingface.co/intfloat/multilingual-e5-small):
  MIT label, multilingual coverage includes Uzbek; requires query/passage prefixes
  and truncates long input at 512 tokens. Runtime performance on Uzbek must be
  judged from this project's measurements, not the model card's general claims.
  Pinned revision and downloaded file hashes: `evaluation/model_manifest.json`.
- [Tesseract language resources](https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html):
  resources exist for `uzb`, `uzb_cyrl`, `rus`. Local binary was absent; quality
  was not measured and OCR is disabled. See `evaluation/ocr_probe.json`.
- [PyMuPDF licenses](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright):
  AGPL/commercial licensing. See `DATA_LICENSES.md` before redistribution/hosting.
- [PyTorch CPU wheel index](https://download.pytorch.org/whl/cpu/torch/):
  checked for the matching Python 3.12 / Linux CPU wheel used by Docker.
