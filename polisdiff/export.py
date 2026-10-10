from datetime import datetime, timezone
from html import escape
from .models import Report, ReviewAction


def add_review(report: Report, rule_id: str, action: str, rationale: str):
    if rule_id not in {f.rule_id for f in report.findings}:
        raise ValueError("Unknown finding")
    report.reviews.append(ReviewAction(rule_id=rule_id, action=action,
        rationale=rationale.strip(), timestamp=datetime.now(timezone.utc)))


def html_report(report: Report) -> str:
    e = lambda value: escape(str(value))
    findings = []
    for f in report.findings:
        evidence = "".join(f"<div><p>Page {v.page} · {e(v.section)}</p><pre>{e(v.quote)}</pre></div>" for v in f.evidence)
        findings.append(f"<section><h2>{e(f.rule_name)}</h2><b>{e(f.status.value)}</b><p>{e(f.reason)}</p>"
            f"<p>{e(f.provision_reference)} · {e(f.effective_from)} – {e(f.effective_to or 'open through verification date')}</p>"
            f"<a href='{e(f.source_url)}'>Primary legal source</a><p>Source excerpt: {e(f.source_quote)}</p>"
            f"<p>{e(f.reviewer_status)}</p>{evidence}</section>")
    reviews = "".join(f"<li>{e(r.timestamp.isoformat())} · {e(r.rule_id)} · {e(r.action)} · {e(r.rationale)}</li>" for r in report.reviews)
    return "<!doctype html><html lang='ru'><meta charset='utf-8'><title>PolisDiff AI report</title>" + (
        "<style>body{font:16px system-ui;max-width:960px;margin:40px auto;padding:24px;color:#172b4d}"
        "section{border:1px solid #ccd5dd;padding:24px;margin:20px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}"
        "a{color:#007f73}</style><h1>PolisDiff AI</h1>"
        f"<p>{e(report.disclaimer)}</p><p>SHA256: {e(report.document_sha256)}</p>"
        f"<p>Audit: {e(report.audit_date)} · Applicable: {e(report.applicable_date)} · Date basis: {e(report.date_basis)}</p>"
        f"<p>Catalogue: {e(report.rules_catalogue_version)} · {e(report.rules_catalogue_sha256)}</p>"
        f"<p>Retrieval: {e(report.retrieval_used)} · Model: {e(report.model_revision)}</p>"
        f"<p>Warnings: {e('; '.join(report.warnings))}</p>" + "".join(findings) + f"<h2>Review audit record</h2><ul>{reviews}</ul></html>")
