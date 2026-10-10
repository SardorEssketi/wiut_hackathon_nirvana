"""Sanitize long test identifiers and preserve truthful machine-readable counts."""
import json
import re
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding="utf-8")

def main():
    path = Path(sys.argv[1])
    tree = ET.parse(path)
    suites = list(tree.getroot().iter("testsuite"))
    row = {"tests": sum(int(s.get("tests",0)) for s in suites),
           "failures": sum(int(s.get("failures",0)) for s in suites),
           "errors": sum(int(s.get("errors",0)) for s in suites),
           "skipped": sum(int(s.get("skipped",0)) for s in suites)}
    cases = list(tree.getroot().iter("testcase"))
    row["passed"] = sum(not any(c.tag in {"failure", "error", "skipped"} for c in case) for case in cases)
    row["error_testcases"] = sum(any(c.tag == "error" for c in case) for case in cases)
    row["details"] = []
    for case in tree.getroot().iter("testcase"):
        case.set("name", case.get("name","")[:160])
        for result in case:
            if result.tag in {"failure", "error"}:
                result.set("message", result.get("message","")[:800])
                sanitized = re.sub(r"(?m)^self = environ\(.*$", "self = environ(<redacted test-run environment>)", result.text or "")
                result.text = sanitized[-3500:]
                row["details"].append({"test": case.get("name"), "type": result.tag, "detail": (result.text or "")[-1800:]})
    tree.write(path, encoding="utf-8", xml_declaration=True)
    path.with_suffix(".json").write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(row, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
