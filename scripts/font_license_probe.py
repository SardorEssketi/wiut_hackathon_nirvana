"""Inspect TrueType embedding flags for the font used in synthetic PDFs."""
from pathlib import Path
import json
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evaluation.generate_fixtures import font_path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    path = font_path()
    content = path.read_bytes()
    tables = struct.unpack_from(">H",content,4)[0]
    flag = None
    for i in range(tables):
        tag,_,offset,_ = struct.unpack_from(">4sIII",content,12+16*i)
        if tag == b"OS/2":
            flag = struct.unpack_from(">H",content,offset+8)[0]
    row = {"font_name":path.name,"fsType":flag,
        "restricted_embedding_bit":bool(flag & 2) if flag is not None else None,
        "no_subsetting_bit":bool(flag & 256) if flag is not None else None,
        "bitmap_only_embedding_bit":bool(flag & 512) if flag is not None else None,
        "font_binary_in_repository":False,
        "license_source":"https://learn.microsoft.com/en-us/typography/fonts/font-faq"}
    (ROOT/"evaluation/font_embedding.json").write_text(json.dumps(row,indent=2),encoding="utf-8")
    print(json.dumps(row))
