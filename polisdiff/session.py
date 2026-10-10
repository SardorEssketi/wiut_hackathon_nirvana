"""Document/configuration identity and invalidation, independent of Streamlit."""
import hashlib

RESULT_KEYS = ("report", "document", "input_fingerprint", "evidence_page", "evidence_selection", "evidence_rule", "preview", "manual_page")


def input_identity(data, audit_date, applicable_date, mode):
    return (hashlib.sha256(data).hexdigest(), str(audit_date), str(applicable_date), mode)


def invalidate_result(state, fingerprint):
    if fingerprint is None or state.get("input_fingerprint") != fingerprint:
        for key in list(state):
            if key in RESULT_KEYS or key.startswith(("review_", "manual_page_")):
                state.pop(key, None)


def select_evidence(state, page, passage_id, rule_id=None):
    state["evidence_page"] = page
    state["evidence_selection"] = passage_id
    state["evidence_rule"] = rule_id
    state.pop("preview", None)
