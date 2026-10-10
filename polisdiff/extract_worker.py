import sys
from .extraction import _extract, validate_pdf, MAX_BYTES


def main():
    # Linux container adds address-space/CPU limits; Windows uses parent timeout.
    if sys.platform != "win32":
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (768 * 1024**2, 768 * 1024**2))
        resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
    data = sys.stdin.buffer.read(MAX_BYTES + 1)
    try:
        validate_pdf(data)
        if "--render" in sys.argv:
            import pymupdf
            with pymupdf.open(stream=data, filetype="pdf") as pdf:
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
