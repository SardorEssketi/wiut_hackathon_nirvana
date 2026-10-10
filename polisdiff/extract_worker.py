import sys
from .extraction import _extract, validate_pdf, MAX_BYTES, MAX_PAGES


def main():
    # Linux container adds address-space/CPU limits; Windows uses parent timeout.
    if sys.platform != "win32":
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (768 * 1024**2, 768 * 1024**2))
        resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
    try:
        if "--evidence" in sys.argv:
            import base64
            import hashlib
            import json
            from dataclasses import asdict
            import pymupdf
            from .models import Finding, Evidence
            from .localization import locate_on_page
            request = json.loads(sys.stdin.buffer.read(MAX_BYTES * 2 + 1))
            data = base64.b64decode(request["pdf"], validate=True)
            validate_pdf(data)
            if hashlib.sha256(data).hexdigest() != request["sha256"]:
                raise ValueError("Document mismatch")
            ev = Evidence.model_validate(request["evidence"])
            finding = Finding.model_validate(request["finding"])
            if ev not in finding.evidence:
                raise ValueError("Unknown evidence")
            with pymupdf.open(stream=data, filetype="pdf") as pdf:
                if pdf.needs_pass or not 1 <= len(pdf) <= MAX_PAGES or not 1 <= ev.page <= len(pdf):
                    raise ValueError("Unsupported document")
                page = pdf[ev.page - 1]
                location = locate_on_page(page, finding, ev)
                if location.state == "evidence_mismatch":
                    raise ValueError("Evidence mismatch")
                for box in location.rectangles:
                    page.draw_rect(pymupdf.Rect(box), color=None, fill=(1, .75, .15), fill_opacity=.3, overlay=True)
                scale = min(1.4, 1400/max(page.rect.width, page.rect.height))
                png = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False).tobytes("png")
                sys.stdout.buffer.write(json.dumps({"location": asdict(location),
                    "png": base64.b64encode(png).decode("ascii")}).encode())
            return
        data = sys.stdin.buffer.read(MAX_BYTES + 1)
        validate_pdf(data)
        if "--render" in sys.argv:
            import pymupdf
            with pymupdf.open(stream=data, filetype="pdf") as pdf:
                if pdf.needs_pass or not 1 <= len(pdf) <= MAX_PAGES:
                    raise ValueError("Unsupported document")
                page = pdf[int(sys.argv[-1])-1]
                scale = min(1.4, 1400/max(page.rect.width, page.rect.height))
                sys.stdout.buffer.write(page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False).tobytes("png"))
        else:
            sys.stdout.buffer.write(_extract(data).model_dump_json().encode("utf-8"))
    except Exception:
        # No document content, filenames or parser tracebacks in logs.
        sys.exit(2)

if __name__ == "__main__":
    main()
