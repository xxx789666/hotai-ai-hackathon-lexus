"""把 Markdown 文件轉成 A4 PDF（中文字型樣式在 pdf_template.html）。

  python pipeline/build_pdf.py 專案架構_2026-09-23.md 專案架構_2026-09-23_v3.pdf
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def main():
    src, dst = ROOT / sys.argv[1], ROOT / sys.argv[2]
    head = (Path(__file__).parent / "pdf_template.html").read_text(encoding="utf-8")
    body = markdown.markdown(src.read_text(encoding="utf-8"), extensions=["tables", "fenced_code"])
    with tempfile.TemporaryDirectory() as d:
        html = Path(d) / "doc.html"
        html.write_text(head + "<body>" + body + "</body></html>", encoding="utf-8")
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={dst}", html.as_uri()], check=True, timeout=120)
    print(f"wrote {dst} ({dst.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
