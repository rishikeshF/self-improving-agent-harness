#!/usr/bin/env python3
"""Exit 0 if every issue in _docs/issues/ is closed. Prints the open ones otherwise."""
import pathlib
import re
import sys

issues = sorted((pathlib.Path(__file__).resolve().parent.parent / "_docs" / "issues").glob("[0-9]*.md"))
open_ = []
for f in issues:
    m = re.search(r"^Status:\s*(\S+)", f.read_text(), re.M)
    status = m.group(1) if m else "open"
    if status != "closed":
        open_.append(f"{f.name}: {status}")
if open_:
    print("not done:\n  " + "\n  ".join(open_))
    sys.exit(1)
print(f"all {len(issues)} issues closed")
