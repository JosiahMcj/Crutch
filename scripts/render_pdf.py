#!/usr/bin/env python3
"""paper/paper.md -> paper/paper.pdf. Needs pandoc and Google Chrome (headless)."""
import shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; P = ROOT/"paper"
CHROME = next((c for c in ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", shutil.which("google-chrome"), shutil.which("chromium")] if c and Path(c).exists()), None)
if not shutil.which("pandoc") or not CHROME: sys.exit("render_pdf needs pandoc and Chrome")
with tempfile.TemporaryDirectory() as td:
    html = Path(td)/"paper.html"
    subprocess.run(["pandoc", str(P/"paper.md"), "-f", "markdown+pipe_tables+implicit_figures", "-t", "html5", "--standalone", "--embed-resources",
                    f"--resource-path={P}", f"--css={P/'style.css'}", "--metadata", "pagetitle=" + (P/"paper.md").read_text().splitlines()[0].lstrip("# ").strip(), "-o", str(html)], check=True)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={P/'paper.pdf'}", f"file://{html}"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("wrote", P/"paper.pdf")
