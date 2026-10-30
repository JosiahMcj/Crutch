#!/usr/bin/env python3
"""paper/paper.tmpl.md + paper/tables.json -> paper/paper.md. Fails on any
unfilled {{T:...}} placeholder."""
import json, re, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1] / "paper"
T = json.loads((P/"tables.json").read_text())
txt = (P/"paper.tmpl.md").read_text()
def sub(m):
    k = m.group(1)
    if k not in T: sys.exit(f"BUILD FAILURE: unknown table {k}")
    return T[k]
out = re.sub(r"\{\{T:([a-z0-9_]+)\}\}", sub, txt)
if "{{" in out: sys.exit("BUILD FAILURE: unfilled placeholder")
(P/"paper.md").write_text(out); print("paper.md", len(out.split()), "words")
